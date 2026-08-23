"""Product Fidelity Validator — QA multimodal para imagens de produto.

Compara imagem original com imagem gerada/editada para garantir
que o produto não foi alterado pela IA.
"""

from __future__ import annotations

from pathlib import Path

from app.creative.schemas import ProductFidelityResult, ProductProfile
from app.openai.client import get_openai_client
from app.openai.vision import get_vision_service


class ProductFidelityValidator:
    """Valida fidelidade do produto em imagens geradas."""

    # Thresholds de aprovação
    MIN_SCORE = 90
    REQUIRE_SAME_PRODUCT = True
    ALLOW_INVENTED_FEATURES = False

    def __init__(self):
        self.vision = get_vision_service()
        self.client = get_openai_client()

    async def validate(
        self,
        original_image: str,
        generated_image: str,
        product_profile: ProductProfile | None = None,
    ) -> ProductFidelityResult:
        """Valida se imagem gerada preserva identidade do produto.

        Args:
            original_image: Path/URL da imagem original
            generated_image: Path/URL da imagem gerada
            product_profile: ProductProfile opcional para contexto extra

        Returns:
            ProductFidelityResult com score e detalhes
        """
        # Construir prompt de comparação
        context = ""
        if product_profile:
            vc = product_profile.visual_characteristics
            context = f"""
CARACTERÍSTICAS ESPERADAS DO PRODUTO:
- Cores: {', '.join(vc.colors)}
- Formato: {vc.shape}
- Materiais: {', '.join(vc.materials) if vc.materials else 'não especificado'}
- Logos: {', '.join(vc.logos) if vc.logos else 'não especificado'}
- Características distintivas: {', '.join(vc.distinctive_features)}

Verifique se TODAS estas características estão preservadas na imagem gerada.
"""

        comparison_prompt = f"""Compare estas duas imagens do MESMO produto.

A PRIMEIRA imagem é a ORIGINAL (referência de verdade).
A SEGUNDA imagem é GERADA por IA.

{context}

ANALISE CUIDADOSAMENTE:

1. É o MESMO produto? (não uma versão diferente)
2. As CORES estão preservadas exatamente?
3. O FORMATO/PROPORÇÕES estão corretos?
4. Todos os COMPONENTES existem? (bolsos, zíperes, alças, etc)
5. LOGOS ou marcas estão preservados?
6. A IA INVENTOU algo que não existe no original?
7. Algo do original está FALTANDO?

CRITÉRIOS DE APROVAÇÃO:
- Score >= 90
- Mesmo produto = true
- Nenhuma feature inventada

Seja RIGOROSO. A fidelidade do produto é CRÍTICA para vendas."""

        result = await self.vision.analyze_structured(
            schema=ProductFidelityResult,
            images=[original_image, generated_image],
            prompt=comparison_prompt,
            system_prompt=(
                "Você é um especialista em controle de qualidade visual. "
                "Sua tarefa é garantir que imagens geradas por IA preservem "
                "EXATAMENTE a identidade física do produto original. "
                "Seja muito rigoroso - erros aqui custam vendas e confiança."
            ),
        )

        # Preencher paths
        result.original_image_path = original_image
        result.generated_image_path = generated_image

        # Aplicar regras de aprovação
        result.approved = self._check_approval(result)

        if not result.approved:
            result.rejection_reasons = self._get_rejection_reasons(result)

        return result

    def _check_approval(self, result: ProductFidelityResult) -> bool:
        """Aplica regras de aprovação."""
        if result.score < self.MIN_SCORE:
            return False

        if self.REQUIRE_SAME_PRODUCT and not result.same_product:
            return False

        if self.ALLOW_INVENTED_FEATURES is False and result.invented_features:
            return False

        # Verificações individuais
        if not result.color_preserved:
            return False

        if not result.shape_preserved:
            return False

        if not result.components_preserved:
            return False

        return True

    def _get_rejection_reasons(self, result: ProductFidelityResult) -> list[str]:
        """Gera lista de motivos de rejeição."""
        reasons = []

        if result.score < self.MIN_SCORE:
            reasons.append(f"Score {result.score:.0f} abaixo do mínimo {self.MIN_SCORE}")

        if not result.same_product:
            reasons.append("Não é o mesmo produto")

        if not result.color_preserved:
            reasons.append("Cores alteradas")

        if not result.shape_preserved:
            reasons.append("Formato/proporções alterados")

        if not result.components_preserved:
            reasons.append("Componentes alterados ou faltando")

        if not result.logo_preserved:
            reasons.append("Logo não preservado")

        if result.invented_features:
            reasons.append(f"Features inventadas: {', '.join(result.invented_features)}")

        if result.missing_features:
            reasons.append(f"Features faltando: {', '.join(result.missing_features)}")

        return reasons

    async def validate_batch(
        self,
        original_image: str,
        generated_images: list[str],
        product_profile: ProductProfile | None = None,
    ) -> list[ProductFidelityResult]:
        """Valida múltiplas imagens geradas contra uma original.

        Args:
            original_image: Path/URL da imagem original
            generated_images: Lista de paths/URLs das imagens geradas
            product_profile: ProductProfile para contexto

        Returns:
            Lista de ProductFidelityResult
        """
        results = []

        for gen_img in generated_images:
            try:
                result = await self.validate(
                    original_image=original_image,
                    generated_image=gen_img,
                    product_profile=product_profile,
                )
                results.append(result)
            except Exception as e:
                # Criar resultado de erro
                results.append(ProductFidelityResult(
                    score=0,
                    same_product=False,
                    color_preserved=False,
                    shape_preserved=False,
                    components_preserved=False,
                    logo_preserved=False,
                    approved=False,
                    rejection_reasons=[f"Erro na validação: {str(e)}"],
                    original_image_path=original_image,
                    generated_image_path=gen_img,
                ))

        return results

    async def quick_check(
        self,
        original_image: str,
        generated_image: str,
    ) -> bool:
        """Verificação rápida se imagem passa (sem detalhes).

        Útil para loops de retry.

        Args:
            original_image: Path/URL da imagem original
            generated_image: Path/URL da imagem gerada

        Returns:
            True se aprovada, False se rejeitada
        """
        result = await self.validate(original_image, generated_image)
        return result.approved

    def get_retry_guidance(self, result: ProductFidelityResult) -> str:
        """Gera orientação para retry baseado nos problemas encontrados.

        Útil para ajustar prompt de geração.

        Args:
            result: Resultado da validação que falhou

        Returns:
            String com orientação para nova geração
        """
        guidance_parts = [
            "A imagem anterior foi rejeitada. Na próxima geração:"
        ]

        if not result.color_preserved:
            guidance_parts.append("- PRESERVAR EXATAMENTE as cores originais")

        if not result.shape_preserved:
            guidance_parts.append("- MANTER formato e proporções idênticos")

        if not result.components_preserved:
            guidance_parts.append("- NÃO adicionar nem remover componentes")

        if result.invented_features:
            guidance_parts.append(
                f"- NÃO inventar: {', '.join(result.invented_features)}"
            )

        if result.missing_features:
            guidance_parts.append(
                f"- INCLUIR: {', '.join(result.missing_features)}"
            )

        guidance_parts.append(
            "- O produto deve ser IDÊNTICO ao original, "
            "apenas fundo/iluminação podem mudar"
        )

        return "\n".join(guidance_parts)


# Singleton
_validator: ProductFidelityValidator | None = None


def get_fidelity_validator() -> ProductFidelityValidator:
    """Retorna instância singleton do validator."""
    global _validator
    if _validator is None:
        _validator = ProductFidelityValidator()
    return _validator
