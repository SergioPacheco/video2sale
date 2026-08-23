"""Vision Analysis Service — Análise de imagens com GPT-4o.

Processa imagens (URLs ou base64) e retorna análises estruturadas.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import TypeVar, Type

from pydantic import BaseModel

from app.openai.client import OpenAIClient, get_openai_client


T = TypeVar("T", bound=BaseModel)


def encode_image_to_base64(image_path: str) -> str:
    """Converte imagem local para base64."""
    with open(image_path, "rb") as f:
        return base64.standard_b64encode(f.read()).decode("utf-8")


def get_image_media_type(path: str) -> str:
    """Detecta media type da imagem."""
    ext = Path(path).suffix.lower()
    return {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }.get(ext, "image/jpeg")


class VisionAnalysisService:
    """Serviço para análise de imagens com Vision API."""

    def __init__(self, client: OpenAIClient | None = None):
        self.client = client or get_openai_client()

    def _build_image_content(
        self,
        images: list[str],
        detail: str = "high",
    ) -> list[dict]:
        """Constrói lista de content com imagens.

        Args:
            images: Lista de URLs ou paths locais
            detail: "low", "high", ou "auto"
        """
        content = []

        for img in images:
            if img.startswith(("http://", "https://")):
                # URL
                content.append({
                    "type": "image_url",
                    "image_url": {"url": img, "detail": detail},
                })
            else:
                # Path local - converter para base64
                media_type = get_image_media_type(img)
                b64 = encode_image_to_base64(img)
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{b64}",
                        "detail": detail,
                    },
                })

        return content

    async def analyze(
        self,
        images: list[str],
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        detail: str = "high",
    ) -> str:
        """Analisa imagens e retorna texto livre.

        Args:
            images: Lista de URLs ou paths locais
            prompt: Pergunta/instrução sobre as imagens
            system_prompt: Prompt de sistema opcional
            model: Modelo (default: gpt-4o)
            detail: Nível de detalhe da análise
        """
        model = model or self.client.config.creative_model

        # Construir mensagens
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Mensagem do usuário com imagens + texto
        user_content = self._build_image_content(images, detail)
        user_content.append({"type": "text", "text": prompt})

        messages.append({"role": "user", "content": user_content})

        response = await self.client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.3,
        )

        return response["content"]

    async def analyze_structured(
        self,
        schema: Type[T],
        images: list[str],
        prompt: str,
        system_prompt: str | None = None,
        model: str | None = None,
        detail: str = "high",
    ) -> T:
        """Analisa imagens e retorna resultado estruturado.

        Args:
            schema: Classe Pydantic para estrutura de resposta
            images: Lista de URLs ou paths locais
            prompt: Instrução sobre as imagens
            system_prompt: Prompt de sistema
            model: Modelo (default: gpt-4o)
            detail: Nível de detalhe
        """
        model = model or self.client.config.creative_model

        # Construir mensagens
        messages = []

        base_system = (
            "Analise as imagens fornecidas e retorne sua análise "
            "no formato JSON especificado. Seja preciso e objetivo."
        )

        if system_prompt:
            base_system = f"{system_prompt}\n\n{base_system}"

        messages.append({"role": "system", "content": base_system})

        # Mensagem do usuário com imagens + texto
        user_content = self._build_image_content(images, detail)
        user_content.append({"type": "text", "text": prompt})

        messages.append({"role": "user", "content": user_content})

        # Gerar JSON Schema
        json_schema = schema.model_json_schema()

        response = await self.client.chat_completion(
            messages=messages,
            model=model,
            temperature=0.3,
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": schema.__name__,
                    "schema": json_schema,
                    "strict": True,
                }
            },
        )

        # Parse e validar
        data = json.loads(response["content"])
        return schema.model_validate(data)

    async def compare_images(
        self,
        original: str,
        generated: str,
        comparison_prompt: str,
        model: str | None = None,
    ) -> dict:
        """Compara duas imagens (útil para fidelidade de produto).

        Args:
            original: Path/URL da imagem original
            generated: Path/URL da imagem gerada
            comparison_prompt: Instrução de comparação
            model: Modelo a usar
        """
        system_prompt = (
            "Você é um especialista em controle de qualidade visual. "
            "Compare as duas imagens fornecidas seguindo as instruções. "
            "A primeira imagem é o ORIGINAL, a segunda é a GERADA."
        )

        full_prompt = (
            f"{comparison_prompt}\n\n"
            "Retorne um JSON com:\n"
            '- "match_score": 0-100 indicando similaridade\n'
            '- "differences": lista de diferenças encontradas\n'
            '- "preserved": lista de elementos preservados\n'
            '- "approved": true/false se a gerada é aceitável'
        )

        result = await self.analyze(
            images=[original, generated],
            prompt=full_prompt,
            system_prompt=system_prompt,
            model=model,
        )

        # Tentar parsear como JSON
        try:
            return json.loads(result)
        except json.JSONDecodeError:
            return {
                "raw_response": result,
                "match_score": 0,
                "differences": ["Não foi possível parsear resposta"],
                "preserved": [],
                "approved": False,
            }

    async def extract_frames_analysis(
        self,
        frame_paths: list[str],
        context: str,
        model: str | None = None,
    ) -> str:
        """Analisa sequência de frames de vídeo.

        Args:
            frame_paths: Paths dos frames em ordem
            context: Contexto sobre o vídeo
            model: Modelo a usar
        """
        system_prompt = (
            "Você é um especialista em análise de vídeos virais de TikTok. "
            "Analise os frames fornecidos que representam momentos-chave de um vídeo. "
            "Identifique técnicas, estrutura narrativa e motivos de sucesso."
        )

        prompt = (
            f"Contexto: {context}\n\n"
            "Estes frames representam momentos-chave de um vídeo de sucesso. "
            "Analise:\n"
            "1. Estrutura narrativa (hook, desenvolvimento, CTA)\n"
            "2. Técnicas visuais usadas\n"
            "3. Pacing e ritmo\n"
            "4. Como o produto é apresentado\n"
            "5. Por que este vídeo provavelmente funciona\n"
            "6. Padrões que podem ser replicados (sem copiar conteúdo)"
        )

        return await self.analyze(
            images=frame_paths,
            prompt=prompt,
            system_prompt=system_prompt,
            model=model,
            detail="high",
        )


# Singleton
_service: VisionAnalysisService | None = None


def get_vision_service() -> VisionAnalysisService:
    """Retorna instância singleton do serviço."""
    global _service
    if _service is None:
        _service = VisionAnalysisService()
    return _service
