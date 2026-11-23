"""LLM Gateway — single interface routing to configured provider."""
from config import settings
from llm.providers.base import BaseLLMProvider
from llm.providers.mock import MockLLMProvider
from security.sanitization import mask_sensitive_data, sanitize_llm_output, hash_content

_provider_instance: BaseLLMProvider | None = None


def get_llm_provider() -> BaseLLMProvider:
    """Factory — returns the configured LLM provider (singleton)."""
    global _provider_instance
    if _provider_instance is None:
        if settings.LLM_PROVIDER == "openai":
            from llm.providers.openai_provider import OpenAIProvider
            _provider_instance = OpenAIProvider()
        elif settings.LLM_PROVIDER == "mock":
            _provider_instance = MockLLMProvider()
        else:
            # Default to Ollama
            from llm.providers.ollama_provider import OllamaProvider
            _provider_instance = OllamaProvider()
    return _provider_instance


def reset_llm_provider():
    """Reset the singleton instance (e.g. for testing or config change)."""
    global _provider_instance
    _provider_instance = None


class LLMGateway:
    """Centralized LLM access with sanitization, masking, and audit hooks."""

    def __init__(self):
        self.provider = get_llm_provider()

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       mask_pii: bool = True) -> dict:
        """Generate with sanitization and audit metadata."""
        # Mask sensitive data before sending to LLM
        safe_prompt = mask_sensitive_data(prompt) if mask_pii else prompt
        safe_system = mask_sensitive_data(system_prompt) if mask_pii else system_prompt

        raw_output = await self.provider.generate(
            safe_prompt, safe_system, temperature, max_tokens
        )

        # Sanitize output
        clean_output = sanitize_llm_output(raw_output)

        return {
            "content": clean_output,
            "model_info": self.provider.get_model_info(),
            "prompt_hash": hash_content(safe_prompt),
        }

    async def generate_structured(self, prompt: str, system_prompt: str = "",
                                   schema: dict | None = None,
                                   max_tokens: int | None = None,
                                   mask_pii: bool = True) -> dict:
        """Generate structured JSON with sanitization."""
        safe_prompt = mask_sensitive_data(prompt) if mask_pii else prompt
        safe_system = mask_sensitive_data(system_prompt) if mask_pii else system_prompt

        try:
            result = await self.provider.generate_structured(
                safe_prompt, safe_system, schema, max_tokens=max_tokens
            )
        except TypeError:
            # Fallback if provider doesn't accept max_tokens
            result = await self.provider.generate_structured(
                safe_prompt, safe_system, schema
            )

        return {
            "data": result,
            "model_info": self.provider.get_model_info(),
            "prompt_hash": hash_content(safe_prompt),
        }
