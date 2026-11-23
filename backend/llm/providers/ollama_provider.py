"""Ollama LLM provider — connects to local Ollama instance (default: Qwen3:4B)."""
import json
import logging
import os
import re
import httpx
from config import settings
from llm.providers.base import BaseLLMProvider

logger = logging.getLogger(__name__)


def extract_json_object(text: str) -> dict | list | None:
    """Robustly extract and parse JSON from LLM output.
    
    Handles:
    - <think>...</think> reasoning blocks from Qwen3/DeepSeek
    - Markdown code fences (```json ... ```)
    - Conversational preambles/postambles
    - Trailing commas in lists/objects
    - Unescaped control characters inside strings
    - Fallback regex object recovery for partial/truncated arrays
    """
    if not text:
        return None

    # 1. Strip reasoning / thinking tokens from Qwen3 / DeepSeek models
    cleaned = re.sub(r"<think>[\s\S]*?(?:</think>|$)", "", text, flags=re.IGNORECASE).strip()
    if not cleaned:
        cleaned = text.strip()

    # 2. Try direct parse
    try:
        return json.loads(cleaned, strict=False)
    except json.JSONDecodeError:
        pass

    # 3. Strip markdown code fences (```json ... ``` or ``` ... ```)
    code_block_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if code_block_match:
        block_content = code_block_match.group(1).strip()
        try:
            return json.loads(block_content, strict=False)
        except json.JSONDecodeError:
            cleaned = block_content

    # 4. Find outermost { ... }
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        candidate = cleaned[first_brace:last_brace + 1]
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            # Try removing trailing commas
            candidate_no_commas = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(candidate_no_commas, strict=False)
            except json.JSONDecodeError:
                pass

    # 5. Find outermost [ ... ]
    first_bracket = cleaned.find("[")
    last_bracket = cleaned.rfind("]")
    if first_bracket != -1 and last_bracket != -1 and last_bracket > first_bracket:
        candidate = cleaned[first_bracket:last_bracket + 1]
        try:
            return json.loads(candidate, strict=False)
        except json.JSONDecodeError:
            candidate_no_commas = re.sub(r",\s*([\]}])", r"\1", candidate)
            try:
                return json.loads(candidate_no_commas, strict=False)
            except json.JSONDecodeError:
                pass

    # 6. Fallback: Regex extraction of individual requirement objects
    # If the response was an array or dict containing requirement objects but outer JSON was malformed
    object_matches = re.findall(r"(\{[^{}]*\"(?:requirement_id|statement)\"[^{}]*\})", cleaned)
    if object_matches:
        recovered = []
        for obj_str in object_matches:
            try:
                obj_clean = re.sub(r",\s*([\]}])", r"\1", obj_str)
                recovered.append(json.loads(obj_clean, strict=False))
            except Exception:
                continue
        if recovered:
            return {"requirements": recovered, "extraction_notes": "Recovered via regex parsing"}

    return None


class OllamaProvider(BaseLLMProvider):
    """Local LLM provider using Ollama REST API with flexible timeout and non-thinking mode."""

    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = settings.OLLAMA_MODEL
        self.context_window = settings.OLLAMA_CONTEXT_WINDOW
        self.timeout = float(getattr(settings, "OLLAMA_TIMEOUT", 300))
        self.max_tokens = int(getattr(settings, "LLM_MAX_TOKENS", 4096))
        self.num_threads = int(getattr(settings, "OLLAMA_NUM_THREADS", None) or os.cpu_count() or 4)
        self.call_count = 0

    async def _make_request(self, endpoint: str, payload: dict) -> dict:
        """Helper to send request to Ollama with meaningful error reporting and progress logging."""
        url = f"{self.base_url}{endpoint}"
        client_timeout = httpx.Timeout(timeout=self.timeout, connect=15.0, read=self.timeout, write=30.0)
        try:
            async with httpx.AsyncClient(timeout=client_timeout) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 404:
                    raise RuntimeError(
                        f"Ollama model '{self.model}' not found on {self.base_url}. "
                        f"Run 'ollama pull {self.model}' to download the model."
                    )
                response.raise_for_status()
                return response.json()
        except httpx.ConnectError:
            raise RuntimeError(
                f"Cannot connect to Ollama at {self.base_url}. "
                f"Please ensure Ollama is running (`ollama serve`). "
                f"Or set LLM_PROVIDER=mock in .env for offline testing."
            )
        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ollama request timed out after {int(self.timeout)}s for model '{self.model}'. "
                f"Check server load or increase OLLAMA_TIMEOUT in .env."
            )
        except Exception as e:
            if isinstance(e, RuntimeError):
                raise
            raise RuntimeError(f"Ollama communication error: {str(e)}")

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       response_format: dict | None = None) -> str:
        self.call_count += 1

        messages = []
        full_system = system_prompt or ""
        if full_system:
            messages.append({"role": "system", "content": full_system})
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
                "num_thread": self.num_threads,
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
        full_system = system_prompt or "You are an expert financial requirements engineering assistant."
        full_system += "\nYou MUST return valid, well-formed JSON only, without any explanatory text, commentary, or <think> tags."

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
                "num_predict": self.max_tokens,  # Use full token limit
                "num_ctx": self.context_window,
                "num_thread": self.num_threads,
            },
        }

        data = await self._make_request("/api/chat", payload)
        raw_content = data.get("message", {}).get("content", "")

        parsed = extract_json_object(raw_content)
        if parsed is not None:
            if isinstance(parsed, dict):
                return parsed
            elif isinstance(parsed, list):
                return {"requirements": parsed, "items": parsed}

        logger.warning(f"Failed to parse JSON from Ollama output: {raw_content[:300]}")
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
            "timeout": self.timeout,
            "threads": self.num_threads,
            "calls": self.call_count,
        }
