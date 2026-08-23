"""OpenAI Client — Cliente base com configuração centralizada.

Gerencia conexão, retry, timeout e tracking de custos.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import Any

from openai import AsyncOpenAI, OpenAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class OpenAIModelConfig(BaseSettings):
    """Configuração centralizada de modelos OpenAI.

    Todos os modelos definidos aqui para facilitar troca sem alterar código.
    """
    # API
    api_key: str = ""

    # Modelos de texto/raciocínio
    creative_model: str = "gpt-4o"           # Análise criativa, planejamento
    premium_model: str = "gpt-4o"            # Tarefas complexas
    fast_model: str = "gpt-4o-mini"          # Tarefas simples, alto volume

    # Imagem
    image_model: str = "gpt-image-1"         # Geração/edição de imagem (dall-e-3 ou gpt-image quando disponível)

    # Vídeo (quando disponível)
    video_model: str = "sora"                # Geração de vídeo padrão
    video_premium_model: str = "sora"        # Cenas premium

    # Áudio
    transcription_model: str = "whisper-1"   # Transcrição (ou gpt-4o-transcribe quando disponível)
    tts_model: str = "tts-1"                 # Text-to-speech
    tts_voice: str = "nova"                  # Voz padrão

    # Timeouts
    timeout_seconds: int = 120
    max_retries: int = 3

    class Config:
        env_prefix = "OPENAI_"
        env_file = ".env"


class UsageTracker:
    """Tracker simples de uso para estimativa de custos."""

    # Preços aproximados (USD por 1K tokens/unidade)
    PRICES = {
        # Texto
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
        "gpt-4.1-mini": {"input": 0.0004, "output": 0.0016},
        # Imagem
        "dall-e-3": {"1024x1024": 0.04, "1024x1792": 0.08},
        "gpt-image-1": {"per_image": 0.02},
        # Áudio
        "whisper-1": {"per_minute": 0.006},
        "tts-1": {"per_1k_chars": 0.015},
        "tts-1-hd": {"per_1k_chars": 0.030},
        # Vídeo (estimativa)
        "sora": {"per_second": 0.05},
    }

    def __init__(self):
        self.records: list[dict] = []

    def record(
        self,
        model: str,
        operation: str,
        tokens_input: int = 0,
        tokens_output: int = 0,
        images: int = 0,
        audio_seconds: float = 0,
        audio_chars: int = 0,
        video_seconds: float = 0,
        product_id: str | None = None,
        creative_id: str | None = None,
    ) -> float:
        """Registra uso e retorna custo estimado."""
        cost = 0.0

        # Texto
        if tokens_input or tokens_output:
            prices = self.PRICES.get(model, {"input": 0.01, "output": 0.03})
            cost += (tokens_input / 1000) * prices.get("input", 0.01)
            cost += (tokens_output / 1000) * prices.get("output", 0.03)

        # Imagem
        if images:
            img_price = self.PRICES.get(model, {}).get("per_image", 0.04)
            cost += images * img_price

        # Áudio transcrição
        if audio_seconds:
            cost += (audio_seconds / 60) * self.PRICES.get(model, {}).get("per_minute", 0.006)

        # TTS
        if audio_chars:
            cost += (audio_chars / 1000) * self.PRICES.get(model, {}).get("per_1k_chars", 0.015)

        # Vídeo
        if video_seconds:
            cost += video_seconds * self.PRICES.get(model, {}).get("per_second", 0.05)

        self.records.append({
            "model": model,
            "operation": operation,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "images": images,
            "audio_seconds": audio_seconds,
            "audio_chars": audio_chars,
            "video_seconds": video_seconds,
            "cost": cost,
            "product_id": product_id,
            "creative_id": creative_id,
        })

        return cost

    def total_cost(self) -> float:
        return sum(r["cost"] for r in self.records)

    def clear(self):
        self.records = []


class OpenAIClient:
    """Cliente OpenAI com configuração centralizada e tracking."""

    def __init__(self, config: OpenAIModelConfig | None = None):
        self.config = config or OpenAIModelConfig()
        self.tracker = UsageTracker()

        # Clientes
        self._sync_client: OpenAI | None = None
        self._async_client: AsyncOpenAI | None = None

    @property
    def sync_client(self) -> OpenAI:
        if self._sync_client is None:
            self._sync_client = OpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout_seconds,
                max_retries=self.config.max_retries,
            )
        return self._sync_client

    @property
    def async_client(self) -> AsyncOpenAI:
        if self._async_client is None:
            self._async_client = AsyncOpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout_seconds,
                max_retries=self.config.max_retries,
            )
        return self._async_client

    def get_model(self, tier: str = "creative") -> str:
        """Retorna modelo apropriado para o tier.

        Args:
            tier: "creative" | "premium" | "fast"
        """
        if tier == "premium":
            return self.config.premium_model
        elif tier == "fast":
            return self.config.fast_model
        return self.config.creative_model

    async def chat_completion(
        self,
        messages: list[dict],
        model: str | None = None,
        temperature: float = 0.7,
        response_format: dict | None = None,
        **kwargs,
    ) -> dict:
        """Faz chamada de chat completion."""
        model = model or self.config.creative_model

        response = await self.async_client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            response_format=response_format,
            **kwargs,
        )

        # Track usage
        usage = response.usage
        if usage:
            self.tracker.record(
                model=model,
                operation="chat_completion",
                tokens_input=usage.prompt_tokens,
                tokens_output=usage.completion_tokens,
            )

        return {
            "content": response.choices[0].message.content,
            "usage": {
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
            },
            "model": model,
        }


# Singleton
_client: OpenAIClient | None = None


def get_openai_client() -> OpenAIClient:
    """Retorna instância singleton do cliente."""
    global _client
    if _client is None:
        _client = OpenAIClient()
    return _client


def reset_client():
    """Reset para testes."""
    global _client
    _client = None
