from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VideoRender
from app.schemas import RenderOut

router = APIRouter(prefix="/renders", tags=["renders"])


@router.get("/", response_model=list[RenderOut])
def list_renders(video_id: int | None = None, status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(VideoRender)
    if video_id:
        query = query.filter(VideoRender.video_id == video_id)
    if status:
        query = query.filter(VideoRender.status == status)
    return query.order_by(VideoRender.created_at.desc()).all()


@router.get("/{render_id}", response_model=RenderOut)
def get_render(render_id: int, db: Session = Depends(get_db)):
    item = db.query(VideoRender).filter(VideoRender.id == render_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Render not found")
    return item
