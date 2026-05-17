from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import Product, Video, VideoCreativePack, VideoEvent, WeeklyWinner
from app.schemas import (
    WeeklyWinnerRequest, WeeklyWinnerOut, VideoOut, VideoDetailOut, CreativePackOut,
)
from app.agents.product_ranker import calculate_score
from app.agents.script_agent import generate_creative_packs
from app.agents.compliance_agent import check_compliance
from app.config import settings

router = APIRouter(tags=["videos"])


# === T04: Weekly Winner ===

@router.post("/weekly-winner", response_model=WeeklyWinnerOut)
def select_weekly_winner(req: WeeklyWinnerRequest, db: Session = Depends(get_db)):
    """Calcula scores e seleciona produto vencedor da semana."""
    products = db.query(Product).filter(Product.active == True).all()
    if not products:
        raise HTTPException(status_code=404, detail="Nenhum produto ativo")

    # Recalcular scores
    for p in products:
        p.total_score = calculate_score({
            "pain_score": p.pain_score, "visual_score": p.visual_score,
            "demo_score": p.demo_score, "impulse_buy_score": p.impulse_buy_score,
            "trend_score": p.trend_score, "availability_score": p.availability_score,
            "commission_estimate": float(p.commission_estimate or 0),
            "competition_score": p.competition_score,
        })

    db.flush()
    winner = max(products, key=lambda p: float(p.total_score))

    # Salvar vencedor
    ww = WeeklyWinner(
        week=req.week,
        product_id=winner.id,
        score=winner.total_score,
        reason=f"Maior score ({winner.total_score}) — destaque em visual e demonstração.",
    )
    db.add(ww)

    # Criar registro de vídeo
    video = Video(product_id=winner.id, week=req.week, status="pending_creative")
    db.add(video)
    db.flush()

    # Evento
    db.add(VideoEvent(video_id=video.id, event_type="product_ranked", actor="system",
                      details={"score": float(winner.total_score), "product_id": winner.id}))
    db.commit()

    return WeeklyWinnerOut(
        week=req.week, product=winner, score=float(winner.total_score), reason=ww.reason,
    )


# === T05: Generate Creative ===

@router.post("/videos/{video_id}/generate-creative", response_model=list[CreativePackOut])
async def generate_creative(video_id: int, prompt_id: int | None = None, db: Session = Depends(get_db)):
    """Gera 3 variações de roteiro via OpenAI. Aceita prompt_id para usar template customizado."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    product = db.query(Product).filter(Product.id == video.product_id).first()

    # Buscar template customizado se fornecido
    custom_prompt = None
    if prompt_id:
        from app.models import PromptTemplate
        custom_prompt = db.query(PromptTemplate).filter(
            PromptTemplate.id == prompt_id, PromptTemplate.active == True
        ).first()
        if not custom_prompt:
            raise HTTPException(status_code=404, detail="Prompt template não encontrado")

    packs = await generate_creative_packs(product, video, custom_prompt=custom_prompt)

    for i, pack in enumerate(packs, 1):
        cp = VideoCreativePack(
            video_id=video.id, version=i,
            hook=pack["hook"], script_json=pack["scenes"],
            caption=pack["caption"], hashtags=pack.get("hashtags", []),
            affiliate_disclaimer=pack.get("affiliate_disclaimer", ""),
            model_used=settings.openai_model,
            tokens_input=pack.get("tokens_input", 0),
            tokens_output=pack.get("tokens_output", 0),
            cost=pack.get("cost", 0),
        )
        db.add(cp)

    video.status = "creative_generated"
    if prompt_id:
        video.script_prompt_id = prompt_id
    db.add(VideoEvent(video_id=video.id, event_type="creative_generated", actor="system",
                      details={"variations": len(packs), "model": settings.openai_model, "prompt_id": prompt_id}))
    db.commit()

    return db.query(VideoCreativePack).filter(VideoCreativePack.video_id == video_id).all()


# === T06: Compliance Check ===

@router.post("/videos/{video_id}/compliance-check", response_model=list[CreativePackOut])
async def compliance_check(video_id: int, db: Session = Depends(get_db)):
    """Valida todos os creative packs de um vídeo."""
    packs = db.query(VideoCreativePack).filter(VideoCreativePack.video_id == video_id).all()
    if not packs:
        raise HTTPException(status_code=404, detail="Nenhum creative pack encontrado")

    for pack in packs:
        result = await check_compliance(pack)
        pack.compliance_status = result["status"]
        pack.compliance_notes = result.get("notes", "")
        if result.get("fixed_scenes"):
            pack.script_json = result["fixed_scenes"]

    video = db.query(Video).filter(Video.id == video_id).first()
    video.status = "compliance_done"
    db.add(VideoEvent(video_id=video_id, event_type="compliance_checked", actor="system"))
    db.commit()

    return packs


# === T07: Select Pack (aprovação humana) ===

@router.post("/videos/{video_id}/select-pack")
def select_pack(video_id: int, pack_id: int, db: Session = Depends(get_db)):
    """Humano seleciona qual creative pack usar."""
    pack = db.query(VideoCreativePack).filter(
        VideoCreativePack.id == pack_id, VideoCreativePack.video_id == video_id
    ).first()
    if not pack:
        raise HTTPException(status_code=404, detail="Pack não encontrado")

    # Desmarcar outros
    db.query(VideoCreativePack).filter(
        VideoCreativePack.video_id == video_id
    ).update({"selected": False})

    pack.selected = True
    video = db.query(Video).filter(Video.id == video_id).first()
    video.selected_creative_pack_id = pack_id
    video.status = "human_selected"

    db.add(VideoEvent(video_id=video_id, event_type="human_selected_pack", actor="human",
                      details={"pack_id": pack_id, "version": pack.version}))
    db.commit()

    return {"status": "ok", "selected_pack_id": pack_id}


# === T08: Generate TTS ===

@router.post("/videos/{video_id}/generate-tts")
async def generate_tts(video_id: int, db: Session = Depends(get_db)):
    """Gera áudio da narração via OpenAI TTS."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or not video.selected_creative_pack_id:
        raise HTTPException(status_code=400, detail="Selecione um creative pack primeiro")

    pack = db.query(VideoCreativePack).filter(
        VideoCreativePack.id == video.selected_creative_pack_id
    ).first()

    # Concatenar voiceover de todas as cenas
    scenes = pack.script_json or []
    full_text = " ".join(scene.get("voiceover", "") for scene in scenes)

    if not full_text.strip():
        raise HTTPException(status_code=400, detail="Nenhum texto de narração nas cenas")

    # Chamar TTS service
    output_dir = f"/output/{video.week}/{video.product_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.post("http://tts-service:8001/generate", json={
            "text": full_text,
            "output_dir": output_dir,
            "filename": f"voiceover-v{pack.version}.mp3",
        }, timeout=60)

    if resp.status_code != 200:
        raise HTTPException(status_code=500, detail="Erro ao gerar TTS")

    result = resp.json()
    video.voiceover_path = result["audio_path"]
    video.status = "tts_generated"
    video.total_cost = float(video.total_cost or 0) + (len(full_text) * 0.000015)  # ~$15/1M chars

    db.add(VideoEvent(video_id=video_id, event_type="tts_generated", actor="system",
                      details={"characters": len(full_text), "path": result["audio_path"]}))
    db.commit()

    return {"status": "ok", "audio_path": result["audio_path"], "characters": len(full_text)}


