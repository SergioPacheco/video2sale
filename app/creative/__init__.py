"""Creative Intelligence Engine.

Módulo principal para análise de produtos, referências e geração de planos criativos.
"""

from app.creative.schemas import (
    # Enums
    HookType,
    CreativeAngle,
    SceneGenerationMode,
    ScenePurpose,
    PacingLevel,
    ComplianceStatus,
    GenerationJobStatus,
    GenerationJobType,
    # Product
    VisualCharacteristics,
    ProductProfile,
    # Reference
    HookAnalysis,
    ReferenceScene,
    CreativeDNA,
    WinningPatterns,
    # Planning
    Hook,
    ScenePlan,
    CaptionPlan,
    CreativePlan,
    # Quality
    ProductFidelityResult,
    TechnicalQAResult,
    CreativeQAResult,
    VideoQualityResult,
    # Performance
    CreativePerformance,
    # Tracking
    AIUsageRecord,
    GenerationJob,
)

# Services
from app.creative.product_analyzer import ProductAnalyzer, get_product_analyzer
from app.creative.reference_analyzer import CompetitorVideoAnalyzer, get_competitor_analyzer
from app.creative.planner import CreativePlanner, get_creative_planner
from app.creative.fidelity_validator import ProductFidelityValidator, get_fidelity_validator
from app.creative.quality_gate import VideoQualityGate, get_quality_gate

__all__ = [
    # Enums
    "HookType",
    "CreativeAngle",
    "SceneGenerationMode",
    "ScenePurpose",
    "PacingLevel",
    "ComplianceStatus",
    "GenerationJobStatus",
    "GenerationJobType",
    # Product
    "VisualCharacteristics",
    "ProductProfile",
    # Reference
    "HookAnalysis",
    "ReferenceScene",
    "CreativeDNA",
    "WinningPatterns",
    # Planning
    "Hook",
    "ScenePlan",
    "CaptionPlan",
    "CreativePlan",
    # Quality
    "ProductFidelityResult",
    "TechnicalQAResult",
    "CreativeQAResult",
    "VideoQualityResult",
    # Performance
    "CreativePerformance",
    # Tracking
    "AIUsageRecord",
    "GenerationJob",
    # Services
    "ProductAnalyzer",
    "get_product_analyzer",
    "CompetitorVideoAnalyzer",
    "get_competitor_analyzer",
    "CreativePlanner",
    "get_creative_planner",
    "ProductFidelityValidator",
    "get_fidelity_validator",
    "VideoQualityGate",
    "get_quality_gate",
]
