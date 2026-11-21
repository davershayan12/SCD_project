"""Ollama LLM integration service with structured JSON output."""

import json
import logging
from typing import Any, Dict, Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OllamaService:
    """Service for interacting with local Ollama LLM runtime."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
        num_ctx: Optional[int] = None,
    ):
        """Initialize Ollama service.

        Args:
            base_url: Ollama API URL. Defaults to settings.
            model_name: Model name. Defaults to settings.
            num_ctx: Context window size. Defaults to settings.
        """
        self.base_url = base_url or settings.ollama_url
        self.model_name = model_name or settings.ollama_model
        self.num_ctx = num_ctx or settings.ollama_num_ctx

    def generate_json(
        self,
        prompt: str,
        json_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate structured JSON output from Ollama using schema format.

        Args:
            prompt: User prompt
            json_schema: Pydantic model JSON schema for structured output
            system_prompt: Optional system prompt
            temperature: Sampling temperature (low for extraction)

        Returns:
            Parsed JSON dictionary

        Raises:
            RuntimeError: If Ollama is down, model missing, or request fails
        """
        url = f"{self.base_url}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model_name,
            "messages": messages,
            "options": {
                "num_ctx": self.num_ctx,
                "temperature": temperature,
            },
            "format": json_schema,  # Enforce JSON schema structure in Ollama
            "stream": False,
        }

        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(url, json=payload)

                if response.status_code == 404:
                    raise RuntimeError(
                        f"Ollama model '{self.model_name}' not found. "
                        f"Please run 'ollama pull {self.model_name}'."
                    )
                elif response.status_code != 200:
                    raise RuntimeError(
                        f"Ollama API returned error {response.status_code}: {response.text}"
                    )

                data = response.json()
                content = data.get("message", {}).get("content", "{}")

                # Parse JSON response
                try:
                    return json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Ollama JSON response: {content}")
                    raise RuntimeError(f"Ollama returned malformed JSON: {str(e)}")

        except httpx.ConnectError:
            raise RuntimeError(
                f"Could not connect to Ollama at '{self.base_url}'. "
                "Please ensure Ollama is running."
            )
        except httpx.TimeoutException:
            raise RuntimeError("Ollama request timed out. Document excerpt may be too long.")
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Ollama generation failed: {str(e)}")

    def check_health(self) -> bool:
        """Check if Ollama service is reachable and model is available."""
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