# === T09: Generate Prompts (Seedance/Runway) ===

@router.post("/videos/{video_id}/generate-prompts")
def generate_prompts(video_id: int, renderer: str = "seedance", prompt_id: int | None = None, db: Session = Depends(get_db)):
    """Gera prompts otimizados para o renderer escolhido. Aceita prompt_id para template customizado."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video or not video.selected_creative_pack_id:
        raise HTTPException(status_code=400, detail="Selecione um creative pack primeiro")

    pack = db.query(VideoCreativePack).filter(
        VideoCreativePack.id == video.selected_creative_pack_id
    ).first()
    product = db.query(Product).filter(Product.id == video.product_id).first()

    # Buscar template customizado se fornecido
    custom_template = None
    if prompt_id:
        from app.models import PromptTemplate
        custom_template = db.query(PromptTemplate).filter(
            PromptTemplate.id == prompt_id, PromptTemplate.active == True
        ).first()
        if not custom_template:
            raise HTTPException(status_code=404, detail="Prompt template não encontrado")

    scenes = pack.script_json or []
    prompts = []

    for scene in scenes:
        if custom_template:
            # Substituir variáveis no template
            prompt = custom_template.content.replace(
                "{{visual}}", scene.get("visual", "")
            ).replace(
                "{{product_name}}", product.name
            ).replace(
                "{{category}}", product.category
            )
        elif renderer == "seedance":
            prompt = (
                f"{scene.get('visual', '')}. "
                f"Vertical 9:16, realistic product video, {product.category.lower()}, "
                f"clean background, natural lighting, TikTok style."
            )
        elif renderer == "runway":
            prompt = (
                f"{scene.get('visual', '')}. "
                f"Cinematic vertical shot, product demonstration, "
                f"smooth camera movement, 4K quality."
            )
        else:
            prompt = scene.get("visual", "")

        prompts.append({
            "scene": scene.get("start", 0),
            "duration": (scene.get("end", 0) - scene.get("start", 0)),
            "prompt": prompt,
            "text_overlay": scene.get("text", ""),
        })

    video.renderer = renderer
    video.status = "prompts_ready"
    if prompt_id:
        video.renderer_prompt_id = prompt_id
    db.add(VideoEvent(video_id=video_id, event_type="prompts_generated", actor="system",
                      details={"renderer": renderer, "scenes": len(prompts), "prompt_id": prompt_id}))
    db.commit()

    return {
        "video_id": video_id,
        "renderer": renderer,
        "product": product.name,
        "hook": pack.hook,
        "caption": pack.caption,
        "hashtags": pack.hashtags,
        "prompts": prompts,
        "voiceover_path": video.voiceover_path,
    }


# === T10: List/Detail Videos ===

@router.get("/videos", response_model=list[VideoOut])
def list_videos(week: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    """Lista vídeos com filtros opcionais."""
    query = db.query(Video)
    if week:
        query = query.filter(Video.week == week)
    if status:
        query = query.filter(Video.status == status)
    return query.order_by(Video.created_at.desc()).all()


@router.get("/videos/{video_id}", response_model=VideoDetailOut)
def get_video(video_id: int, db: Session = Depends(get_db)):
    """Detalhe completo de um vídeo com creative packs e eventos."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    return video
