"""Structured Response Service — Responses API com JSON Schema.

Garante outputs estruturados usando Pydantic schemas.
Elimina necessidade de regex para parsing.
"""

from __future__ import annotations

import json
from typing import TypeVar, Type

from pydantic import BaseModel

from app.openai.client import OpenAIClient, get_openai_client


T = TypeVar("T", bound=BaseModel)


class StructuredResponseService:
    """Serviço para obter respostas estruturadas da OpenAI.

    Usa response_format com json_schema para garantir output válido.
    """

    def __init__(self, client: OpenAIClient | None = None):
        self.client = client or get_openai_client()

    async def generate(
        self,
        schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        context_messages: list[dict] | None = None,
    ) -> T:
        """Gera resposta estruturada seguindo um schema Pydantic.

        Args:
            schema: Classe Pydantic que define a estrutura esperada
            system_prompt: Prompt de sistema
            user_prompt: Prompt do usuário
            model: Modelo a usar (ou default)
            temperature: Temperatura para geração
            context_messages: Mensagens adicionais de contexto

        Returns:
            Instância do schema preenchida

        Example:
            >>> result = await service.generate(
            ...     schema=ProductProfile,
            ...     system_prompt="Analise o produto...",
            ...     user_prompt="Produto: Mochila de viagem...",
            ... )
            >>> print(result.problems)
        """
        # Construir mensagens
        messages = [{"role": "system", "content": system_prompt}]

        if context_messages:
            messages.extend(context_messages)

        messages.append({"role": "user", "content": user_prompt})

        # Gerar JSON Schema do Pydantic
        json_schema = schema.model_json_schema()

        # Chamar API com response_format
        response = await self.client.chat_completion(
            messages=messages,
            model=model,
            temperature=temperature,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": json_schema,
                    "strict": True,
                }
            },
        )

        # Parse e validar com Pydantic
        content = response["content"]
        data = json.loads(content)
        return schema.model_validate(data)

    async def generate_list(
        self,
        item_schema: Type[T],
        system_prompt: str,
        user_prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        min_items: int = 1,
        max_items: int = 10,
    ) -> list[T]:
        """Gera lista de items estruturados.

        Cria um schema wrapper para lista e retorna os items.
        """
        # Criar schema wrapper para lista
        class ListWrapper(BaseModel):
            items: list[item_schema]  # type: ignore

        # Ajustar prompt para indicar que queremos lista
        adjusted_system = (
            f"{system_prompt}\n\n"
            f"Retorne entre {min_items} e {max_items} items no campo 'items'."
        )

        wrapper = await self.generate(
            schema=ListWrapper,
            system_prompt=adjusted_system,
            user_prompt=user_prompt,
            model=model,
            temperature=temperature,
        )

        return wrapper.items

    async def analyze_with_schema(
        self,
        schema: Type[T],
        content: str,
        analysis_instructions: str,
        model: str | None = None,
    ) -> T:
        """Analisa conteúdo e retorna resultado estruturado.

        Wrapper conveniente para análises.
        """
        system_prompt = (
            f"{analysis_instructions}\n\n"
            "Analise o conteúdo fornecido e retorne sua análise "
            "no formato JSON especificado."
        )

        return await self.generate(
            schema=schema,
            system_prompt=system_prompt,
            user_prompt=content,
            model=model,
            temperature=0.3,  # Menor temperatura para análise
        )


# Singleton
_service: StructuredResponseService | None = None


def get_structured_service() -> StructuredResponseService:
    """Retorna instância singleton do serviço."""
    global _service
    if _service is None:
        _service = StructuredResponseService()
    return _service
