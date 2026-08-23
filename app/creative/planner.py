"""Creative Planner — Gera CreativePlans combinando ProductProfile + CreativeDNA.

O coração do Creative Intelligence Engine.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.creative.schemas import (
    CreativeAngle,
    CreativeDNA,
    CreativePlan,
    Hook,
    HookType,
    PacingLevel,
    ProductProfile,
    SceneGenerationMode,
    ScenePlan,
    ScenePurpose,
    CaptionPlan,
    WinningPatterns,
    ComplianceStatus,
)
from app.openai.client import get_openai_client
from app.openai.structured import get_structured_service


# Mapeamento de ângulos para estratégias
ANGLE_STRATEGIES = {
    CreativeAngle.PROBLEM_SOLUTION: {
        "description": "Foca no problema que o produto resolve",
        "hook_types": [HookType.PROBLEM, HookType.CURIOSITY],
        "structure": [ScenePurpose.HOOK, ScenePurpose.PROBLEM, ScenePurpose.REVEAL, 
                      ScenePurpose.DEMONSTRATION, ScenePurpose.BENEFIT, ScenePurpose.CTA],
    },
    CreativeAngle.TRAVEL_DESIRE: {
        "description": "Conecta com desejo de viajar/aventura",
        "hook_types": [HookType.DESIRE, HookType.CURIOSITY],
        "structure": [ScenePurpose.HOOK, ScenePurpose.BENEFIT, ScenePurpose.DEMONSTRATION,
                      ScenePurpose.PROOF, ScenePurpose.OFFER, ScenePurpose.CTA],
    },
    CreativeAngle.PRICE_SHOCK: {
        "description": "Destaca o valor/preço acessível",
        "hook_types": [HookType.PRICE, HookType.SURPRISE],
        "structure": [ScenePurpose.HOOK, ScenePurpose.REVEAL, ScenePurpose.BENEFIT,
                      ScenePurpose.DEMONSTRATION, ScenePurpose.OFFER, ScenePurpose.CTA],
    },
    CreativeAngle.DEMONSTRATION: {
        "description": "Foca em mostrar o produto em ação",
        "hook_types": [HookType.DEMONSTRATION, HookType.CURIOSITY],
        "structure": [ScenePurpose.HOOK, ScenePurpose.DEMONSTRATION, ScenePurpose.BENEFIT,
                      ScenePurpose.PROOF, ScenePurpose.OFFER, ScenePurpose.CTA],
    },
    CreativeAngle.DISCOVERY: {
        "description": "Apresenta como descoberta/achado",
        "hook_types": [HookType.CURIOSITY, HookType.SURPRISE],
        "structure": [ScenePurpose.HOOK, ScenePurpose.REVEAL, ScenePurpose.DEMONSTRATION,
                      ScenePurpose.BENEFIT, ScenePurpose.CTA],
    },
    CreativeAngle.BEFORE_AFTER: {
        "description": "Mostra transformação antes/depois",
        "hook_types": [HookType.PROBLEM, HookType.DEMONSTRATION],
        "structure": [ScenePurpose.HOOK, ScenePurpose.PROBLEM, ScenePurpose.DEMONSTRATION,
                      ScenePurpose.BENEFIT, ScenePurpose.CTA],
    },
    CreativeAngle.COMPARISON: {
        "description": "Compara com alternativas/concorrentes",
        "hook_types": [HookType.CURIOSITY, HookType.PRICE],
        "structure": [ScenePurpose.HOOK, ScenePurpose.PROBLEM, ScenePurpose.REVEAL,
                      ScenePurpose.DEMONSTRATION, ScenePurpose.PROOF, ScenePurpose.CTA],
    },
    CreativeAngle.UNBOXING: {
        "description": "Experiência de unboxing/recebimento",
        "hook_types": [HookType.CURIOSITY, HookType.SURPRISE],
        "structure": [ScenePurpose.HOOK, ScenePurpose.REVEAL, ScenePurpose.BENEFIT,
                      ScenePurpose.DEMONSTRATION, ScenePurpose.CTA],
    },
}


class CreativePlannerInput(BaseModel):
    """Input estruturado para geração de plano criativo."""
    product_id: str
    product_name: str
    problems: list[str]
    desires: list[str]
    benefits: list[str]
    demonstrations: list[str]
    audiences: list[str]
    factual_claims: list[str]
    prohibited_claims: list[str]
    visual_description: str

    angle: CreativeAngle
    target_duration_ms: int = 16000
    language: str = "pt-BR"

    # Insights de referências
    reference_hooks: list[dict] = Field(default_factory=list)
    reference_techniques: list[str] = Field(default_factory=list)
    winning_patterns: list[str] = Field(default_factory=list)


class CreativePlanner:
    """Gera CreativePlans combinando produto e referências."""

    def __init__(self):
        self.structured = get_structured_service()
        self.client = get_openai_client()

    async def plan(
        self,
        product: ProductProfile,
        references: list[CreativeDNA] | None = None,
        patterns: WinningPatterns | None = None,
        angles: list[CreativeAngle] | None = None,
        count: int = 5,
        target_duration_ms: int = 16000,
        language: str = "pt-BR",
    ) -> list[CreativePlan]:
        """Gera múltiplos CreativePlans para um produto.

        Args:
            product: ProductProfile do produto
            references: Lista de CreativeDNA de referências
            patterns: WinningPatterns consolidado
            angles: Ângulos específicos a usar (ou auto-seleciona)
            count: Número de planos a gerar
            target_duration_ms: Duração alvo em ms
            language: Idioma do conteúdo

        Returns:
            Lista de CreativePlans diferentes
        """
        # Selecionar ângulos se não especificados
        if not angles:
            angles = self._select_angles(product, references, count)

        # Garantir que temos ângulos suficientes
        while len(angles) < count:
            angles.append(angles[len(angles) % len(angles)])

        # Extrair insights de referências
        reference_insights = self._extract_reference_insights(references, patterns)

        # Gerar plano para cada ângulo
        plans = []
        for i, angle in enumerate(angles[:count]):
            plan = await self._generate_plan(
                product=product,
                angle=angle,
                reference_insights=reference_insights,
                target_duration_ms=target_duration_ms,
                language=language,
                plan_index=i,
            )
            plans.append(plan)

        return plans

    def _select_angles(
        self,
        product: ProductProfile,
        references: list[CreativeDNA] | None,
        count: int,
    ) -> list[CreativeAngle]:
        """Seleciona ângulos apropriados para o produto."""
        angles = []

        # Se tem problemas fortes, usar problem_solution
        if product.problems and len(product.problems) >= 3:
            angles.append(CreativeAngle.PROBLEM_SOLUTION)

        # Se tem desejos de viagem/lifestyle
        travel_keywords = ["viaj", "trip", "aventur", "vacacione", "aeropuerto"]
        if any(kw in " ".join(product.desires).lower() for kw in travel_keywords):
            angles.append(CreativeAngle.TRAVEL_DESIRE)

        # Se referências têm hook de preço
        if references:
            has_price_hooks = any(
                ref.hook.type == HookType.PRICE for ref in references
            )
            if has_price_hooks:
                angles.append(CreativeAngle.PRICE_SHOCK)

        # Demonstration sempre funciona
        if product.demonstrations:
            angles.append(CreativeAngle.DEMONSTRATION)

        # Discovery é bom para produtos novos
        angles.append(CreativeAngle.DISCOVERY)

        # Preencher com antes/depois e comparação
        if len(angles) < count:
            angles.append(CreativeAngle.BEFORE_AFTER)
        if len(angles) < count:
            angles.append(CreativeAngle.COMPARISON)
        if len(angles) < count:
            angles.append(CreativeAngle.UNBOXING)

        return angles[:count]

    def _extract_reference_insights(
        self,
        references: list[CreativeDNA] | None,
        patterns: WinningPatterns | None,
    ) -> dict:
        """Extrai insights úteis das referências."""
        insights = {
            "hooks": [],
            "techniques": [],
            "patterns": [],
            "structures": [],
        }

        if references:
            for ref in references[:5]:  # Limitar a 5
                insights["hooks"].append({
                    "type": ref.hook.type.value,
                    "concept": ref.hook.concept,
                    "duration": ref.hook.duration_seconds,
                })
                insights["techniques"].extend(ref.techniques[:3])
                insights["structures"].append([s.value for s in ref.structure])

            # Deduplicar técnicas
            insights["techniques"] = list(set(insights["techniques"]))[:10]

        if patterns:
            insights["patterns"] = patterns.common_patterns[:10]

        return insights

    async def _generate_plan(
        self,
        product: ProductProfile,
        angle: CreativeAngle,
        reference_insights: dict,
        target_duration_ms: int,
        language: str,
        plan_index: int,
    ) -> CreativePlan:
        """Gera um CreativePlan específico."""
        strategy = ANGLE_STRATEGIES[angle]

        # Construir input estruturado
        input_data = CreativePlannerInput(
            product_id=product.product_id,
            product_name="",  # Será preenchido pelo prompt
            problems=product.problems[:5],
            desires=product.desires[:5],
            benefits=product.functional_benefits[:5],
            demonstrations=product.demonstrations[:5],
            audiences=product.audiences[:3],
            factual_claims=product.factual_claims[:5],
            prohibited_claims=product.prohibited_claims[:5],
            visual_description=f"Cores: {', '.join(product.visual_characteristics.colors)}. "
                              f"Formato: {product.visual_characteristics.shape}. "
                              f"Características: {', '.join(product.visual_characteristics.distinctive_features[:3])}.",
            angle=angle,
            target_duration_ms=target_duration_ms,
            language=language,
            reference_hooks=reference_insights.get("hooks", []),
            reference_techniques=reference_insights.get("techniques", []),
            winning_patterns=reference_insights.get("patterns", []),
        )

        system_prompt = f"""Você é um criador de conteúdo viral para TikTok Shop no Brasil.

