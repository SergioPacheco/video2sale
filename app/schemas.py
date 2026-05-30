from datetime import datetime
from pydantic import BaseModel


# === Integrations ===

class IntegrationOut(BaseModel):
    id: int
    provider: str
    status: str
    last_used_at: datetime | None = None
    last_error: str | None = None
    config: dict = {}
    created_at: datetime

    class Config:
        from_attributes = True


class IntegrationUpdate(BaseModel):
    api_key: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    config: dict | None = None


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


# === Generation Presets ===

class PresetCreate(BaseModel):
    name: str
    engine: str = "ffmpeg"
    template: str = "producto_destaque"
    voice: str = "nova"
    language: str = "es-ES"
    target_duration: int = 30
    music_mode: str = "auto"
    variations_count: int = 3
    is_default: bool = False


class PresetOut(PresetCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# === Projects ===

class ProjectCreate(BaseModel):
    name: str
    description: str | None = None
    target_videos: int = 5
    target_platform: str = "tiktok"
    config: dict = {}


class ProjectOut(ProjectCreate):
    id: int
    status: str = "active"
    created_at: datetime

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
    description: str | None = None
    commission_rate: float | None = None
    seller_name: str | None = None
    seller_url: str | None = None
    accepts_affiliates: bool = False
    assets: list[dict] | None = []


class ProductOut(ProductBase):
    id: int
    total_score: float = 0
    active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


class ProductImportResponse(BaseModel):
    source: str
    imported: int
    search_id: int


# === Assets ===

class AssetCreate(BaseModel):
    product_id: int
    type: str
    url: str
    source: str = "manual"
    label: str | None = None


class AssetOut(BaseModel):
    id: int
    product_id: int
    type: str
    url: str
    local_path: str | None = None
    source: str
    label: str | None = None
    width: int | None = None
    height: int | None = None
    duration_seconds: float | None = None
    used_in_videos: int = 0
    active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# === Weekly Winner ===

class WeeklyWinnerRequest(BaseModel):
    week: str


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
    project_id: int | None = None
    preset_id: int | None = None
    week: str
    template: str | None = None
    renderer: str = "ffmpeg"
    status: str
    total_cost: float = 0
    voiceover_path: str | None = None
    video_path: str | None = None
    thumbnail_path: str | None = None
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


# === Video Renders ===

class RenderOut(BaseModel):
    id: int
    video_id: int
    engine: str
    template: str | None = None
    voice: str = "nova"
    language: str = "es-ES"
    target_duration: int = 30
    video_path: str | None = None
    thumbnail_path: str | None = None
    duration_seconds: float | None = None
    total_cost: float = 0
    status: str = "pending"
    error_message: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Publications ===

class PublicationCreate(BaseModel):
    video_id: int
    render_id: int | None = None
    platform: str
    account_name: str | None = None
    caption_used: str | None = None
    hashtags_used: list[str] | None = None
    scheduled_at: datetime | None = None


class PublicationOut(BaseModel):
    id: int
    video_id: int
    render_id: int | None = None
    platform: str
    account_name: str | None = None
    external_id: str | None = None
    external_url: str | None = None
    caption_used: str | None = None
    hashtags_used: list[str] | None = None
    status: str = "draft"
    views: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    saves: int = 0
    published_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
