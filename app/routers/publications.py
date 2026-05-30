from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Publication
from app.schemas import PublicationCreate, PublicationOut

router = APIRouter(prefix="/publications", tags=["publications"])


@router.get("/", response_model=list[PublicationOut])
def list_publications(video_id: int | None = None, platform: str | None = None, status: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Publication)
    if video_id:
        query = query.filter(Publication.video_id == video_id)
    if platform:
        query = query.filter(Publication.platform == platform)
    if status:
        query = query.filter(Publication.status == status)
    return query.order_by(Publication.created_at.desc()).all()


@router.get("/{pub_id}", response_model=PublicationOut)
def get_publication(pub_id: int, db: Session = Depends(get_db)):
    item = db.query(Publication).filter(Publication.id == pub_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Publication not found")
    return item


@router.post("/", response_model=PublicationOut, status_code=201)
def create_publication(data: PublicationCreate, db: Session = Depends(get_db)):
    item = Publication(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.post("/{pub_id}/publish", response_model=PublicationOut)
def mark_published(pub_id: int, external_id: str | None = None, external_url: str | None = None, db: Session = Depends(get_db)):
    item = db.query(Publication).filter(Publication.id == pub_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Publication not found")
    item.status = "published"
    item.published_at = datetime.utcnow()
    if external_id:
        item.external_id = external_id
    if external_url:
        item.external_url = external_url
    db.commit()
    db.refresh(item)
    return item
