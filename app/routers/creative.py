"""Creative Pipeline Router — Endpoints para Creative Intelligence Engine.

Endpoints:
- POST /creative/analyze-product/{id} — Analisa produto e gera ProductProfile
- POST /creative/analyze-reference — Analisa vídeo de referência
- POST /creative/plan/{product_id} — Gera CreativePlans
- POST /creative/generate/{plan_id} — Gera vídeo a partir de plan
- GET /creative/plans/{product_id} — Lista plans de um produto
"""

from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel
import shutil
import tempfile
from pathlib import Path

from app.database import get_db
from app.models import Product, Asset, Video, VideoCreativePack, VideoEvent
from app.creative import (
    get_product_analyzer,
    get_competitor_analyzer,
    get_creative_planner,
    get_fidelity_validator,
    get_quality_gate,
    ProductProfile,
    CreativeDNA,
    CreativePlan,
    CreativeAngle,
)
from app.openai.speech import get_speech_service
from app.renderer import render_video

router = APIRouter(prefix="/creative", tags=["creative"])


# =============================================================================
# SCHEMAS DE REQUEST/RESPONSE
# =============================================================================

class AnalyzeProductResponse(BaseModel):
    product_id: int
    profile: ProductProfile
    suggested_hooks: list[dict]


class AnalyzeReferenceResponse(BaseModel):
    reference_id: str
    dna: CreativeDNA
    key_insights: list[str]


class GeneratePlansRequest(BaseModel):
    angles: list[CreativeAngle] | None = None
    count: int = 5
    target_duration_ms: int = 16000
    language: str = "pt-BR"
    reference_ids: list[str] | None = None


class GeneratePlansResponse(BaseModel):
    product_id: int
    plans: list[CreativePlan]
    reference_insights_used: list[str]


class GenerateVideoRequest(BaseModel):
    plan: CreativePlan
    voice: str = "nova"


