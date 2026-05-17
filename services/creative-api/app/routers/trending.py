"""Busca produtos trending do TikTok Creative Center (dados públicos, gratuitos)."""

import re
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import Product
from app.agents.product_ranker import calculate_score

router = APIRouter(prefix="/tiktok-trending", tags=["tiktok-trending"])

CREATIVE_CENTER_URL = "https://ads.tiktok.com/business/creativecenter/top-products/pc/en"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def fetch_trending(country_code: str = "ES", period: int = 7) -> list[dict]:
    """Busca top products do TikTok Creative Center."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            CREATIVE_CENTER_URL,
            params={"countryCode": country_code, "period": period},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Erro ao acessar TikTok Creative Center")

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    if not m:
        raise HTTPException(status_code=502, detail="Formato inesperado do Creative Center")

    data = json.loads(m.group(1))
    return data.get("props", {}).get("pageProps", {}).get("data", [])


@router.get("/")
async def list_trending(country: str = "ES", period: int = Query(7, enum=[7, 30])):
    """Lista produtos trending do TikTok Creative Center (Espanha por padrão)."""
    products = await fetch_trending(country, period)

    return [
        {
            "name": p.get("urlTitle", ""),
            "category_id": p.get("thirdEcomCategory", {}).get("id", ""),
            "category": p.get("firstEcomCategory", {}).get("value", ""),
            "subcategory": p.get("secondEcomCategory", {}).get("value", ""),
            "product_type": p.get("thirdEcomCategory", {}).get("value", ""),
            "popularity": p.get("post", 0),
            "popularity_change": p.get("postChange", 0),
            "ctr": p.get("ctr", 0),
            "cvr": p.get("cvr", 0),
            "cpa": p.get("cpa", 0),
            "cost": p.get("cost", 0),
            "likes": p.get("like", 0),
            "shares": p.get("share", 0),
            "comments": p.get("comment", 0),
            "impressions": p.get("impression", 0),
            "view_rate_6s": p.get("playSixRate", 0),
        }
        for p in products
    ]


@router.get("/detail/{category_id}")
async def get_category_detail(category_id: str, name: str = "", country: str = "ES", period: int = 7):
    """Detalhe de uma categoria: hashtags, audience, vídeos de exemplo, métricas diárias."""
    category_name = name or category_id
    url = f"https://ads.tiktok.com/business/creativecenter/product-category/{category_name}-{category_id}/pc/en"
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            url,
            params={"index": 0, "level": "l3", "period": period, "type": "last", "region": country},
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Erro ao acessar detalhe")

    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
    if not m:
        raise HTTPException(status_code=502, detail="Formato inesperado")

    data = json.loads(m.group(1))
    props = data.get("props", {}).get("pageProps", {})
    info = props.get("info", {})
    metrics = props.get("metrics", {})

    video_ids = info.get("posts", [])
    videos = [
        {"id": vid, "url": f"https://www.tiktok.com/@/video/{vid}"}
        for vid in video_ids if isinstance(vid, str)
    ]

    return {
        "name": category_name,
        "category_id": category_id,
        "hashtags": info.get("hashtags", []),
        "audience_ages": info.get("audienceAges", []),
        "audience_interests": info.get("audienceInterests", []),
        "videos": videos,
        "metrics": {
            "ctr": metrics.get("ctr", 0),
            "cvr": metrics.get("cvr", 0),
            "cpa": metrics.get("cpa", 0),
            "likes": metrics.get("like", 0),
            "impressions": metrics.get("impression", 0),
            "posts": metrics.get("post", 0),
        },
        "daily_ctr": metrics.get("ctrMetrics", []),
        "daily_posts": metrics.get("postMetrics", []),
    }


@router.post("/import")
async def import_trending(
    indices: list[int],
    country: str = "ES",
    period: int = 7,
    db: Session = Depends(get_db),
):
    """Importa produtos selecionados do trending para o cadastro local."""
    products = await fetch_trending(country, period)

    imported = 0
    for idx in indices:
        if idx < 0 or idx >= len(products):
            continue

        p = products[idx]
        name = p.get("thirdEcomCategory", {}).get("value") or p.get("urlTitle", "")
        category = p.get("firstEcomCategory", {}).get("value", "")

        product = Product(
            name=name,
            category=category,
            source="TikTok Creative Center",
            notes=f"Subcategory: {p.get('secondEcomCategory', {}).get('value', '')}. "
                  f"CTR: {p.get('ctr')}%, CVR: {p.get('cvr')}%, CPA: ${p.get('cpa')}. "
                  f"Impressions: {p.get('impression', 0):,}",
            visual_score=min(10, int(p.get("playSixRate", 0))),
            trend_score=min(10, int(p.get("post", 0) / 1500)),
            pain_score=min(10, int(p.get("cvr", 0))),
            impulse_buy_score=min(10, int(p.get("ctr", 0) * 2)),
        )
        product.total_score = calculate_score({
            "pain_score": product.pain_score,
            "visual_score": product.visual_score,
            "trend_score": product.trend_score,
            "impulse_buy_score": product.impulse_buy_score,
            "demo_score": 0, "availability_score": 5,
            "commission_estimate": 0, "competition_score": 5,
        })
        db.add(product)
        imported += 1

    db.commit()
    return {"status": "ok", "imported": imported}
