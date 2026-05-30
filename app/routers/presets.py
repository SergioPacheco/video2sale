from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GenerationPreset
from app.schemas import PresetCreate, PresetOut

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("/", response_model=list[PresetOut])
def list_presets(db: Session = Depends(get_db)):
    return db.query(GenerationPreset).order_by(GenerationPreset.name).all()


@router.get("/{preset_id}", response_model=PresetOut)
def get_preset(preset_id: int, db: Session = Depends(get_db)):
    item = db.query(GenerationPreset).filter(GenerationPreset.id == preset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Preset not found")
    return item


@router.post("/", response_model=PresetOut, status_code=201)
def create_preset(data: PresetCreate, db: Session = Depends(get_db)):
    item = GenerationPreset(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/{preset_id}", response_model=PresetOut)
def update_preset(preset_id: int, data: PresetCreate, db: Session = Depends(get_db)):
    item = db.query(GenerationPreset).filter(GenerationPreset.id == preset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Preset not found")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{preset_id}")
def delete_preset(preset_id: int, db: Session = Depends(get_db)):
    item = db.query(GenerationPreset).filter(GenerationPreset.id == preset_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Preset not found")
    db.delete(item)
    db.commit()
    return {"status": "ok", "id": preset_id}
