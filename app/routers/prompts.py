from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import PromptTemplate
from app.schemas import PromptTemplateCreate, PromptTemplateUpdate, PromptTemplateOut

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("/", response_model=list[PromptTemplateOut])
def list_prompts(type: str | None = None, active: bool = True, db: Session = Depends(get_db)):
    query = db.query(PromptTemplate).filter(PromptTemplate.active == active)
    if type:
        query = query.filter(PromptTemplate.type == type)
    return query.order_by(PromptTemplate.name).all()


@router.get("/{prompt_id}", response_model=PromptTemplateOut)
def get_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    return prompt


@router.post("/", response_model=PromptTemplateOut, status_code=201)
def create_prompt(data: PromptTemplateCreate, db: Session = Depends(get_db)):
    prompt = PromptTemplate(**data.model_dump())
    db.add(prompt)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.put("/{prompt_id}", response_model=PromptTemplateOut)
def update_prompt(prompt_id: int, data: PromptTemplateUpdate, db: Session = Depends(get_db)):
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(prompt, key, value)
    db.commit()
    db.refresh(prompt)
    return prompt


@router.delete("/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt não encontrado")
    prompt.active = False
    db.commit()
    return {"status": "ok", "id": prompt_id}
