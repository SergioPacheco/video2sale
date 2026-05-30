from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Integration
from app.schemas import IntegrationOut, IntegrationUpdate

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/", response_model=list[IntegrationOut])
def list_integrations(db: Session = Depends(get_db)):
    return db.query(Integration).order_by(Integration.provider).all()


@router.get("/{provider}", response_model=IntegrationOut)
def get_integration(provider: str, db: Session = Depends(get_db)):
    item = db.query(Integration).filter(Integration.provider == provider).first()
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found")
    return item


@router.put("/{provider}", response_model=IntegrationOut)
def update_integration(provider: str, data: IntegrationUpdate, db: Session = Depends(get_db)):
    item = db.query(Integration).filter(Integration.provider == provider).first()
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    item.status = "connected"
    db.commit()
    db.refresh(item)
    return item


@router.post("/{provider}/disconnect", response_model=IntegrationOut)
def disconnect_integration(provider: str, db: Session = Depends(get_db)):
    item = db.query(Integration).filter(Integration.provider == provider).first()
    if not item:
        raise HTTPException(status_code=404, detail="Integration not found")
    item.status = "disconnected"
    item.access_token = None
    item.refresh_token = None
    db.commit()
    db.refresh(item)
    return item
