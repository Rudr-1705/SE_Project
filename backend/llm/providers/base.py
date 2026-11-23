"""Base LLM provider interface."""
from abc import ABC, abstractmethod


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers (mock, OpenAI, etc.)."""

    @abstractmethod
    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       response_format: dict | None = None) -> str:
        """Generate a text response from the LLM."""
        ...

    @abstractmethod
    async def generate_structured(self, prompt: str, system_prompt: str = "",
                                   schema: dict | None = None,
                                   temperature: float = 0.1,
                                   max_tokens: int | None = None) -> dict:
        """Generate a structured (JSON) response from the LLM."""
        ...

    @abstractmethod
    def get_model_info(self) -> dict:
        """Return model name and version for audit tracking."""
        ...