Crie um roteiro completo para um vídeo de {target_duration_ms // 1000} segundos.

ÂNGULO: {angle.value} — {strategy['description']}

ESTRUTURA SUGERIDA: {' → '.join(s.value for s in strategy['structure'])}

REGRAS:
1. Hook em 0-2 segundos que interrompa o scroll
2. Mostrar produto rapidamente (antes de 3s)
3. Demonstrar benefício de forma visual
4. CTA que continue a história
5. Narração natural, não comercial
6. Texto na tela curto e impactante
7. NUNCA inventar características ou benefícios não listados
8. NUNCA usar claims proibidos

O hook é a parte mais importante. Deve ser específico, não genérico.

EVITAR frases como:
- "Você não vai acreditar nisso"
- "Este produto vai mudar sua vida"
- "A solução perfeita"
- "Imperdível"

PREFERIR:
- Problemas específicos
- Situações reconhecíveis
- Números concretos
- Demonstrações visuais"""

        user_prompt = f"""Crie um roteiro para este produto:

PRODUTO ID: {input_data.product_id}

PROBLEMAS QUE RESOLVE:
{chr(10).join(f'- {p}' for p in input_data.problems)}

DESEJOS RELACIONADOS:
{chr(10).join(f'- {d}' for d in input_data.desires)}

BENEFÍCIOS:
{chr(10).join(f'- {b}' for b in input_data.benefits)}

FORMAS DE DEMONSTRAR:
{chr(10).join(f'- {d}' for d in input_data.demonstrations)}

PÚBLICO-ALVO:
{chr(10).join(f'- {a}' for a in input_data.audiences)}

CLAIMS PERMITIDOS:
{chr(10).join(f'- {c}' for c in input_data.factual_claims)}

CLAIMS PROIBIDOS (NÃO USAR):
{chr(10).join(f'- {c}' for c in input_data.prohibited_claims)}

DESCRIÇÃO VISUAL DO PRODUTO:
{input_data.visual_description}

INSIGHTS DE REFERÊNCIAS VENCEDORAS:
Hooks que funcionam: {input_data.reference_hooks[:3]}
Técnicas: {input_data.reference_techniques[:5]}
Padrões: {input_data.winning_patterns[:5]}

Gere o roteiro completo no formato CreativePlan. Todo o conteúdo deve estar em português do Brasil."""

        # Gerar plano
        plan = await self.structured.generate(
            schema=CreativePlan,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.8,  # Maior variedade
        )

        # Preencher campos adicionais
        plan.id = f"plan_{uuid.uuid4().hex[:8]}"
        plan.product_id = product.product_id
        plan.version = plan_index + 1
        plan.target_duration_ms = target_duration_ms
        plan.language = language
        plan.angle = angle
        plan.created_at = datetime.utcnow()
        plan.model_used = self.client.config.creative_model
        plan.compliance_status = ComplianceStatus.PENDING

        # Garantir que hook tem ID
        if not plan.hook.id:
            plan.hook.id = f"hook_{uuid.uuid4().hex[:8]}"

        # Garantir que scenes têm IDs
        for i, scene in enumerate(plan.scenes):
            if not scene.id:
                scene.id = f"scene_{i}_{uuid.uuid4().hex[:4]}"
            scene.order = i

        return plan

    async def generate_variations(
        self,
        base_plan: CreativePlan,
        count: int = 3,
        vary: Literal["hook", "narration", "cta"] = "hook",
    ) -> list[CreativePlan]:
        """Gera variações de um plano existente.

        Útil para A/B testing.

        Args:
            base_plan: Plano base para variar
            count: Número de variações
            vary: O que variar (hook, narration ou cta)
        """
        variations = []

        for i in range(count):
            variation = base_plan.model_copy(deep=True)
            variation.id = f"plan_{uuid.uuid4().hex[:8]}"
            variation.version = base_plan.version + i + 1

            if vary == "hook":
                # Gerar novo hook mantendo o resto
                new_hook = await self._generate_hook_variation(
                    base_plan=base_plan,
                    variation_index=i,
                )
                variation.hook = new_hook
                # Atualizar primeira cena se for hook
                if variation.scenes and variation.scenes[0].purpose == ScenePurpose.HOOK:
                    variation.scenes[0].narration = new_hook.text
                    variation.scenes[0].visual_description = new_hook.visual_concept

            elif vary == "narration":
                # Regerar narração mantendo estrutura
                variation.full_narration = await self._generate_narration_variation(
                    base_plan=base_plan,
                    variation_index=i,
                )

            elif vary == "cta":
                # Gerar novo CTA
                new_cta = await self._generate_cta_variation(
                    base_plan=base_plan,
                    variation_index=i,
                )
                variation.cta_text = new_cta["text"]
                variation.cta_voice = new_cta["voice"]
                variation.cta_strategy = new_cta["strategy"]

            variation.novelty_elements.append(f"variation_{vary}_{i}")
            variations.append(variation)

        return variations

    async def _generate_hook_variation(
        self,
        base_plan: CreativePlan,
        variation_index: int,
    ) -> Hook:
        """Gera variação do hook."""
        result = await self.structured.generate(
            schema=Hook,
            system_prompt="Crie uma variação do hook para teste A/B. Mantenha o mesmo tipo mas mude o texto e conceito visual.",
            user_prompt=f"""Hook original:
Tipo: {base_plan.hook.type.value}
Texto: {base_plan.hook.text}
Visual: {base_plan.hook.visual_concept}

Ângulo do vídeo: {base_plan.angle.value}
Variação número: {variation_index + 1}

Crie uma alternativa diferente mas igualmente efetiva.""",
        )

        result.id = f"hook_{uuid.uuid4().hex[:8]}"
        return result

    async def _generate_narration_variation(
        self,
        base_plan: CreativePlan,
        variation_index: int,
    ) -> str:
        """Gera variação da narração."""
        from pydantic import BaseModel

        class NarrationResult(BaseModel):
            narration: str

        result = await self.structured.generate(
            schema=NarrationResult,
            system_prompt="Reescreva a narração mantendo a mesma estrutura e duração aproximada.",
            user_prompt=f"""Narração original:
{base_plan.full_narration}

Variação número: {variation_index + 1}

Reescreva usando palavras diferentes mas mantendo:
- Mesmo tom
- Mesma estrutura
- Mesmos pontos-chave
- Mesma duração aproximada""",
        )

        return result.narration

    async def _generate_cta_variation(
        self,
        base_plan: CreativePlan,
        variation_index: int,
    ) -> dict:
        """Gera variação do CTA."""
        from pydantic import BaseModel

        class CTAResult(BaseModel):
            text: str
            voice: str
            strategy: str

        result = await self.structured.generate(
            schema=CTAResult,
            system_prompt="Crie uma variação do call-to-action para teste A/B.",
            user_prompt=f"""CTA original:
Texto: {base_plan.cta_text}
Estratégia: {base_plan.cta_strategy}

Variação número: {variation_index + 1}

Crie uma alternativa que:
- Seja diferente mas igualmente efetiva
- Mantenha a mesma intenção
- Use linguagem natural de TikTok""",
        )

        return result.model_dump()


# Singleton
_planner: CreativePlanner | None = None


def get_creative_planner() -> CreativePlanner:
    """Retorna instância singleton do planner."""
    global _planner
    if _planner is None:
        _planner = CreativePlanner()
    return _planner
