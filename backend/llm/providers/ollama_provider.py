"""Ollama LLM provider — connects to local Ollama instance (default: Qwen3:8B)."""
import json
import logging
import re
import httpx
from config import settings
from llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


def extract_json_object(text: str) -> dict | list | None:
    """Robustly extract and parse JSON from LLM output, handling markdown blocks and stray text."""
    if not text:
        return None

    cleaned = text.strip()

    # 1. Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown code fences (```json ... ``` or ``` ... ```)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if code_block_match:
        try:
            return json.loads(code_block_match.group(1).strip())
        except json.JSONDecodeError:
            cleaned = code_block_match.group(1).strip()

    # 3. Find outermost { ... } or [ ... ]
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Try removing trailing commas
            candidate_no_commas = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(candidate_no_commas)
            except json.JSONDecodeError:
                pass

    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = cleaned[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            candidate_no_commas = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(candidate_no_commas)
            except json.JSONDecodeError:
                pass

    return None


class OllamaProvider(BaseLLMProvider):
    """Local LLM provider using Ollama REST API."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.context_window = settings.OLLAMA_CONTEXT_WINDOW
        self.timeout = settings.OLLAMA_TIMEOUT
        self.call_count = 0

    async def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Helper to send request to Ollama with meaningful error reporting."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 404:
                    raise RuntimeError(
                        f"Ollama model '{self.model}' not found. "
                        f"Run 'ollama pull {self.model}' to download the model."
                    )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Please ensure Ollama is installed and running (`ollama serve`). "
                f"Or set LLM_PROVIDER=mock in .env for offline testing."
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ollama request timed out after {self.timeout}s for model '{self.model}'."
            )
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Ollama request error: {str(e)}")

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       response_format: dict | None = None) -> str:
        self.call_count += 1

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.context_window,
            },
        }

        if response_format and response_format.get("type") == "json_object":
            payload["format"] = "json"

        data = await self._make_request("/api/chat", payload)
        message = data.get("message", {})
        return message.get("content", "")

    async def generate_structured(self, prompt: str, system_prompt: str = "",
                                   schema: dict | None = None,
                                   temperature: float = 0.1) -> dict:
        self.call_count += 1

        messages = []
        full_system = system_prompt or "You are a requirements engineering assistant."
        full_system += "\nYou MUST return valid, well-formed JSON only, without any explanatory text or markdown code fences outside the JSON."

        messages.append({"role": "system", "content": full_system})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": False,
            "format": "json",
            "options": {
                "temperature": temperature,
                "num_predict": 1024,
                "num_ctx": self.context_window,
            },
        }

        data = await self._make_request("/api/chat", payload)
        raw_content = data.get("message", {}).get("content", "")

        parsed = extract_json_object(raw_content)
        if parsed is not None:
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list):
                return {"items": parsed}

        logger.warning(f"Failed to parse JSON from Ollama output: {raw_content[:200]}")
        return {
            "error": "Failed to parse structured response from model",
            "raw_output": raw_content,
        }

    def get_model_info(self) -> dict:
        return {
            "provider": "ollama",
            "model": self.model,
            "base_url": self.base_url,
            "context_window": self.context_window,
            "calls": self.call_count,
        }
