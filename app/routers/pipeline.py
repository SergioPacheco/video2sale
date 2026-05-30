"""Pipeline v2 — produto → vídeo MP4 em 1 chamada.

Sem Remotion. Sem serviços separados. Tudo inline com ffmpeg.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Video, VideoCreativePack, VideoEvent, PromptTemplate
from app.agents.product_ranker import calculate_score
from app.agents.script_agent import generate_creative_packs
from app.agents.compliance_agent import check_compliance
from app.tts import generate_voiceover
from app.renderer import render_video
from app.config import settings

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/full")
async def run_full_pipeline(
    product_id: int | None = None,
    week: str | None = None,
    db: Session = Depends(get_db),
):
    """Pipeline completo: produto → vídeo MP4 renderizado.

    1. Seleciona produto (ou usa o fornecido)
    2. Gera 3 roteiros via OpenAI
    3. Compliance check
    4. Seleciona melhor roteiro
    5. Gera narração TTS
    6. Renderiza vídeo com ffmpeg (Ken Burns + texto + áudio)

    Retorna path do vídeo ou erro com o step que falhou.
    """
    if not week:
        now = datetime.now()
        week = f"{now.year}-W{now.isocalendar()[1]:02d}"

    steps = []
    video = None

    try:
        # === 1. Produto ===
        if product_id:
            product = db.query(Product).filter(Product.id == product_id, Product.active == True).first()
            if not product:
                raise HTTPException(status_code=404, detail="Produto não encontrado ou inativo")
        else:
            products = db.query(Product).filter(Product.active == True).all()
            if not products:
                raise HTTPException(status_code=404, detail="Nenhum produto ativo")
            for p in products:
                p.total_score = calculate_score({
                    "pain_score": p.pain_score, "visual_score": p.visual_score,
                    "demo_score": p.demo_score, "impulse_buy_score": p.impulse_buy_score,
                    "trend_score": p.trend_score, "availability_score": p.availability_score,
                    "commission_estimate": float(p.commission_estimate or 0),
                    "competition_score": p.competition_score,
                })
            db.flush()
            product = max(products, key=lambda p: float(p.total_score or 0))

        steps.append({"step": "product", "id": product.id, "name": product.name})

        # === 2. Criar registro de vídeo ===
        video = Video(product_id=product.id, week=week, status="pending_creative")
        db.add(video)
        db.flush()

        # === 3. Gerar roteiros ===
        prompt_tpl = db.query(PromptTemplate).filter(
            PromptTemplate.type == "script_agent", PromptTemplate.active == True
        ).first()

        packs_data = await generate_creative_packs(product, video, custom_prompt=prompt_tpl)

        packs = []
        for i, pd in enumerate(packs_data, 1):
            cp = VideoCreativePack(
                video_id=video.id, version=i,
                hook=pd.get("hook") or "",
                script_json=pd.get("scenes") or [],
                caption=pd.get("caption") or "",
                hashtags=pd.get("hashtags", []),
                affiliate_disclaimer=pd.get("affiliate_disclaimer") or "",
                model_used=settings.openai_model,
                tokens_input=pd.get("tokens_input", 0),
                tokens_output=pd.get("tokens_output", 0),
                cost=pd.get("cost", 0),
            )
            db.add(cp)
            packs.append(cp)

        video.status = "creative_generated"
        db.flush()
        steps.append({"step": "roteiro", "packs": len(packs)})

        # === 4. Compliance ===
        compliance_tpl = db.query(PromptTemplate).filter(
            PromptTemplate.type == "compliance", PromptTemplate.active == True
        ).first()

        for pack in packs:
            result = await check_compliance(pack, custom_prompt=compliance_tpl)
            pack.compliance_status = result["status"]
            pack.compliance_notes = result.get("notes", "")

        video.status = "compliance_done"
        db.flush()
        steps.append({"step": "compliance"})

        # === 5. Selecionar melhor pack ===
        approved = [p for p in packs if p.compliance_status in ("APROBADO", "approved", "AJUSTAR", "adjusted")]
        best = next((p for p in (approved or packs) if p.compliance_status in ("APROBADO", "approved")), (approved or packs)[0])

        best.selected = True
        video.selected_creative_pack_id = best.id
        video.status = "human_selected"
        db.flush()
        steps.append({"step": "pack_selected", "version": best.version, "hook": (best.hook or "")[:60]})

        # === 6. TTS ===
        scenes = best.script_json or []
        full_text = " ".join(
            s.get("voiceover", "") if isinstance(s, dict) else str(s)
            for s in scenes
        ).strip()

        voiceover_path = None
        tts_cost = 0
        if full_text:
            tts_result = generate_voiceover(full_text, week, product.id)
            voiceover_path = tts_result["audio_path"]
            tts_cost = tts_result["cost"]
            video.voiceover_path = voiceover_path
            video.status = "tts_generated"
            db.flush()
            steps.append({"step": "tts", "characters": len(full_text)})
        else:
            steps.append({"step": "tts_skipped"})

        # === 7. Buscar imagens se produto não tiver ===
        assets = product.assets or []
        image_urls = [a.get("url") for a in assets if a.get("type") in ("image", "photo", "producto", "lifestyle") and a.get("url")]

        if not image_urls and product.image_url:
            image_urls = [product.image_url]

        if not image_urls:
            from app.agents.image_fetcher import fetch_images_for_product
            fetched = await fetch_images_for_product(
                product_name=product.name,
                category=product.category or "",
                product_url=product.product_url or "",
                limit=5,
            )
            if fetched:
                product.assets = (product.assets or []) + fetched
                db.flush()
                image_urls = [img["url"] for img in fetched]
                steps.append({"step": "images_fetched", "count": len(image_urls)})

        # === 8. Render (ffmpeg) ===
            scenes=scenes,
            voiceover_path=voiceover_path,
            image_urls=image_urls,
            product_name=product.name,
            week=week,
            product_id=product.id,
        )

        video.video_path = render_result.video_path
        video.thumbnail_path = render_result.thumbnail_path
        video.renderer = "ffmpeg"
        video.status = "rendered"
        video.total_cost = float(video.total_cost or 0) + tts_cost + sum(p.cost or 0 for p in packs)

        db.add(VideoEvent(video_id=video.id, event_type="video_rendered", actor="system",
                          details={"renderer": "ffmpeg", "duration": render_result.duration,
                                   "scenes": render_result.scenes_count, "images": len(image_urls)}))
        db.commit()

        steps.append({
            "step": "rendered",
            "video_path": render_result.video_path,
            "duration": render_result.duration,
            "scenes": render_result.scenes_count,
        })

        return {
            "status": "ok",
            "video_id": video.id,
            "product": {"id": product.id, "name": product.name},
            "week": week,
            "video_path": render_result.video_path,
            "thumbnail_path": render_result.thumbnail_path,
            "duration": render_result.duration,
            "total_cost": float(video.total_cost or 0),
            "steps": steps,
        }

    except HTTPException:
        raise
    except Exception as e:
        if video:
            video.status = "error"
            db.add(VideoEvent(video_id=video.id, event_type="error", actor="system",
                              details={"error": str(e), "steps": steps}))
            db.commit()
        steps.append({"step": "error", "error": str(e)})
        raise HTTPException(status_code=500, detail={
            "message": f"Pipeline falhou: {str(e)}",
            "steps": steps,
            "video_id": video.id if video else None,
        })


@router.post("/batch")
async def run_batch(
    count: int = 3,
    week: str | None = None,
    db: Session = Depends(get_db),
):
    """Gera N vídeos para os top N produtos."""
    if not week:
        now = datetime.now()
        week = f"{now.year}-W{now.isocalendar()[1]:02d}"

    products = db.query(Product).filter(Product.active == True).order_by(Product.total_score.desc()).limit(count).all()
    if not products:
        raise HTTPException(status_code=404, detail="Nenhum produto ativo")

    results = []
    for product in products:
        try:
            r = await run_full_pipeline(product_id=product.id, week=week, db=db)
            results.append(r)
        except Exception as e:
            results.append({"status": "error", "product_id": product.id, "error": str(e)})

    return {
        "week": week,
        "requested": count,
        "completed": sum(1 for r in results if r.get("status") == "ok"),
        "total_cost": sum(r.get("total_cost", 0) for r in results),
        "results": results,
    }
