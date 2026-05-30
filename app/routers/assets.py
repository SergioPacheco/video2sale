from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Asset
from app.schemas import AssetCreate, AssetOut

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("/", response_model=list[AssetOut])
def list_assets(product_id: int | None = None, type: str | None = None, db: Session = Depends(get_db)):
    query = db.query(Asset).filter(Asset.active == True)
    if product_id:
        query = query.filter(Asset.product_id == product_id)
    if type:
        query = query.filter(Asset.type == type)
    return query.order_by(Asset.created_at.desc()).all()


@router.get("/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: int, db: Session = Depends(get_db)):
    item = db.query(Asset).filter(Asset.id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Asset not found")
    return item


@router.post("/", response_model=AssetOut, status_code=201)
def create_asset(data: AssetCreate, db: Session = Depends(get_db)):
    item = Asset(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{asset_id}")
def delete_asset(asset_id: int, db: Session = Depends(get_db)):
    item = db.query(Asset).filter(Asset.id == asset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Asset not found")
    item.active = False
    db.commit()
    return {"status": "ok", "id": asset_id}
