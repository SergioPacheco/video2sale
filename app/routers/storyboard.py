"""Storyboard local - handoff simples de prompts e materiais."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
from pathlib import Path

from app.database import get_db
from app.models import Video, VideoCreativePack, Product, Asset, VideoEvent

router = APIRouter(prefix="/storyboard", tags=["storyboard"])

OUTPUT_BASE = Path("/output")


@router.post("/generate/{video_id}")
async def generate_storyboard(video_id: int, db: Session = Depends(get_db)):
    """Gera um handoff local em MD e JSON com assets e prompts por cena."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    pack = None
    if video.selected_creative_pack_id:
        pack = db.query(VideoCreativePack).filter(VideoCreativePack.id == video.selected_creative_pack_id).first()
    if not pack:
        packs = db.query(VideoCreativePack).filter(VideoCreativePack.video_id == video_id).all()
        pack = packs[0] if packs else None
    if not pack:
        raise HTTPException(status_code=400, detail="Nenhum roteiro gerado. Execute o pipeline primeiro.")

    product = db.query(Product).filter(Product.id == video.product_id).first()
    assets = db.query(Asset).filter(Asset.product_id == product.id, Asset.active == True).all()
    image_urls = [a.url for a in assets if a.type in ("image", "lifestyle", "detail") and a.url]
    if not image_urls and product.image_url:
        image_urls = [product.image_url]

    storyboard_dir = OUTPUT_BASE / video.week / str(product.id) / "storyboard"
    storyboard_dir.mkdir(parents=True, exist_ok=True)

    scenes = pack.script_json or []
    video_prompts = []
    md_lines = [
        f"# Storyboard - {product.name}",
        "",
        f"Produto: {product.name}",
        f"Categoria: {product.category}",
        f"Semana: {video.week}",
        f"Hook: {pack.hook}",
        f"Caption: {pack.caption}",
        f"Hashtags: {' '.join(pack.hashtags or [])}",
        "",
        "Assets:",
    ]

    for i, url in enumerate(image_urls[:9], 1):
        md_lines.append(f"- IMG{i}: {url}")

    md_lines.extend(["", "Cenas:"])

    for i, scene in enumerate(scenes):
        start = scene.get("start", i * 5)
        end = scene.get("end", start + 5)
        text = scene.get("text", "")
        voiceover = scene.get("voiceover", "")
        visual = scene.get("visual", "")
        prompt = (
            "Realistic product video, clean background, natural lighting, "
            f"smooth camera movement, vertical 9:16. {start}-{end}s: {visual}."
        )
        video_prompts.append({
            "scene": i + 1,
            "start": start,
            "end": end,
            "prompt": prompt,
            "text_overlay": text,
            "voiceover": voiceover,
            "image_ref": image_urls[i] if i < len(image_urls) else None,
        })
        md_lines.extend([
            f"- Cena {i + 1}: {start}-{end}s",
            f"  - Visual: {visual}",
            f"  - Voiceover: {voiceover}",
            f"  - Texto: {text}",
            f"  - Prompt: {prompt}",
        ])

    md_lines.extend([
        "",
        f"Caption: {pack.caption}",
        f"Affiliate disclaimer: {pack.affiliate_disclaimer or ''}",
    ])

    storyboard_md = "\n".join(md_lines)
    full_prompt = "\n".join(item["prompt"] for item in video_prompts)

    md_path = str(storyboard_dir / "storyboard.md")
    with open(md_path, "w") as f:
        f.write(storyboard_md)

    prompts_path = str(storyboard_dir / "prompts.json")
    with open(prompts_path, "w") as f:
        json.dump({
            "product": product.name,
            "full_prompt": full_prompt,
            "scenes": video_prompts,
            "caption": pack.caption,
            "hashtags": pack.hashtags,
            "images": image_urls[:9],
        }, f, ensure_ascii=False, indent=2)

    db.add(VideoEvent(video_id=video_id, event_type="storyboard_generated", actor="system",
                      details={"scenes": len(scenes), "images": len(image_urls)}))
    db.commit()

    return {
        "status": "ok",
        "video_id": video_id,
        "product": product.name,
        "scenes": len(scenes),
        "images": len(image_urls),
        "files": {
            "storyboard": md_path,
            "prompts": prompts_path,
        },
        "full_prompt": full_prompt,
        "video_prompts": video_prompts,
    }


@router.get("/list")
def list_storyboards(db: Session = Depends(get_db)):
    events = (
        db.query(VideoEvent)
        .filter(VideoEvent.event_type == "storyboard_generated")
        .order_by(VideoEvent.created_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "video_id": e.video_id,
            "scenes": e.details.get("scenes") if e.details else None,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
