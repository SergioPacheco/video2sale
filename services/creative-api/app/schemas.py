from datetime import datetime
from pydantic import BaseModel


# === Prompt Templates ===

class PromptTemplateCreate(BaseModel):
    type: str
    name: str
    content: str
    variables: list[str] = []


class PromptTemplateUpdate(BaseModel):
    name: str | None = None
    content: str | None = None
    variables: list[str] | None = None
    active: bool | None = None


class PromptTemplateOut(BaseModel):
    id: int
    type: str
    name: str
    content: str
    variables: list[str]
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Products ===

class ProductBase(BaseModel):
    name: str
    category: str
    source: str = "TikTok Shop"
    asin: str | None = None
    product_url: str | None = None
    shop_url: str | None = None
    affiliate_url: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str = "EUR"
    rating: float | None = None
    reviews_count: int = 0
    pain_score: int = 0
    visual_score: int = 0
    trend_score: int = 0
    competition_score: int = 0
    availability_score: int = 0
    demo_score: int = 0
    impulse_buy_score: int = 0
    commission_estimate: float = 0
    notes: str | None = None
    assets: list[dict] | None = []


class ProductOut(ProductBase):
    id: int
    total_score: float = 0
    active: bool = True
    assets: list[dict] | None = []
    created_at: datetime

    class Config:
        from_attributes = True


class ProductImportResponse(BaseModel):
    source: str
    imported: int
    search_id: int


# === Weekly Winner ===

class WeeklyWinnerRequest(BaseModel):
    week: str  # '2026-W21'


class WeeklyWinnerOut(BaseModel):
    week: str
    product: ProductOut
    score: float
    reason: str

    class Config:
        from_attributes = True


# === Videos ===

class VideoOut(BaseModel):
    id: int
    product_id: int
    week: str
    template: str | None = None
    renderer: str = "seedance"
    status: str
    total_cost: float = 0
    voiceover_path: str | None = None
    video_path: str | None = None
    script_prompt_id: int | None = None
    renderer_prompt_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreativePackOut(BaseModel):
    id: int
    video_id: int
    version: int
    hook: str | None = None
    script_json: dict | list | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    compliance_status: str = "pending"
    compliance_notes: str | None = None
    selected: bool = False
    cost: float = 0
    created_at: datetime

    class Config:
        from_attributes = True


class VideoEventOut(BaseModel):
    id: int
    event_type: str
    actor: str
    details: dict | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class VideoDetailOut(VideoOut):
    creative_packs: list[CreativePackOut] = []
    events: list[VideoEventOut] = []
