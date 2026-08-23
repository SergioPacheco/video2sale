"""Image Service — Geração e edição de imagens com DALL-E/gpt-image.

Usado para cleanup de fotos de produto, criação de cenas e assets.
"""

from __future__ import annotations

import base64
import hashlib
import shutil
from pathlib import Path
from typing import Literal

import httpx

from app.openai.client import OpenAIClient, get_openai_client


# Cache de imagens
IMAGE_CACHE_DIR = Path("/data/cache/images")


class ImageService:
    """Serviço para geração e edição de imagens."""

    # Instrução base para preservar fidelidade do produto
    PRODUCT_IDENTITY_LOCK = """
PRODUCT_IDENTITY_LOCK:

The input product is immutable. Preserve exactly the physical identity of the product.

Do not redesign, reinterpret or beautify product construction.

Do not add or remove:
- pockets
- zippers
- straps
- logos
- seams
- accessories
- pieces

Do not change:
- color
- shape
- proportions
- model
- material appearance

You may alter only:
- background
- lighting
- framing
- photographic quality
- environment
"""

    def __init__(self, client: OpenAIClient | None = None):
        self.client = client or get_openai_client()
        IMAGE_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, prompt: str, size: str) -> str:
        """Gera chave de cache baseada no prompt."""
        content = f"{prompt}:{size}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _check_cache(self, cache_key: str) -> str | None:
        """Verifica se imagem está em cache."""
        for ext in [".png", ".jpg", ".webp"]:
            path = IMAGE_CACHE_DIR / f"{cache_key}{ext}"
            if path.exists():
                return str(path)
        return None

    async def generate(
        self,
        prompt: str,
        size: Literal["1024x1024", "1024x1792", "1792x1024"] = "1024x1792",
        quality: Literal["standard", "hd"] = "standard",
        style: Literal["natural", "vivid"] = "natural",
        output_path: str | None = None,
        use_cache: bool = True,
    ) -> str:
        """Gera uma imagem a partir de prompt.

        Args:
            prompt: Descrição da imagem
            size: Tamanho da imagem
            quality: Qualidade (standard ou hd)
            style: Estilo (natural ou vivid)
            output_path: Path para salvar (ou gera automático)
            use_cache: Se deve usar cache

        Returns:
            Path da imagem gerada
        """
        model = self.client.config.image_model

        # Verificar cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, size)
            cached = self._check_cache(cache_key)
            if cached:
                if output_path:
                    shutil.copy2(cached, output_path)
                    return output_path
                return cached

        # Gerar imagem
        response = await self.client.async_client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality=quality,
            style=style,
            n=1,
            response_format="url",
        )

        image_url = response.data[0].url

        # Baixar imagem
        if not output_path:
            cache_key = self._get_cache_key(prompt, size)
            output_path = str(IMAGE_CACHE_DIR / f"{cache_key}.png")

        await self._download_image(image_url, output_path)

        # Track usage
        self.client.tracker.record(
            model=model,
            operation="image_generate",
            images=1,
        )

        return output_path

    async def generate_product_scene(
        self,
        product_description: str,
        scene_context: str,
        output_path: str | None = None,
        size: Literal["1024x1024", "1024x1792", "1792x1024"] = "1024x1792",
    ) -> str:
        """Gera cena com produto em contexto.

        Inclui instrução de preservação de identidade.

        Args:
            product_description: Descrição detalhada do produto
            scene_context: Contexto da cena (ex: "aeroporto", "praia")
            output_path: Path para salvar
            size: Tamanho da imagem
        """
        prompt = f"""
{self.PRODUCT_IDENTITY_LOCK}

Product: {product_description}

Scene: Create a realistic, commercial-quality photograph showing this exact product in the following context: {scene_context}

Style: Clean, bright, natural lighting. TikTok-friendly vertical composition.
The product should be clearly visible and recognizable.
"""

        return await self.generate(
            prompt=prompt,
            size=size,
            quality="hd",
            style="natural",
            output_path=output_path,
        )

    async def generate_hook_image(
        self,
        hook_concept: str,
        product_description: str | None = None,
        output_path: str | None = None,
    ) -> str:
        """Gera imagem para hook (primeiros 2 segundos).

        Args:
            hook_concept: Conceito visual do hook
            product_description: Descrição do produto se deve aparecer
            output_path: Path para salvar
        """
        product_part = ""
        if product_description:
            product_part = f"""
{self.PRODUCT_IDENTITY_LOCK}
Product to include: {product_description}
"""

        prompt = f"""
{product_part}

Create a striking, attention-grabbing image for a TikTok video hook.

Hook concept: {hook_concept}

Style:
- Bold, eye-catching composition
- Vertical format (9:16)
- High contrast
- Immediate visual impact
- Should make viewer stop scrolling
"""

        return await self.generate(
            prompt=prompt,
            size="1024x1792",
            quality="hd",
            style="vivid",
            output_path=output_path,
        )

    async def enhance_product_photo(
        self,
        original_description: str,
        improvements: list[str],
        output_path: str | None = None,
    ) -> str:
        """Gera versão melhorada de foto de produto.

        Mantém identidade do produto, melhora qualidade visual.

        Args:
            original_description: Descrição detalhada do produto original
            improvements: Lista de melhorias desejadas
            output_path: Path para salvar
        """
        improvements_text = "\n".join(f"- {imp}" for imp in improvements)

        prompt = f"""
{self.PRODUCT_IDENTITY_LOCK}

Original product: {original_description}

Create an enhanced, professional product photograph with these improvements:
{improvements_text}

CRITICAL: The product must remain EXACTLY as described. Only improve:
- Lighting quality
- Background cleanliness
- Image sharpness
- Professional framing
- Commercial appeal

Do NOT change the product itself in any way.
"""

        return await self.generate(
            prompt=prompt,
            size="1024x1792",
            quality="hd",
            style="natural",
            output_path=output_path,
        )

    async def _download_image(self, url: str, output_path: str) -> None:
        """Baixa imagem de URL."""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            response.raise_for_status()

            with open(output_path, "wb") as f:
                f.write(response.content)


# Singleton
_service: ImageService | None = None


def get_image_service() -> ImageService:
    """Retorna instância singleton do serviço."""
    global _service
    if _service is None:
        _service = ImageService()
    return _service
