"""Product Analyzer — Analisa produto e fotos para gerar ProductProfile.

Usa OpenAI Vision para entender o produto e gerar insights de venda.
"""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING

from app.creative.schemas import (
    ProductProfile,
    VisualCharacteristics,
)
from app.openai.client import get_openai_client
from app.openai.vision import get_vision_service


if TYPE_CHECKING:
    from app.models import Product


# Cache de análises
ANALYSIS_CACHE_DIR = Path("/data/cache/product_analysis")


class ProductAnalyzer:
    """Analisa produtos usando OpenAI Vision para gerar ProductProfile."""

    def __init__(self):
        self.vision = get_vision_service()
        self.client = get_openai_client()
        ANALYSIS_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, product_id: int, image_urls: list[str]) -> str:
        """Gera chave de cache baseada no produto e imagens."""
        content = f"{product_id}:{':'.join(sorted(image_urls))}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _check_cache(self, cache_key: str) -> ProductProfile | None:
        """Verifica se análise está em cache."""
        cache_path = ANALYSIS_CACHE_DIR / f"{cache_key}.json"
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text())
                return ProductProfile.model_validate(data)
            except Exception:
                pass
        return None

    def _save_cache(self, cache_key: str, profile: ProductProfile) -> None:
        """Salva análise no cache."""
        cache_path = ANALYSIS_CACHE_DIR / f"{cache_key}.json"
        cache_path.write_text(profile.model_dump_json(indent=2))

    async def analyze(
        self,
        product: "Product",
        image_urls: list[str] | None = None,
        use_cache: bool = True,
    ) -> ProductProfile:
        """Analisa produto e gera ProductProfile completo.

        Args:
            product: Objeto Product do banco
            image_urls: URLs das imagens (ou usa product.image_url)
            use_cache: Se deve usar cache de análises anteriores

        Returns:
            ProductProfile com análise completa
        """
        # Coletar imagens
        images = image_urls or []
        if not images and product.image_url:
            images = [product.image_url]

        if not images:
            raise ValueError("Produto precisa de pelo menos uma imagem para análise")

        # Verificar cache
        if use_cache:
            cache_key = self._get_cache_key(product.id, images)
            cached = self._check_cache(cache_key)
            if cached:
                return cached

        # Construir contexto do produto
        product_context = self._build_product_context(product)

        # Analisar com Vision
        profile = await self._analyze_with_vision(
            product_id=str(product.id),
            images=images,
            context=product_context,
        )

        # Salvar no cache
        if use_cache:
            self._save_cache(cache_key, profile)

        return profile

    def _build_product_context(self, product: "Product") -> str:
        """Constrói contexto textual do produto."""
        parts = [
            f"Nome: {product.name}",
            f"Categoria: {product.category}",
        ]

        if product.description:
            parts.append(f"Descrição: {product.description}")

        if product.notes:
            parts.append(f"Notas: {product.notes}")

        if product.price:
            parts.append(f"Preço: {product.price} {product.currency or 'EUR'}")

        if product.rating:
            parts.append(f"Rating: {product.rating}/5 ({product.reviews_count} reviews)")

        return "\n".join(parts)

    async def _analyze_with_vision(
        self,
        product_id: str,
        images: list[str],
        context: str,
    ) -> ProductProfile:
        """Executa análise com OpenAI Vision."""
        system_prompt = """Você é um especialista em marketing de produtos para TikTok Shop e e-commerce.

Analise as imagens do produto e o contexto fornecido para criar um perfil completo de venda.

Seu objetivo é descobrir:
1. Que problemas este produto resolve na vida das pessoas?
2. Que desejos ele satisfaz?
3. Como demonstrar seus benefícios visualmente?
4. Quais objeções compradores podem ter?
5. Para quem é este produto?
6. O que NÃO podemos afirmar sem provas?

Seja específico e prático. Pense em como um criador de conteúdo de TikTok venderia isso.

IMPORTANTE: Na análise visual, seja extremamente preciso sobre:
- Cores exatas do produto
- Formato e proporções
- Todos os componentes visíveis (bolsos, zíperes, alças, etc)
- Logos ou marcas visíveis
- Características que distinguem este produto

Estas informações visuais são CRÍTICAS para garantir fidelidade quando gerarmos imagens."""

        user_prompt = f"""Analise este produto:

{context}

As imagens mostram o produto real. Analise-as cuidadosamente.

Retorne um JSON com a seguinte estrutura:

{{
    "product_id": "{product_id}",
    "problems": ["problema 1", "problema 2", ...],
    "desires": ["desejo 1", "desejo 2", ...],
    "functional_benefits": ["benefício funcional 1", ...],
    "emotional_benefits": ["benefício emocional 1", ...],
    "objections": ["objeção comum 1", ...],
    "audiences": ["público 1", ...],
    "demonstrations": ["forma de demonstrar 1", ...],
    "use_cases": ["situação de uso 1", ...],
    "factual_claims": ["afirmação permitida 1", ...],
    "prohibited_claims": ["afirmação proibida 1", ...],
    "visual_characteristics": {{
        "colors": ["cor 1", "cor 2"],
        "shape": "descrição do formato",
        "materials": ["material 1"],
        "logos": ["logo se visível"],
        "distinctive_features": ["característica única 1", ...]
    }},
    "confidence_score": 0.85
}}

Seja específico para TikTok Shop no Brasil. Use português para os textos de venda."""

        result = await self.vision.analyze_structured(
            schema=ProductProfile,
            images=images,
            prompt=user_prompt,
            system_prompt=system_prompt,
            detail="high",
        )

        # Garantir que product_id está correto
        result.product_id = product_id
        result.analyzed_at = datetime.utcnow()
        result.model_used = self.client.config.creative_model

        return result

    async def analyze_from_data(
        self,
        product_id: str,
        name: str,
        category: str,
        image_urls: list[str],
        description: str | None = None,
        price: float | None = None,
        currency: str = "EUR",
    ) -> ProductProfile:
        """Analisa produto a partir de dados simples (sem objeto Product).

        Útil para análise rápida ou testes.
        """
        # Construir contexto
        parts = [
            f"Nome: {name}",
            f"Categoria: {category}",
        ]

        if description:
            parts.append(f"Descrição: {description}")

        if price:
            parts.append(f"Preço: {price} {currency}")

        context = "\n".join(parts)

        return await self._analyze_with_vision(
            product_id=product_id,
            images=image_urls,
            context=context,
        )

    async def get_selling_hooks(
        self,
        profile: ProductProfile,
        count: int = 5,
    ) -> list[dict]:
        """Gera sugestões de hooks baseadas no ProductProfile.

        Args:
            profile: ProductProfile analisado
            count: Número de hooks a gerar

        Returns:
            Lista de dicts com tipo, texto e conceito visual
        """
        from app.openai.structured import get_structured_service
        from pydantic import BaseModel, Field
        from app.creative.schemas import HookType

        class HookSuggestion(BaseModel):
            type: HookType
            text: str = Field(description="Texto do hook em espanhol")
            visual_concept: str = Field(description="Conceito visual para acompanhar")
            target_emotion: str = Field(description="Emoção que queremos provocar")

        class HookSuggestions(BaseModel):
            hooks: list[HookSuggestion]

        service = get_structured_service()

        result = await service.generate(
            schema=HookSuggestions,
            system_prompt="""Você é um especialista em hooks virais para TikTok Shop.

Crie hooks que:
1. Interrompam o scroll em menos de 2 segundos
2. Conectem com problemas ou desejos reais
3. Não sejam genéricos ou clickbait vazio
4. Funcionem em português do Brasil
5. Possam ser demonstrados visualmente

Cada hook deve ser único e atacar um ângulo diferente.""",
            user_prompt=f"""Baseado neste perfil de produto, gere {count} hooks diferentes:

Problemas: {', '.join(profile.problems[:5])}
Desejos: {', '.join(profile.desires[:5])}
Benefícios: {', '.join(profile.functional_benefits[:5])}
Público: {', '.join(profile.audiences[:3])}

Gere hooks para TikTok Shop Brasil. Varie os tipos (problem, desire, price, curiosity, demonstration, surprise).""",
        )

        return [h.model_dump() for h in result.hooks]


# Singleton
_analyzer: ProductAnalyzer | None = None


def get_product_analyzer() -> ProductAnalyzer:
    """Retorna instância singleton do analyzer."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ProductAnalyzer()
    return _analyzer
