"""Trending products — dados do TikTok Creative Center ou catálogo local."""

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
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"


async def fetch_trending(country_code: str = "ES", period: int = 7) -> list[dict]:
    """Tenta buscar top products do TikTok Creative Center.
    Retorna lista vazia se não conseguir (API requer browser/auth)."""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(
                CREATIVE_CENTER_URL,
                params={"countryCode": country_code, "period": period},
                headers={"User-Agent": USER_AGENT},
                timeout=15,
            )

        if resp.status_code != 200:
            return []

        m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', resp.text, re.DOTALL)
        if not m:
            return []

        data = json.loads(m.group(1))
        return data.get("props", {}).get("pageProps", {}).get("data", [])
    except Exception:
        return []


@router.get("/")
async def list_trending(country: str = "ES", period: int = Query(7, enum=[7, 30]), db: Session = Depends(get_db)):
    """Lista produtos trending. Tenta TikTok Creative Center, fallback para catálogo local."""
    # Tentar TikTok Creative Center
    products = await fetch_trending(country, period)

    if products:
        return [
            {
                "name": p.get("urlTitle", ""),
                "category": p.get("firstEcomCategory", {}).get("value", ""),
                "subcategory": p.get("secondEcomCategory", {}).get("value", ""),
                "product_type": p.get("thirdEcomCategory", {}).get("value", ""),
                "popularity": p.get("post", 0),
                "popularity_change": p.get("postChange", 0),
                "ctr": p.get("ctr", 0),
                "cvr": p.get("cvr", 0),
                "likes": p.get("like", 0),
                "shares": p.get("share", 0),
                "source": "tiktok_creative_center",
            }
            for p in products
        ]

    # Fallback: top produtos do catálogo local por score
    local = (
        db.query(Product)
        .filter(Product.active == True)
        .order_by(Product.total_score.desc())
        .limit(20)
        .all()
    )

    return [
        {
            "name": p.name,
            "category": p.category,
            "subcategory": "",
            "product_type": p.source,
            "popularity": int(p.trend_score or 0),
            "popularity_change": 0,
            "ctr": 0,
            "cvr": 0,
            "likes": 0,
            "shares": 0,
            "total_score": float(p.total_score or 0),
            "product_id": p.id,
            "source": "local_catalog",
        }
        for p in local
    ]


@router.get("/oembed/{video_id}")
async def get_oembed(video_id: str):
    """Proxy para TikTok oEmbed (evita CORS)."""
    url = f"https://www.tiktok.com/@/video/{video_id}"
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://www.tiktok.com/oembed", params={"url": url}, timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        return {"thumbnail": data.get("thumbnail_url", ""), "title": data.get("title", ""), "author": data.get("author_name", "")}
    return {"thumbnail": "", "title": "", "author": ""}


@router.post("/import")
async def import_trending(
    indices: list[int],
    country: str = "ES",
    period: int = 7,
    db: Session = Depends(get_db),
):
    """Importa produtos do trending para o cadastro local."""
    products = await fetch_trending(country, period)
    if not products:
        raise HTTPException(status_code=502, detail="TikTok Creative Center indisponível. Use import CSV.")

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
                  f"CTR: {p.get('ctr')}%, CVR: {p.get('cvr')}%",
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