class GenerateVideoResponse(BaseModel):
    video_id: int
    video_path: str
    thumbnail_path: str | None
    duration_seconds: float
    quality_passed: bool
    quality_score: float
    cost: float


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/analyze-product/{product_id}", response_model=AnalyzeProductResponse)
async def analyze_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Analisa produto e gera ProductProfile completo.

    Usa OpenAI Vision para analisar fotos e descobrir:
    - Problemas que resolve
    - Desejos relacionados
    - Benefícios demonstráveis
    - Claims permitidos e proibidos
    - Características visuais para fidelidade
    """
    # Buscar produto
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Buscar imagens
    assets = db.query(Asset).filter(
        Asset.product_id == product_id,
        Asset.active == True,
        Asset.type.in_(["image", "photo", "lifestyle"])
    ).all()

    image_urls = [a.url for a in assets if a.url]
    if not image_urls and product.image_url:
        image_urls = [product.image_url]

    if not image_urls:
        raise HTTPException(status_code=400, detail="Produto sem imagens para análise")

    # Analisar
    analyzer = get_product_analyzer()
    profile = await analyzer.analyze(product, image_urls)

    # Gerar sugestões de hooks
    hooks = await analyzer.get_selling_hooks(profile, count=5)

    return AnalyzeProductResponse(
        product_id=product_id,
        profile=profile,
        suggested_hooks=hooks,
    )


@router.post("/analyze-reference", response_model=AnalyzeReferenceResponse)
async def analyze_reference(
    video: UploadFile = File(...),
    source_url: str | None = Form(None),
    language: str = Form("es"),
):
    """Analisa vídeo de referência e extrai CreativeDNA.

    Upload um vídeo vencedor para extrair:
    - Estrutura do hook
    - Estrutura narrativa
    - Técnicas usadas
    - Pacing e ritmo
    - Por que funciona
    """
    # Salvar arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
        shutil.copyfileobj(video.file, tmp)
        tmp_path = tmp.name

    try:
        analyzer = get_competitor_analyzer()
        dna = await analyzer.analyze(
            video_path=tmp_path,
            source_url=source_url,
            language=language,
        )

        return AnalyzeReferenceResponse(
            reference_id=dna.reference_id,
            dna=dna,
            key_insights=dna.reasons_it_works[:5],
        )

    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.post("/plan/{product_id}", response_model=GeneratePlansResponse)
async def generate_plans(
    product_id: int,
    request: GeneratePlansRequest,
    db: Session = Depends(get_db),
):
    """Gera múltiplos CreativePlans para um produto.

    Combina ProductProfile com insights de referências para criar
    5 conceitos diferentes (problem_solution, travel_desire, etc).
    """
    # Buscar produto
    product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Analisar produto primeiro (usa cache se já analisado)
    analyzer = get_product_analyzer()
    assets = db.query(Asset).filter(
        Asset.product_id == product_id,
        Asset.active == True,
        Asset.type.in_(["image", "photo", "lifestyle"])
    ).all()
    image_urls = [a.url for a in assets if a.url] or ([product.image_url] if product.image_url else [])

    if not image_urls:
        raise HTTPException(status_code=400, detail="Produto sem imagens")

    profile = await analyzer.analyze(product, image_urls)

    # TODO: Buscar referências do banco se reference_ids fornecidos
    references = []
    patterns = None

    # Gerar planos
    planner = get_creative_planner()
    plans = await planner.plan(
        product=profile,
        references=references,
        patterns=patterns,
        angles=request.angles,
        count=request.count,
        target_duration_ms=request.target_duration_ms,
        language=request.language,
    )

    return GeneratePlansResponse(
        product_id=product_id,
        plans=plans,
        reference_insights_used=[],
    )


@router.post("/generate")
async def generate_video(
    request: GenerateVideoRequest,
    db: Session = Depends(get_db),
):
    """Gera vídeo MP4 a partir de um CreativePlan.

    Pipeline:
    1. Gerar TTS da narração
    2. Buscar/gerar assets
    3. Renderizar com FFmpeg
    4. Quality Gate
    5. Retornar resultado
    """
    plan = request.plan

    # Buscar produto
    product = db.query(Product).filter(Product.id == int(plan.product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    # Criar registro de vídeo
    week = f"{datetime.now().year}-W{datetime.now().isocalendar()[1]:02d}"
    video = Video(
        product_id=product.id,
        week=week,
        status="generating",
    )
    db.add(video)
    db.flush()

    try:
        # 1. Gerar TTS
        speech = get_speech_service()
        output_dir = Path(f"/output/{week}/{product.id}")
        output_dir.mkdir(parents=True, exist_ok=True)

        tts_result = await speech.generate(
            text=plan.full_narration,
            output_path=str(output_dir / "voiceover.mp3"),
            voice=request.voice,
        )
        voiceover_path = tts_result.get("audio_path")
        tts_cost = tts_result.get("cost", 0)

        # 2. Buscar imagens do produto
        assets = db.query(Asset).filter(
            Asset.product_id == product.id,
            Asset.active == True,
        ).all()
        image_urls = [a.url for a in assets if a.type in ("image", "photo", "lifestyle") and a.url]
        if not image_urls and product.image_url:
            image_urls = [product.image_url]

        # 3. Converter scenes para formato do renderer
        scenes = []
        for scene in plan.scenes:
            scenes.append({
                "start": scene.start_ms / 1000,
                "end": scene.end_ms / 1000,
                "text": scene.text_overlay or "",
                "voiceover": scene.narration or "",
                "visual": scene.visual_description,
            })

        # 4. Renderizar
        render_result = render_video(
            scenes=scenes,
            voiceover_path=voiceover_path,
            image_urls=image_urls,
            product_name=product.name,
            week=week,
            product_id=product.id,
        )

        # 5. Quality Gate
        gate = get_quality_gate()
        quality_result = await gate.validate(
            video_path=render_result.video_path,
            creative_plan=plan,
        )

        # Atualizar vídeo
        video.video_path = render_result.video_path
        video.thumbnail_path = render_result.thumbnail_path
        video.voiceover_path = voiceover_path
        video.status = "rendered" if quality_result.overall_approved else "quality_failed"
        video.total_cost = tts_cost

        # Salvar creative pack
        pack = VideoCreativePack(
            video_id=video.id,
            version=1,
            hook=plan.hook.text,
            script_json=plan.model_dump(),
            caption="",
            hashtags=[],
            compliance_status="pending",
            selected=True,
        )
        db.add(pack)

        # Registrar evento
        db.add(VideoEvent(
            video_id=video.id,
            event_type="creative_generated",
            actor="creative_pipeline",
            details={
                "plan_id": plan.id,
                "angle": plan.angle.value,
                "quality_passed": quality_result.overall_approved,
                "quality_score": quality_result.creative.overall if quality_result.creative else 0,
            },
        ))

        db.commit()

        return {
            "video_id": video.id,
            "video_path": render_result.video_path,
            "thumbnail_path": render_result.thumbnail_path,
            "duration_seconds": render_result.duration,
            "quality_passed": quality_result.overall_approved,
            "quality_score": quality_result.creative.overall if quality_result.creative else 0,
            "quality_details": quality_result.model_dump() if quality_result else None,
            "cost": tts_cost,
        }

    except Exception as e:
        video.status = "error"
        db.add(VideoEvent(
            video_id=video.id,
            event_type="error",
            actor="creative_pipeline",
            details={"error": str(e)},
        ))
        db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/profiles/{product_id}")
async def get_product_profile(
    product_id: int,
    db: Session = Depends(get_db),
):
    """Retorna ProductProfile em cache se existir."""
    from app.creative.product_analyzer import ANALYSIS_CACHE_DIR
    import json

    # Buscar no cache
    cache_files = list(ANALYSIS_CACHE_DIR.glob("*.json"))

    for cache_file in cache_files:
        try:
            data = json.loads(cache_file.read_text())
            if data.get("product_id") == str(product_id):
                return ProductProfile.model_validate(data)
        except Exception:
            continue

    raise HTTPException(status_code=404, detail="Profile não encontrado. Execute /analyze-product primeiro.")


@router.get("/health")
async def creative_health():
    """Health check do Creative Intelligence Engine."""
    return {
        "status": "ok",
        "service": "creative-intelligence-engine",
        "components": [
            "product_analyzer",
            "reference_analyzer",
            "creative_planner",
            "fidelity_validator",
            "quality_gate",
        ],
    }
