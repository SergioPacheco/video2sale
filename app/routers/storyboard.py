"""Storyboard — gera pacote de produção com prompts Seedance + materiais."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import json
import os
from pathlib import Path

from app.database import get_db
from app.models import Video, VideoCreativePack, Product, Asset, VideoEvent
from app.config import settings

router = APIRouter(prefix="/storyboard", tags=["storyboard"])

OUTPUT_BASE = Path("/output")

SEEDANCE_TEMPLATE = """## Cena {i} ({start}s - {end}s)

### Material
| Slot | Arquivo | Uso |
|------|---------|-----|
{material_table}

### Prompt Seedance
```
{style_prefix}

{start}-{end}s: {visual}

【Texto em tela】{text}
【Narração】{voiceover}
【Câmera】{camera}
【Referência】{references}
```

### Prompt para copiar:
{visual}. {camera_en}. Vertical 9:16, product video, high quality, TikTok style.
"""


@router.post("/generate/{video_id}")
async def generate_storyboard(video_id: int, style: str = "product_showcase", db: Session = Depends(get_db)):
    """Gera pacote de produção completo: prompts Seedance + materiais organizados.

    Salva em /output/{week}/{product_id}/storyboard/
    """
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

    # Imagens do produto (assets + legado)
    image_urls = [a.url for a in assets if a.type in ("image", "lifestyle", "detail")]
    if not image_urls and product.image_url:
        image_urls = [product.image_url]
    if not image_urls and product.assets:
        image_urls = [a.get("url") for a in product.assets if a.get("url")]

    # Diretório de saída
    storyboard_dir = OUTPUT_BASE / video.week / str(product.id) / "storyboard"
    storyboard_dir.mkdir(parents=True, exist_ok=True)

    # Estilo base
    styles = {
        "product_showcase": "Realistic product video, clean background, natural lighting, smooth camera movement",
        "lifestyle": "Lifestyle video, product in use, natural environment, warm tones",
        "before_after": "Before and after comparison, split screen transition, dramatic reveal",
        "unboxing": "Unboxing video, hands opening package, close-up details, excitement",
        "review": "Product review style, multiple angles, detail shots, honest presentation",
    }
    style_prefix = styles.get(style, styles["product_showcase"])

    # Câmeras por cena
    cameras = [
        ("Plano general, cámara estática", "Wide shot, static camera"),
        ("Primer plano, zoom lento", "Close-up, slow zoom in"),
        ("Plano detalle, paneo lateral", "Detail shot, lateral pan"),
        ("Plano medio, seguimiento", "Medium shot, tracking"),
        ("Primer plano, zoom out", "Close-up, slow zoom out"),
        ("Plano general, cámara baja", "Wide shot, low angle"),
    ]

    scenes = pack.script_json or []
    storyboard_md = f"""# Storyboard — {product.name}

**Producto:** {product.name}
**Categoría:** {product.category}
**Semana:** {video.week}
**Estilo:** {style}
**Hook:** {pack.hook}
**Caption:** {pack.caption}
**Hashtags:** {' '.join(pack.hashtags or [])}

---

## Materiales disponibles

| # | Tipo | URL |
|---|------|-----|
"""
    for i, url in enumerate(image_urls[:9], 1):
        storyboard_md += f"| IMG{i} | image | {url} |\n"

    storyboard_md += f"\n---\n\n## Escenas ({len(scenes)} cenas, ~{sum(s.get('end',5)-s.get('start',0) for s in scenes)}s total)\n\n"

    # Gerar prompt por cena
    seedance_prompts = []
    for i, scene in enumerate(scenes):
        start = scene.get("start", i * 5)
        end = scene.get("end", start + 5)
        text = scene.get("text", "")
        voiceover = scene.get("voiceover", "")
        visual = scene.get("visual", "")
        camera_es, camera_en = cameras[i % len(cameras)]

        # Material table
        material_lines = []
        if i < len(image_urls):
            material_lines.append(f"| Imagen {i+1} | IMG{i+1} | Referencia visual |")
        material_table = "\n".join(material_lines) if material_lines else "| - | Sin material | Generar con IA |"

        # Referências
        refs = f"@IMG{i+1}" if i < len(image_urls) else "Sin referencia"

        # Prompt completo para Seedance
        seedance_prompt = f"{style_prefix}, vertical 9:16\n\n{start}-{end}s: {visual}. {camera_en}."
        seedance_prompts.append({
            "scene": i + 1,
            "start": start,
            "end": end,
            "prompt": seedance_prompt,
            "text_overlay": text,
            "voiceover": voiceover,
            "camera": camera_en,
            "image_ref": image_urls[i] if i < len(image_urls) else None,
        })

        storyboard_md += SEEDANCE_TEMPLATE.format(
            i=i+1, start=start, end=end,
            material_table=material_table,
            style_prefix=style_prefix,
            visual=visual, text=text, voiceover=voiceover,
            camera=camera_es, camera_en=camera_en,
            references=refs,
        )

    # Prompt completo (para copiar tudo de uma vez no Seedance)
    full_prompt = f"""{style_prefix}, vertical 9:16, {product.category} product

"""
    for i, scene in enumerate(scenes):
        start = scene.get("start", i * 5)
        end = scene.get("end", start + 5)
        visual = scene.get("visual", "")
        _, camera_en = cameras[i % len(cameras)]
        full_prompt += f"{start}-{end}s: {visual}. {camera_en}.\n"

    full_prompt += f"\n【Audio】Energetic background music, product sounds\n"
    full_prompt += f"【References】" + ", ".join(f"@IMG{i+1}" for i in range(min(len(image_urls), len(scenes))))

    storyboard_md += f"""
---

## Prompt completo (copiar para Seedance)

```
{full_prompt}
```

---

## Caption para TikTok

```
{pack.caption}

{' '.join(pack.hashtags or [])}

{pack.affiliate_disclaimer or ''}
```
"""

    # Salvar arquivos
    md_path = str(storyboard_dir / "storyboard.md")
    with open(md_path, "w") as f:
        f.write(storyboard_md)

    prompts_path = str(storyboard_dir / "prompts.json")
    with open(prompts_path, "w") as f:
        json.dump({
            "product": product.name,
            "style": style,
            "full_prompt": full_prompt,
            "scenes": seedance_prompts,
            "caption": pack.caption,
            "hashtags": pack.hashtags,
            "images": image_urls[:9],
        }, f, ensure_ascii=False, indent=2)

    # Registrar evento
    db.add(VideoEvent(video_id=video_id, event_type="storyboard_generated", actor="system",
                      details={"style": style, "scenes": len(scenes), "images": len(image_urls)}))
    db.commit()

    return {
        "status": "ok",
        "video_id": video_id,
        "product": product.name,
        "style": style,
        "scenes": len(scenes),
        "images": len(image_urls),
        "files": {
            "storyboard": md_path,
            "prompts": prompts_path,
        },
        "full_prompt": full_prompt,
        "seedance_prompts": seedance_prompts,
    }


@router.get("/list")
def list_storyboards(db: Session = Depends(get_db)):
    """Lista storyboards gerados."""
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
            "style": e.details.get("style") if e.details else None,
            "scenes": e.details.get("scenes") if e.details else None,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
