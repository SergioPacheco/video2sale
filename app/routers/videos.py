from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import Product, Video, VideoCreativePack, VideoEvent, WeeklyWinner, Asset
from app.schemas import (
    WeeklyWinnerRequest, WeeklyWinnerOut, VideoOut, VideoDetailOut, CreativePackOut,
)
from app.agents.product_ranker import calculate_score
from app.agents.script_agent import generate_creative_packs
from app.agents.compliance_agent import check_compliance
from app.config import settings

router = APIRouter(tags=["videos"])


# === T04: Weekly Winner ===

@router.post("/videos", response_model=VideoOut)
def create_video(product_id: int, week: str, db: Session = Depends(get_db)):
    """Cria um vídeo para um produto selecionado manualmente."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    video = Video(product_id=product_id, week=week, status="pending_creative")
    db.add(video)
    db.flush()
    db.add(VideoEvent(video_id=video.id, event_type="product_ranked", actor="human",
                      details={"product_id": product_id, "score": float(product.total_score or 0)}))
    db.commit()
    db.refresh(video)
    return video


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

    # Buscar template: se prompt_id fornecido usa esse, senão busca o primeiro script_agent ativo
    from app.models import PromptTemplate
    custom_prompt = None
    if prompt_id:
        custom_prompt = db.query(PromptTemplate).filter(
            PromptTemplate.id == prompt_id, PromptTemplate.active == True
        ).first()
        if not custom_prompt:
            raise HTTPException(status_code=404, detail="Prompt template não encontrado")
    else:
        custom_prompt = db.query(PromptTemplate).filter(
            PromptTemplate.type == "script_agent", PromptTemplate.active == True
        ).first()

    packs = await generate_creative_packs(product, video, custom_prompt=custom_prompt)

    for i, pack in enumerate(packs, 1):
        cp = VideoCreativePack(
            video_id=video.id, version=i,
            hook=pack.get("hook") or pack.get("gancho") or "",
            script_json=pack.get("scenes") or pack.get("script_json") or pack.get("escenas") or [],
            caption=pack.get("caption") or pack.get("descripcion") or "",
            hashtags=pack.get("hashtags", []),
            affiliate_disclaimer=pack.get("affiliate_disclaimer") or pack.get("aviso_afiliado") or "",
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

    # Buscar prompt de compliance do banco
    from app.models import PromptTemplate
    compliance_prompt = db.query(PromptTemplate).filter(
        PromptTemplate.type == "compliance", PromptTemplate.active == True
    ).first()

    for pack in packs:
        result = await check_compliance(pack, custom_prompt=compliance_prompt)
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
    full_text = ""
    for scene in scenes:
        if isinstance(scene, dict):
            full_text += " " + scene.get("voiceover", "")
        elif isinstance(scene, str):
            full_text += " " + scene
    full_text = full_text.strip()

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


# === T09: Generate Prompts (video handoff) ===

@router.post("/videos/{video_id}/generate-prompts")
def generate_prompts(video_id: int, prompt_id: int | None = None, db: Session = Depends(get_db)):
    """Gera prompts de vídeo genéricos para handoff local. Aceita prompt_id para template customizado."""
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
        else:
            prompt = (
                f"{scene.get('visual', '')}. "
                f"Vertical 9:16, realistic product video, {product.category.lower()}, "
                f"clean background, natural lighting, TikTok style."
            )

        prompts.append({
            "scene": scene.get("start", 0),
            "duration": (scene.get("end", 0) - scene.get("start", 0)),
            "prompt": prompt,
            "text_overlay": scene.get("text", ""),
        })

    video.renderer = "ffmpeg"
    video.status = "prompts_ready"
    if prompt_id:
        video.renderer_prompt_id = prompt_id
    db.add(VideoEvent(video_id=video_id, event_type="prompts_generated", actor="system",
                      details={"renderer": "ffmpeg", "scenes": len(prompts), "prompt_id": prompt_id}))
    db.commit()

    return {
        "video_id": video_id,
        "renderer": "ffmpeg",
        "product": product.name,
        "hook": pack.hook,
        "caption": pack.caption,
        "hashtags": pack.hashtags,
        "prompts": prompts,
        "voiceover_path": video.voiceover_path,
    }



# === Download Pack ===

@router.get("/videos/{video_id}/download-pack")
def download_pack(video_id: int, db: Session = Depends(get_db)):
    """Gera ZIP com roteiro, caption, hashtags e links de assets."""
    import zipfile, io, json as json_lib
    from fastapi.responses import StreamingResponse

    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    pack = db.query(VideoCreativePack).filter(
        VideoCreativePack.id == video.selected_creative_pack_id
    ).first()
    if not pack:
        raise HTTPException(status_code=400, detail="Nenhum roteiro selecionado")

    product = db.query(Product).filter(Product.id == video.product_id).first()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        roteiro = {
            "product": product.name, "category": product.category,
            "hook": pack.hook, "scenes": pack.script_json,
            "caption": pack.caption, "hashtags": pack.hashtags,
            "affiliate_disclaimer": pack.affiliate_disclaimer,
        }
        zf.writestr("roteiro.json", json_lib.dumps(roteiro, ensure_ascii=False, indent=2))

        txt = f"PRODUCTO: {product.name}\nCATEGORÍA: {product.category}\n\nGANCHO: {pack.hook}\n\nESCENAS:\n"
        for i, scene in enumerate(pack.script_json or [], 1):
            if isinstance(scene, dict):
                txt += f"\n  Escena {i} ({scene.get('start',0)}s - {scene.get('end',0)}s)\n"
                txt += f"    Texto: {scene.get('text','')}\n"
                txt += f"    Narración: {scene.get('voiceover','')}\n"
                txt += f"    Visual: {scene.get('visual','')}\n"
        txt += f"\nCAPTION: {pack.caption}\nHASHTAGS: {' '.join(pack.hashtags or [])}\n"
        zf.writestr("roteiro.txt", txt)

        asset_rows = db.query(Asset).filter(
            Asset.product_id == product.id,
            Asset.active == True,
        ).order_by(Asset.id.asc()).all()
        if asset_rows:
            assets_txt = "MATERIALES DEL PRODUCTO\n\n"
            for asset in asset_rows:
                assets_txt += f"[{asset.type}] {asset.label or ''}\n  {asset.url}\n\n"
            zf.writestr("assets.txt", assets_txt)

    buffer.seek(0)
    filename = f"pack-{product.name[:20].replace(' ','-')}-{video.week}.zip"
    return StreamingResponse(buffer, media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'})

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


# === T11: Publish ===

@router.post("/videos/{video_id}/publish")
def publish_video(video_id: int, platform: str = "tiktok", tiktok_url: str | None = None, db: Session = Depends(get_db)):
    """Marca vídeo como publicado. Salva tiktok_url para cruzamento com Sort Feed."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    video.status = "published"
    db.add(VideoEvent(
        video_id=video_id, event_type="published", actor="human",
        details={"platform": platform, "tiktok_url": tiktok_url},
    ))
    db.commit()

    return {"status": "ok", "video_id": video_id, "tiktok_url": tiktok_url}
