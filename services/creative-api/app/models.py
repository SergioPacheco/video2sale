from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, JSON,
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import relationship

from app.database import Base


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
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    search = relationship("ProductSearch", back_populates="products")
    videos = relationship("Video", back_populates="product")


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
    week = Column(String, nullable=False)
    template = Column(String)
    selected_creative_pack_id = Column(Integer, ForeignKey("video_creative_packs.id", use_alter=True))
    voiceover_path = Column(Text)
    video_path = Column(Text)
    thumbnail_path = Column(Text)
    renderer = Column(String, default="seedance")
    renderer_config = Column(JSONB)
    status = Column(String, default="pending_creative")
    total_cost = Column(Numeric(8, 4), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="videos")
    creative_packs = relationship("VideoCreativePack", back_populates="video", foreign_keys="VideoCreativePack.video_id")
    events = relationship("VideoEvent", back_populates="video", order_by="VideoEvent.created_at")


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


class VideoEvent(Base):
    __tablename__ = "video_events"

    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id"))
    event_type = Column(String, nullable=False)
    actor = Column(String, default="system")
    details = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow)

    video = relationship("Video", back_populates="events")
