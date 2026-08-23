from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, DateTime, Float, ForeignKey, JSON,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


# ============================================================
# INTEGRAÇÕES
# ============================================================

class Integration(Base):
    __tablename__ = "integrations"

    id = Column(Integer, primary_key=True)
    provider = Column(String, nullable=False, unique=True)
    api_key = Column(Text)
    client_id = Column(Text)
    client_secret = Column(Text)
    access_token = Column(Text)
    refresh_token = Column(Text)
    token_expires_at = Column(DateTime)
    status = Column(String, default="disconnected")
    last_used_at = Column(DateTime)
    last_error = Column(Text)
    config = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# PROMPT TEMPLATES
# ============================================================

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    variables = Column(ARRAY(String), default=[])
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================
# PRESETS DE GERAÇÃO
# ============================================================

class GenerationPreset(Base):
    __tablename__ = "generation_presets"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    engine = Column(String, default="ffmpeg")
    template = Column(String, default="producto_destaque")
    voice = Column(String, default="nova")
    language = Column(String, default="pt-BR")
    target_duration = Column(Integer, default=30)
    music_mode = Column(String, default="auto")
    variations_count = Column(Integer, default=3)
    script_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    compliance_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================
# PROJETOS
# ============================================================

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="active")
    target_videos = Column(Integer, default=5)
    target_platform = Column(String, default="tiktok")
    config = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    videos = relationship("Video", back_populates="project")


# ============================================================
# PRODUTOS
# ============================================================

class ProductSearch(Base):
    __tablename__ = "product_searches"

    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False, default="manual_csv")
    keywords = Column(Text)
    category = Column(Text)
    marketplace = Column(String, default="amazon.es")
    results_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    products = relationship("Product", back_populates="search")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    search_id = Column(Integer, ForeignKey("product_searches.id"))
    name = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    source = Column(String, default="TikTok Shop")
    asin = Column(String)
    product_url = Column(Text)
    shop_url = Column(Text)
    affiliate_url = Column(Text)
    image_url = Column(Text)
    price = Column(Numeric(10, 2))
    currency = Column(String, default="EUR")
    rating = Column(Numeric(3, 2))
    reviews_count = Column(Integer, default=0)
    pain_score = Column(Integer, default=0)
    visual_score = Column(Integer, default=0)
    trend_score = Column(Integer, default=0)
    competition_score = Column(Integer, default=0)
    availability_score = Column(Integer, default=0)
    demo_score = Column(Integer, default=0)
    impulse_buy_score = Column(Integer, default=0)
    commission_estimate = Column(Numeric(5, 2), default=0)
    total_score = Column(Numeric(5, 2), default=0)
    notes = Column(Text)
    description = Column(Text)
    commission_rate = Column(Numeric(5, 2))
    seller_name = Column(String)
    seller_url = Column(Text)
    accepts_affiliates = Column(Boolean, default=False)
    assets = Column(JSONB, default=[])  # legado compatível; a fonte ativa é a tabela assets
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    search = relationship("ProductSearch", back_populates="products")
    videos = relationship("Video", back_populates="product")
    asset_files = relationship("Asset", back_populates="product")


# ============================================================
# ASSETS
# ============================================================

class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"))
    type = Column(String, nullable=False)  # image, video, lifestyle, detail, before_after
    url = Column(Text, nullable=False)
    local_path = Column(Text)
    filename = Column(String)
    mime_type = Column(String)
    size_bytes = Column(Integer)
    source = Column(String, default="manual")  # manual, serper, tiktok, amazon, upload
    label = Column(Text)
    width = Column(Integer)
    height = Column(Integer)
    duration_seconds = Column(Float)
    used_in_videos = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="asset_files")


# ============================================================
# VÍDEOS
# ============================================================

class WeeklyWinner(Base):
    __tablename__ = "weekly_winners"

    id = Column(Integer, primary_key=True)
    week = Column(String, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    score = Column(Numeric(5, 2))
    reason = Column(Text)
    approved_by = Column(String, default="system")
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product")


class Video(Base):
    __tablename__ = "videos"

    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey("products.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    preset_id = Column(Integer, ForeignKey("generation_presets.id"))
    week = Column(String, nullable=False)
    template = Column(String)
    selected_creative_pack_id = Column(Integer, ForeignKey("video_creative_packs.id", use_alter=True))
    best_render_id = Column(Integer, ForeignKey("video_renders.id", use_alter=True))
    voiceover_path = Column(Text)
    video_path = Column(Text)
    thumbnail_path = Column(Text)
    renderer = Column(String, default="ffmpeg")
    renderer_config = Column(JSONB)
    script_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    renderer_prompt_id = Column(Integer, ForeignKey("prompt_templates.id"))
    status = Column(String, default="pending_creative")
    total_cost = Column(Numeric(8, 4), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="videos")
    project = relationship("Project", back_populates="videos")
    creative_packs = relationship("VideoCreativePack", back_populates="video", foreign_keys="VideoCreativePack.video_id")
    renders = relationship("VideoRender", back_populates="video", foreign_keys="VideoRender.video_id")
    events = relationship("VideoEvent", back_populates="video", order_by="VideoEvent.created_at")
    publications = relationship("Publication", back_populates="video")


# ============================================================
# PACOTES CRIATIVOS
# ============================================================

class VideoCreativePack(Base):
    __tablename__ = "video_creative_packs"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    version = Column(Integer, default=1)
    hook = Column(Text)
    script_json = Column(JSONB)
    caption = Column(Text)
    hashtags = Column(ARRAY(String))
    affiliate_disclaimer = Column(Text)
    compliance_status = Column(String, default="pending")
    compliance_notes = Column(Text)
    selected = Column(Boolean, default=False)
    model_used = Column(String)
    tokens_input = Column(Integer, default=0)
    tokens_output = Column(Integer, default=0)
    cost = Column(Numeric(8, 6), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="creative_packs", foreign_keys=[video_id])


# ============================================================
# RENDERS
# ============================================================

class VideoRender(Base):
    __tablename__ = "video_renders"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    engine = Column(String, nullable=False, default="ffmpeg")
    template = Column(String)
    voice = Column(String, default="nova")
    language = Column(String, default="pt-BR")
    target_duration = Column(Integer, default=30)
    music_track = Column(Text)
    video_path = Column(Text)
    thumbnail_path = Column(Text)
    duration_seconds = Column(Float)
    resolution = Column(String, default="1080x1920")
    file_size_bytes = Column(Integer)
    llm_cost = Column(Numeric(8, 6), default=0)
    tts_cost = Column(Numeric(8, 6), default=0)
    render_cost = Column(Numeric(8, 6), default=0)
    total_cost = Column(Numeric(8, 4), default=0)
    status = Column(String, default="pending")
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="renders", foreign_keys=[video_id])


# ============================================================
# EVENTOS
# ============================================================

class VideoEvent(Base):
    __tablename__ = "video_events"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"))
    event_type = Column(String, nullable=False)
    actor = Column(String, default="system")
    details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="events")


# ============================================================
# PUBLICAÇÕES
# ============================================================

class Publication(Base):
    __tablename__ = "publications"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    render_id = Column(Integer, ForeignKey("video_renders.id"))
    platform = Column(String, nullable=False)
    account_name = Column(String)
    external_id = Column(Text)
    external_url = Column(Text)
    caption_used = Column(Text)
    hashtags_used = Column(ARRAY(String))
    scheduled_at = Column(DateTime)
    published_at = Column(DateTime)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    saves = Column(Integer, default=0)
    status = Column(String, default="draft")
    error_message = Column(Text)
    metrics_updated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="publications")
