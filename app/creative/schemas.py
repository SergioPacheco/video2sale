"""Creative Intelligence Engine — Core Schemas.

Estruturas de dados para todo o pipeline criativo usando Pydantic v2
com suporte a JSON Schema para OpenAI Structured Outputs.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class HookType(str, Enum):
    """Tipos de hook para interromper scroll."""
    PROBLEM = "problem"
    DESIRE = "desire"
    PRICE = "price"
    CURIOSITY = "curiosity"
    DEMONSTRATION = "demonstration"
    SURPRISE = "surprise"


class CreativeAngle(str, Enum):
    """Ângulos de venda para criativos."""
    PROBLEM_SOLUTION = "problem_solution"
    TRAVEL_DESIRE = "travel_desire"
    PRICE_SHOCK = "price_shock"
    DEMONSTRATION = "demonstration"
    DISCOVERY = "discovery"
    BEFORE_AFTER = "before_after"
    COMPARISON = "comparison"
    UNBOXING = "unboxing"


class SceneGenerationMode(str, Enum):
    """Como gerar cada cena."""
    IMAGE_MOTION = "image_motion"      # FFmpeg zoom/pan sobre imagem
    SORA = "sora"                       # OpenAI video generation
    PRODUCT_COMPOSITE = "product_composite"  # Produto sobre fundo
    TEXT_ANIMATION = "text"             # Remotion/FFmpeg texto animado
    STOCK_VIDEO = "stock_video"         # Vídeo de biblioteca


class ScenePurpose(str, Enum):
    """Propósito narrativo da cena."""
    HOOK = "hook"
    PROBLEM = "problem"
    REVEAL = "reveal"
    DEMONSTRATION = "demonstration"
    BENEFIT = "benefit"
    PROOF = "proof"
    OFFER = "offer"
    CTA = "cta"


class PacingLevel(str, Enum):
    """Velocidade/ritmo do vídeo."""
    SLOW = "slow"
    MEDIUM = "medium"
    FAST = "fast"


class ComplianceStatus(str, Enum):
    """Status de compliance do criativo."""
    APPROVED = "approved"
    NEEDS_ADJUSTMENT = "needs_adjustment"
    REJECTED = "rejected"
    PENDING = "pending"


# =============================================================================
# PRODUCT PROFILE — Output do ProductAnalyzer
# =============================================================================

class VisualCharacteristics(BaseModel):
    """Características visuais invariáveis do produto."""
    colors: list[str] = Field(description="Cores principais do produto")
    shape: str = Field(description="Formato geral do produto")
    materials: list[str] = Field(default_factory=list, description="Materiais visíveis")
    logos: list[str] = Field(default_factory=list, description="Logos ou marcas visíveis")
    distinctive_features: list[str] = Field(description="Características distintivas únicas")


class ProductProfile(BaseModel):
    """Perfil completo do produto gerado por análise de IA.

    Usado como input para CreativePlanner e para validação de fidelidade.
    """
    product_id: str = Field(description="ID do produto no banco")

    # O que o produto resolve/oferece
    problems: list[str] = Field(description="Problemas que o produto resolve")
    desires: list[str] = Field(description="Desejos relacionados ao produto")
    functional_benefits: list[str] = Field(description="Benefícios funcionais demonstráveis")
    emotional_benefits: list[str] = Field(description="Benefícios emocionais")

    # Objeções e público
    objections: list[str] = Field(description="Objeções comuns de compradores")
    audiences: list[str] = Field(description="Públicos-alvo prováveis")

    # Demonstração
    demonstrations: list[str] = Field(description="Formas de demonstrar o produto")
    use_cases: list[str] = Field(description="Situações de uso")

    # Claims e compliance
    factual_claims: list[str] = Field(description="Afirmações que podem ser feitas")
    prohibited_claims: list[str] = Field(description="Afirmações proibidas ou não verificáveis")

    # Visual (crítico para fidelidade)
    visual_characteristics: VisualCharacteristics

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(default="gpt-4o")
    confidence_score: float = Field(default=0.0, ge=0, le=1)


# =============================================================================
# CREATIVE DNA — Output do CompetitorVideoAnalyzer
# =============================================================================

class HookAnalysis(BaseModel):
    """Análise do hook de um vídeo de referência."""
    type: HookType
    duration_seconds: float = Field(ge=0, le=5)
    concept: str = Field(description="Conceito/ideia do hook")
    visual_mechanism: str = Field(description="Como o visual funciona com o hook")
    text_used: str | None = Field(default=None, description="Texto usado no hook se houver")


class ReferenceScene(BaseModel):
    """Cena identificada em vídeo de referência."""
    start_seconds: float
    end_seconds: float
    purpose: ScenePurpose
    description: str
    camera_movement: str | None = None
    text_overlay: str | None = None


class CreativeDNA(BaseModel):
    """DNA criativo extraído de um vídeo de referência.

    Captura POR QUE o vídeo funciona, não O QUE ele mostra.
    """
    reference_id: str = Field(description="ID da referência no banco")
    source_url: str | None = Field(default=None, description="URL original se disponível")

    # Duração e estrutura
    duration_seconds: float
    structure: list[ScenePurpose] = Field(description="Sequência de propósitos das cenas")

    # Hook (crítico)
    hook: HookAnalysis

    # Cenas
    scenes: list[ReferenceScene]

    # Pacing
    pacing: PacingLevel
    average_shot_duration: float = Field(description="Duração média de cada tomada em segundos")

    # Técnicas identificadas
    techniques: list[str] = Field(description="Técnicas usadas (ex: zoom rápido, corte seco)")
    emotional_triggers: list[str] = Field(description="Gatilhos emocionais usados")
    curiosity_mechanisms: list[str] = Field(description="Como mantém curiosidade")
    demonstrations: list[str] = Field(description="Tipos de demonstração usados")

    # Estratégias
    text_overlay_strategy: list[str] = Field(description="Como usa texto na tela")
    cta_strategy: str = Field(description="Estratégia de call-to-action")
    audio_strategy: str = Field(description="Estratégia de áudio/voz")

    # Insights
    reasons_it_works: list[str] = Field(description="Por que este vídeo provavelmente funciona")

    # Transcrição
    transcript: str | None = Field(default=None, description="Transcrição do áudio")
    language: str = Field(default="pt-BR")

    # Metadata
    analyzed_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(default="gpt-4o")


class WinningPatterns(BaseModel):
    """Padrões identificados em múltiplas referências vencedoras."""
    common_patterns: list[str] = Field(description="Padrões que aparecem em múltiplas refs")
    common_hook_types: list[HookType]
    common_structures: list[list[ScenePurpose]]
    average_duration: float
    recommended_pacing: PacingLevel
    key_insights: list[str]


# =============================================================================
# HOOK — Entidade de primeira classe
# =============================================================================

class Hook(BaseModel):
    """Hook como entidade rastreável para métricas.

    Cada hook tem ID único para medir CTR e aprender o que funciona.
    """
    id: str = Field(description="ID único do hook")
    type: HookType
    text: str = Field(description="Texto do hook (fala ou legenda)")
    visual_concept: str = Field(description="Conceito visual do hook")
    target_duration_ms: int = Field(default=2000, description="Duração alvo em ms")
    source_insight: str | None = Field(default=None, description="De qual referência/insight veio")

    # Para rastreamento de performance
    times_used: int = Field(default=0)
    avg_ctr: float | None = Field(default=None)


# =============================================================================
# SCENE PLAN — Planejamento de cada cena
# =============================================================================

class ScenePlan(BaseModel):
    """Plano detalhado para uma cena do vídeo."""
    id: str
    order: int
    start_ms: int
    end_ms: int

    purpose: ScenePurpose
    generation_mode: SceneGenerationMode

    visual_description: str = Field(description="Descrição do que deve aparecer")
    narration: str | None = Field(default=None, description="Texto da narração")
    text_overlay: str | None = Field(default=None, description="Texto na tela")

    product_must_be_visible: bool = Field(default=True)
    product_asset_id: str | None = Field(default=None, description="ID do asset a usar")

    camera_movement: str | None = Field(default=None, description="Movimento de câmera")
    transition_in: str | None = Field(default=None, description="Transição de entrada")
    transition_out: str | None = Field(default=None, description="Transição de saída")


class CaptionPlan(BaseModel):
    """Legenda sincronizada."""
    start_ms: int
    end_ms: int
    text: str
    emphasis_words: list[str] = Field(default_factory=list)


# =============================================================================
# CREATIVE PLAN — Output do CreativePlanner
# =============================================================================

class CreativePlan(BaseModel):
    """Plano completo para um criativo.

    Gerado pelo CreativePlanner combinando ProductProfile + CreativeDNA[].
    """
    id: str = Field(description="ID único do plano")
    product_id: str
    version: int = Field(default=1)

    # Configuração
    target_duration_ms: int = Field(default=16000)
    language: str = Field(default="pt-BR")

    # Ângulo e estratégia
    angle: CreativeAngle
    strategy_description: str = Field(description="Descrição da estratégia criativa")

    # Hook (entidade separada para rastreamento)
    hook: Hook

    # Cenas
    scenes: list[ScenePlan]

    # Narração completa
    full_narration: str = Field(description="Narração completa para TTS")

    # Legendas
    captions: list[CaptionPlan]

    # CTA
    cta_text: str
    cta_voice: str
    cta_strategy: str

    # Rastreabilidade
    reference_insights: list[str] = Field(description="Insights das referências usados")
    novelty_elements: list[str] = Field(description="Elementos novos/experimentais")

    # Compliance
    risk_flags: list[str] = Field(default_factory=list, description="Alertas de risco")
    compliance_status: ComplianceStatus = Field(default=ComplianceStatus.PENDING)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = Field(default="gpt-4o")


# =============================================================================
# PRODUCT FIDELITY — Output do ProductFidelityValidator
# =============================================================================

class ProductFidelityResult(BaseModel):
    """Resultado da validação de fidelidade do produto.

    Compara imagem original com imagem gerada/editada.
    """
    score: float = Field(ge=0, le=100, description="Score de fidelidade 0-100")

    same_product: bool = Field(description="É o mesmo produto?")
    color_preserved: bool = Field(description="Cores preservadas?")
    shape_preserved: bool = Field(description="Formato preservado?")
    components_preserved: bool = Field(description="Componentes preservados?")
    logo_preserved: bool = Field(description="Logo preservado?")

    invented_features: list[str] = Field(default_factory=list, description="Features inventadas pela IA")
    missing_features: list[str] = Field(default_factory=list, description="Features que sumiram")

    approved: bool = Field(description="Aprovado para uso?")
    rejection_reasons: list[str] = Field(default_factory=list)

    # Metadata
    original_image_path: str
    generated_image_path: str
    validated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# QUALITY GATE — Output do VideoQualityGate
# =============================================================================

class TechnicalQAResult(BaseModel):
    """Resultado da validação técnica do vídeo."""
    file_exists: bool
    codec_valid: bool
    resolution_valid: bool
    aspect_ratio_valid: bool
    duration_valid: bool
    has_audio: bool
    audio_normalized: bool
    no_black_frames: bool
    no_frozen_frames: bool
    file_not_corrupted: bool

    passed: bool
    issues: list[str] = Field(default_factory=list)


class CreativeQAResult(BaseModel):
    """Resultado da validação criativa por IA."""
    overall: float = Field(ge=0, le=100)
    hook_score: float = Field(ge=0, le=100)
    clarity_score: float = Field(ge=0, le=100)
    product_visibility: float = Field(ge=0, le=100)
    demonstration_score: float = Field(ge=0, le=100)
    pacing_score: float = Field(ge=0, le=100)
    authenticity_score: float = Field(ge=0, le=100)
    cta_score: float = Field(ge=0, le=100)
    product_fidelity: float = Field(ge=0, le=100)

    reasons: list[str] = Field(description="Razões para os scores")
    problems: list[str] = Field(default_factory=list)
    suggested_fixes: list[str] = Field(default_factory=list)

    approved: bool


class VideoQualityResult(BaseModel):
    """Resultado completo do Quality Gate."""
    video_id: str
    creative_plan_id: str

    technical: TechnicalQAResult
    creative: CreativeQAResult

    overall_approved: bool
    can_publish: bool

    # Se reprovado, o que regenerar
    components_to_regenerate: list[str] = Field(default_factory=list)

    validated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PERFORMANCE — Métricas de criativos publicados
# =============================================================================

class CreativePerformance(BaseModel):
    """Métricas de performance de um criativo publicado."""
    video_id: str
    product_id: str
    creative_plan_id: str
    hook_id: str

    angle: CreativeAngle
    template: str | None = None
    duration_seconds: float
    voice_profile: str

    # Publicação
    platform: str = Field(default="tiktok")
    published_at: datetime | None = None
    external_url: str | None = None

    # Métricas de engajamento
    views: int = Field(default=0)
    likes: int = Field(default=0)
    comments: int = Field(default=0)
    shares: int = Field(default=0)
    saves: int = Field(default=0)

    # Métricas de conversão
    ctr: float | None = Field(default=None, description="Click-through rate")
    retention_2s: float | None = Field(default=None, description="% que assiste 2s+")

    # Métricas de venda (principal)
    orders: int = Field(default=0)
    units_sold: int = Field(default=0)
    gmv: float = Field(default=0.0, description="Gross Merchandise Value")
    commission: float = Field(default=0.0)

    # Custo
    generation_cost: float = Field(default=0.0)

    # Calculado
    @property
    def roas(self) -> float | None:
        """Return on Ad Spend."""
        if self.generation_cost > 0:
            return self.commission / self.generation_cost
        return None

    metrics_updated_at: datetime | None = None


# =============================================================================
# AI USAGE — Tracking de custos
# =============================================================================

class AIUsageRecord(BaseModel):
    """Registro de uso de IA para controle de custos."""
    id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model: str
    operation: str  # analyze_product, analyze_reference, plan, generate_image, etc.

    product_id: str | None = None
    creative_id: str | None = None

    # Tokens (para modelos de texto)
    tokens_input: int = Field(default=0)
    tokens_output: int = Field(default=0)

    # Imagens
    images_generated: int = Field(default=0)

    # Vídeo
    video_seconds: float = Field(default=0.0)

    # Áudio
    audio_characters: int = Field(default=0)

    # Custo
    estimated_cost_usd: float = Field(default=0.0)
    actual_cost_usd: float | None = Field(default=None)


# =============================================================================
# GENERATION JOB — Para operações assíncronas
# =============================================================================

class GenerationJobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class GenerationJobType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    SPEECH = "speech"
    ANALYSIS = "analysis"


class GenerationJob(BaseModel):
    """Job de geração assíncrona (para Sora, etc)."""
    id: str
    provider: str = Field(default="openai")
    provider_job_id: str | None = None

    type: GenerationJobType
    status: GenerationJobStatus = Field(default=GenerationJobStatus.QUEUED)

    # Input
    prompt: str | None = None
    input_image_path: str | None = None
    duration_seconds: float | None = None

    # Output
    output_path: str | None = None

    # Timing
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    # Error
    error: str | None = None
    retry_count: int = Field(default=0)
    max_retries: int = Field(default=2)
