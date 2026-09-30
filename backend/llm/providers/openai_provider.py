"""OpenAI LLM provider — production-ready, requires OPENAI_API_KEY."""
import json
from llm.providers.base import BaseLLMProvider
from config import settings


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider. Set LLM_PROVIDER=openai and OPENAI_API_KEY in env."""

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise ValueError(
                "OPENAI_API_KEY is required. Set it in .env or environment variables."
            )
        # Lazy import to avoid dependency when using mock
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    async def generate(self, prompt: str, system_prompt: str = "",
                       temperature: float = 0.2, max_tokens: int = 4096,
                       response_format: dict | None = None) -> str:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""

    async def generate_structured(self, prompt: str, system_prompt: str = "",
                                   schema: dict | None = None,
                                   temperature: float = 0.1) -> dict:
        system = system_prompt or "You are a financial requirements engineering assistant. Respond with valid JSON only."
        if schema:
            system += f"\n\nRespond with JSON matching this schema:\n{json.dumps(schema, indent=2)}"

        text = await self.generate(
            prompt, system, temperature,
            response_format={"type": "json_object"}
        )
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"response": text, "structured": False}

    def get_model_info(self) -> dict:
        return {
            "provider": "openai",
            "model": self.model,
            "version": "api",
        }
