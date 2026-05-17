from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.database import get_db
from app.models import Video, VideoEvent

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.post("/import-sortfeed")
async def import_sortfeed(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importa métricas do Sort Feed (CSV exportado da extensão Chrome).
    Cruza vídeos por URL ou caption e atualiza métricas."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .csv")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    # Normalizar nomes de colunas (Sort Feed pode variar maiúsculas)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Mapear colunas possíveis
    url_col = next((c for c in df.columns if "url" in c or "link" in c), None)
    views_col = next((c for c in df.columns if "view" in c), None)
    likes_col = next((c for c in df.columns if "like" in c), None)
    comments_col = next((c for c in df.columns if "comment" in c), None)
    shares_col = next((c for c in df.columns if "share" in c), None)
    saves_col = next((c for c in df.columns if "save" in c or "favorite" in c or "bookmark" in c), None)
    caption_col = next((c for c in df.columns if "caption" in c or "description" in c), None)

    if not views_col:
        raise HTTPException(status_code=400, detail="CSV não contém coluna de views")

    # Buscar todos os vídeos publicados
    videos = db.query(Video).filter(Video.status == "published").all()
    updated = 0

    for _, row in df.iterrows():
        matched_video = None

        # Tentar cruzar por URL (se o vídeo tem tiktok_url salvo no evento de publish)
        if url_col and pd.notna(row.get(url_col)):
            tiktok_url = str(row[url_col]).strip()
            for v in videos:
                # Verificar nos eventos de publish
                for event in v.events:
                    if event.event_type == "published" and event.details:
                        if event.details.get("tiktok_url") == tiktok_url:
                            matched_video = v
                            break
                if matched_video:
                    break

        # Se não cruzou por URL, tentar por caption
        if not matched_video and caption_col and pd.notna(row.get(caption_col)):
            caption = str(row[caption_col]).strip()[:50]  # primeiros 50 chars
            from app.models import VideoCreativePack
            for v in videos:
                pack = db.query(VideoCreativePack).filter(
                    VideoCreativePack.id == v.selected_creative_pack_id
                ).first()
                if pack and pack.caption and caption in pack.caption:
                    matched_video = v
                    break

        if not matched_video:
            continue

        # Atualizar métricas
        metrics = {}
        if views_col and pd.notna(row.get(views_col)):
            metrics["views"] = int(row[views_col])
        if likes_col and pd.notna(row.get(likes_col)):
            metrics["likes"] = int(row[likes_col])
        if comments_col and pd.notna(row.get(comments_col)):
            metrics["comments"] = int(row[comments_col])
        if shares_col and pd.notna(row.get(shares_col)):
            metrics["shares"] = int(row[shares_col])
        if saves_col and pd.notna(row.get(saves_col)):
            metrics["saves"] = int(row[saves_col])

        if metrics:
            db.add(VideoEvent(
                video_id=matched_video.id,
                event_type="metrics_updated",
                actor="sortfeed",
                details=metrics,
            ))
            updated += 1

    db.commit()

    return {
        "status": "ok",
        "rows_in_csv": len(df),
        "videos_updated": updated,
        "columns_detected": {
            "url": url_col, "views": views_col, "likes": likes_col,
            "comments": comments_col, "shares": shares_col, "saves": saves_col,
        },
    }


@router.get("/video/{video_id}")
def get_video_metrics(video_id: int, db: Session = Depends(get_db)):
    """Retorna métricas mais recentes de um vídeo (do último evento metrics_updated)."""
    event = (
        db.query(VideoEvent)
        .filter(VideoEvent.video_id == video_id, VideoEvent.event_type == "metrics_updated")
        .order_by(VideoEvent.created_at.desc())
        .first()
    )
    if not event:
        return {"video_id": video_id, "metrics": None, "source": None}

    return {
        "video_id": video_id,
        "metrics": event.details,
        "source": event.actor,
        "updated_at": event.created_at.isoformat(),
    }
