from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.database import get_db
from app.models import Product, Video, VideoCreativePack, VideoEvent, PromptTemplate

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/")
def get_stats(db: Session = Depends(get_db)):
    """KPIs do pipeline."""
    total_products = db.query(func.count(Product.id)).filter(Product.active == True).scalar()
    total_videos = db.query(func.count(Video.id)).scalar()

    # Videos por status
    status_counts = dict(
        db.query(Video.status, func.count(Video.id))
        .group_by(Video.status)
        .all()
    )

    # Custo total
    total_cost = db.query(func.coalesce(func.sum(Video.total_cost), 0)).scalar()

    # Creative packs gerados
    total_packs = db.query(func.count(VideoCreativePack.id)).scalar()

    # Prompts ativos
    total_prompts = db.query(func.count(PromptTemplate.id)).filter(PromptTemplate.active == True).scalar()

    # Últimos 5 eventos
    recent_events = (
        db.query(VideoEvent)
        .order_by(VideoEvent.created_at.desc())
        .limit(5)
        .all()
    )

    # Videos por semana (últimas 4)
    weekly = (
        db.query(Video.week, func.count(Video.id))
        .group_by(Video.week)
        .order_by(Video.week.desc())
        .limit(4)
        .all()
    )

    return {
        "products": total_products,
        "videos": total_videos,
        "packs": total_packs,
        "prompts": total_prompts,
        "cost": float(total_cost),
        "status_counts": status_counts,
        "weekly": [{"week": w, "count": c} for w, c in weekly],
        "recent_events": [
            {"id": e.id, "video_id": e.video_id, "event_type": e.event_type, "actor": e.actor, "created_at": e.created_at.isoformat()}
            for e in recent_events
        ],
    }
