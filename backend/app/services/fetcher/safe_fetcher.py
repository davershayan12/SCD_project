"""SSRF-protected, robots.txt-compliant HTTP fetcher for third-party pages.

Design notes:
- Only http/https, no credentials in URL, no spoofed User-Agent.
- DNS resolved before connecting; every resolved address (and the address
  after redirects) must be public. Private / loopback / link-local /
  reserved / metadata ranges are blocked.
- Streamed download with a hard byte cap; content-type allowlist.
- Timeouts and a small redirect limit.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
import urllib.parse
import urllib.robotparser
from dataclasses import dataclass
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_CONTENT_TYPES = {"text/html", "text/plain", "application/pdf"}
MAX_REDIRECTS = 3


class FetchError(Exception):
    """Raised when a URL cannot be safely fetched."""


@dataclass
class FetchResult:
    """Result of a successful fetch."""

    url: str
    final_url: str
    status_code: int
    content_type: str
    content: bytes

    @property
    def text(self) -> str:
        """Decoded text for HTML/plain responses."""
        if self.content_type.startswith("application/pdf"):
            return ""
        return self.content.decode("utf-8", errors="replace")


class SafeFetcher:
    """Hardened fetcher with SSRF, robots and size protections."""

    def __init__(
        self,
        max_bytes: int = 5 * 1024 * 1024,
        timeout: float = 10.0,
        respect_robots: bool = True,
        user_agent: str = "ResearchRadarBot/1.0 (+https://github.com/davershayan12/SCD_project)",
    ):
        self.max_bytes = max_bytes
        self.timeout = timeout
        self.respect_robots = respect_robots
        self.user_agent = user_agent

    # ------------------------------------------------------------------ IPs
    def is_blocked_ip(self, ip: ipaddress._BaseAddress) -> bool:
        """Return True if the address is private, internal or non-routable."""
        return bool(
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_reserved
            or ip.is_multicast
            or ip.is_unspecified
        )

    def _resolve_and_check(self, hostname: str) -> None:
        """Resolve a hostname and reject if any address is blocked.

        Resolving DNS ourselves (rather than letting httpx do it) is what
        prevents a hostname from pointing at an internal address.
        """
        try:
            infos = socket.getaddrinfo(hostname, None)
        except socket.gaierror as e:
            raise FetchError(f"Could not resolve host '{hostname}': {e}")

        for info in infos:
            addr = info[4][0]
            try:
                ip = ipaddress.ip_address(addr)
            except ValueError:
                continue
            if self.is_blocked_ip(ip):
                raise FetchError(f"Blocked private or internal IP for host '{hostname}': {addr}")

    # ------------------------------------------------------------------ URL
    def validate_url(self, url: str) -> urllib.parse.ParseResult:
        """Validate scheme, credentials, and target IP of a URL."""
        parsed = urllib.parse.urlparse(url)

        if parsed.scheme.lower() not in ALLOWED_SCHEMES:
            raise FetchError(f"Only http and https URLs are allowed (got '{parsed.scheme}')")

        if parsed.username or parsed.password:
            raise FetchError("URLs with credentials are not allowed")

        hostname = parsed.hostname
        if not hostname:
            raise FetchError("URL has no hostname")

        # Literal IP in the URL: check directly.
        try:
            literal_ip = ipaddress.ip_address(hostname)
            if self.is_blocked_ip(literal_ip):
                raise FetchError(f"Blocked private or internal IP: {hostname}")
        except ValueError:
            # Not a literal IP -> resolve DNS and check every address.
            self._resolve_and_check(hostname)

        return parsed

    # --------------------------------------------------------------- robots
    def is_allowed_by_robots(self, path: str, robots_txt: str) -> bool:
        """Evaluate a path against a robots.txt document."""
        if not robots_txt.strip():
            return True
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(robots_txt.splitlines())
        # RobotFileParser matches on user agent token (first word).
        agent = self.user_agent.split("/")[0]
        return parser.can_fetch(agent, path)

    def _fetch_robots(self, parsed: urllib.parse.ParseResult, client: httpx.Client) -> str:
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        try:
            resp = client.get(robots_url)
            if resp.status_code == 200:
                return resp.text[:100_000]
        except Exception as e:  # robots fetch is best-effort
            logger.info("robots.txt unavailable: %s", e)
        return ""

    # ---------------------------------------------------------- content type
    def is_allowed_content_type(self, content_type: str) -> bool:
        base = (content_type or "").split(";")[0].strip().lower()
        return base in ALLOWED_CONTENT_TYPES

    # ---------------------------------------------------------------- fetch
    def fetch_url(self, url: str) -> FetchResult:
        """Fetch a URL safely, following limited, validated redirects."""
        parsed = self.validate_url(url)

        with httpx.Client(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=False,
        ) as client:
            if self.respect_robots:
                robots = self._fetch_robots(parsed, client)
                if not self.is_allowed_by_robots(parsed.path or "/", robots):
                    raise FetchError(f"Blocked by robots.txt: {url}")

            current_url = url
            for _ in range(MAX_REDIRECTS + 1):
                current_parsed = self.validate_url(current_url)
                with client.stream("GET", current_url) as resp:
                    if resp.is_redirect:
                        location = resp.headers.get("location")
                        if not location:
                            raise FetchError("Redirect without Location header")
                        current_url = urllib.parse.urljoin(current_url, location)
                        continue

                    if resp.status_code != 200:
                        raise FetchError(f"HTTP {resp.status_code} for {current_url}")

                    content_type = resp.headers.get("content-type", "")
                    if not self.is_allowed_content_type(content_type):
                        raise FetchError(f"Blocked content-type '{content_type}'")

                    chunks: list[bytes] = []
                    total = 0
                    for chunk in resp.iter_bytes():
                        total += len(chunk)
                        if total > self.max_bytes:
                            raise FetchError(
                                f"Response exceeds size cap of {self.max_bytes} bytes"
                            )
                        chunks.append(chunk)

                    return FetchResult(
                        url=url,
                        final_url=current_url,
                        status_code=resp.status_code,
                        content_type=content_type,
                        content=b"".join(chunks),
                    )

            raise FetchError("Too many redirects")
