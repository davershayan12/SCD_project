"""Tests for SSRF-protected safe fetcher."""

import ipaddress
import pytest

from app.services.fetcher.safe_fetcher import SafeFetcher, FetchError


class TestIPValidation:
    """SSRF blocking rules."""

    def test_block_loopback_127(self):
        fetcher = SafeFetcher()
        with pytest.raises(FetchError, match="Blocked private or internal IP"):
            fetcher.validate_url("http://127.0.0.1/admin")

    def test_block_cloud_metadata_ip(self):
        fetcher = SafeFetcher()
        with pytest.raises(FetchError, match="Blocked private or internal IP"):
            fetcher.validate_url("http://169.254.169.254/latest/meta-data")

    def test_block_rfc1918_private(self):
        fetcher = SafeFetcher()
        for url in ("http://10.0.0.1/", "http://192.168.1.1/", "http://172.16.0.5/"):
            with pytest.raises(FetchError, match="Blocked private or internal IP"):
                fetcher.validate_url(url)

    def test_block_ipv6_loopback(self):
        fetcher = SafeFetcher()
        with pytest.raises(FetchError, match="Blocked private or internal IP"):
            fetcher.validate_url("http://[::1]/")

    def test_reject_non_http_scheme(self):
        fetcher = SafeFetcher()
        for url in ("file:///etc/passwd", "ftp://example.com/a", "gopher://x/"):
            with pytest.raises(FetchError, match="Only http and https"):
                fetcher.validate_url(url)

    def test_reject_credentials_in_url(self):
        fetcher = SafeFetcher()
        with pytest.raises(FetchError, match="credentials"):
            fetcher.validate_url("http://user:pass@example.com/")

    def test_allow_public_ip(self):
        fetcher = SafeFetcher()
        # Should not raise
        fetcher.validate_url("http://93.184.216.34/")

    def test_is_public_ip_helper(self):
        fetcher = SafeFetcher()
        assert fetcher.is_blocked_ip(ipaddress.ip_address("127.0.0.1")) is True
        assert fetcher.is_blocked_ip(ipaddress.ip_address("169.254.169.254")) is True
        assert fetcher.is_blocked_ip(ipaddress.ip_address("8.8.8.8")) is False


class TestRobots:
    """robots.txt compliance."""

    def test_robots_disallow_blocks_fetch(self):
        fetcher = SafeFetcher()
        robots = "User-agent: *\nDisallow: /private/\n"
        assert fetcher.is_allowed_by_robots("/private/page", robots) is False
        assert fetcher.is_allowed_by_robots("/public/page", robots) is True

    def test_robots_allow_all_when_absent(self):
        fetcher = SafeFetcher()
        assert fetcher.is_allowed_by_robots("/anything", "") is True

    def test_robots_user_agent_specific(self):
        fetcher = SafeFetcher(respect_robots=True, user_agent="ResearchRadarBot")
        robots = "User-agent: ResearchRadarBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
        assert fetcher.is_allowed_by_robots("/paper", robots) is False


class TestContentLimits:
    """Size-cap and content-type enforcement."""

    def test_hard_size_cap_constant(self):
        fetcher = SafeFetcher(max_bytes=1024)
        assert fetcher.max_bytes == 1024

    def test_content_type_allowlist(self):
        fetcher = SafeFetcher()
        assert fetcher.is_allowed_content_type("text/html; charset=utf-8") is True
        assert fetcher.is_allowed_content_type("text/plain") is True
        assert fetcher.is_allowed_content_type("application/pdf") is True
        assert fetcher.is_allowed_content_type("image/png") is False

    def test_honest_user_agent(self):
        fetcher = SafeFetcher()
        assert "ResearchRadar" in fetcher.user_agent
        assert not any(
            token in fetcher.user_agent.lower()
            for token in ("mozilla", "chrome", "safari", "webkit")
        )
