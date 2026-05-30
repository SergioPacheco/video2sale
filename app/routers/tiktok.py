"""TikTok Integration — OAuth2 + Product Search via Research API."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import httpx

from app.database import get_db
from app.models import Integration, Product
from app.config import settings
from app.agents.product_ranker import calculate_score

router = APIRouter(prefix="/tiktok", tags=["tiktok"])

TIKTOK_AUTH_URL = "https://open-api.tiktok.com/v2/oauth/token/"
TIKTOK_SHOP_API = "https://open.tiktokapis.com/v2/research/tts"


async def get_client_token(db: Session) -> str:
    """Obtém client access token do TikTok (machine-to-machine, sem user)."""
    integration = db.query(Integration).filter(Integration.provider == "tiktok").first()

    # Se já tem token válido, retorna
    if integration and integration.access_token and integration.token_expires_at:
        if integration.token_expires_at > datetime.utcnow():
            return integration.access_token

    # Obter novo token
    client_key = settings.tiktok_client_key
    client_secret = settings.tiktok_client_secret

    if not client_key or not client_secret:
        raise HTTPException(status_code=400, detail="TIKTOK_CLIENT_KEY e TIKTOK_CLIENT_SECRET não configurados no .env")

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://open.tiktokapis.com/v2/oauth/token/",
            data={
                "client_key": client_key,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=15,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TikTok OAuth falhou: {resp.text}")

    data = resp.json()
    access_token = data.get("access_token")
    expires_in = data.get("expires_in", 7200)

    if not access_token:
        raise HTTPException(status_code=502, detail=f"TikTok não retornou token: {data}")

    # Salvar no banco
    if not integration:
        integration = db.query(Integration).filter(Integration.provider == "tiktok").first()
    if integration:
        integration.access_token = access_token
        integration.token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        integration.status = "connected"
        integration.last_used_at = datetime.utcnow()
        db.commit()

    return access_token


@router.post("/connect")
async def connect_tiktok(db: Session = Depends(get_db)):
    """Testa conexão com TikTok API e obtém client token."""
    token = await get_client_token(db)
    return {"status": "connected", "token_preview": token[:20] + "..."}


@router.get("/shop/search")
async def search_shop(
    shop_name: str,
    db: Session = Depends(get_db),
):
    """Busca uma loja no TikTok Shop."""
    token = await get_client_token(db)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TIKTOK_SHOP_API}/shop/",
            json={
                "shop_name": shop_name,
                "fields": "shop_name,shop_rating,shop_review_count,item_sold_count,shop_id,shop_performance_value",
                "limit": 10,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    if resp.status_code != 200:
        error_data = resp.json() if resp.text.startswith("{") else {}
        error_msg = error_data.get("error", {}).get("message", resp.text)
        if "scope_not_authorized" in str(error_data):
            raise HTTPException(status_code=403, detail="TikTok Research API requer scope 'research.data.basic'. Solicite acesso em developers.tiktok.com")
        raise HTTPException(status_code=502, detail=f"TikTok API error: {error_msg}")

    data = resp.json()
    return data.get("data", {})


@router.get("/shop/products")
async def search_products(
    shop_name: str,
    db: Session = Depends(get_db),
):
    """Busca produtos de uma loja no TikTok Shop."""
    token = await get_client_token(db)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TIKTOK_SHOP_API}/shop/products/",
            json={
                "shop_name": shop_name,
                "fields": "product_name,product_id,product_price,product_rating,product_review_count,product_sold_count,product_image",
                "limit": 20,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    if resp.status_code != 200:
        error_data = resp.json() if resp.text.startswith("{") else {}
        error_msg = error_data.get("error", {}).get("message", resp.text)
        if "scope_not_authorized" in str(error_data):
            raise HTTPException(status_code=403, detail="TikTok Research API requer scope 'research.data.basic'. Solicite acesso em developers.tiktok.com")
        raise HTTPException(status_code=502, detail=f"TikTok API error: {error_msg}")

    data = resp.json()
    return data.get("data", {})


@router.post("/shop/import")
async def import_from_shop(
    shop_name: str,
    category: str = "TikTok Shop",
    db: Session = Depends(get_db),
):
    """Busca produtos de uma loja TikTok e importa para o catálogo."""
    token = await get_client_token(db)

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{TIKTOK_SHOP_API}/shop/products/",
            json={
                "shop_name": shop_name,
                "fields": "product_name,product_id,product_price,product_rating,product_review_count,product_sold_count,product_image",
                "limit": 20,
            },
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            timeout=15,
        )

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"TikTok API error: {resp.status_code}")

    data = resp.json()
    products_data = data.get("data", {}).get("products", [])

    imported = 0
    for p in products_data:
        product = Product(
            name=p.get("product_name", ""),
            category=category,
            source="TikTok Shop",
            shop_url=f"https://shop.tiktok.com/product/{p.get('product_id', '')}",
            image_url=p.get("product_image", ""),
            price=p.get("product_price"),
            rating=p.get("product_rating"),
            reviews_count=p.get("product_review_count", 0),
            seller_name=shop_name,
            trend_score=min(10, int((p.get("product_sold_count", 0) or 0) / 100)),
            visual_score=5,
        )
        product.total_score = calculate_score({
            "pain_score": 0, "visual_score": product.visual_score,
            "trend_score": product.trend_score, "impulse_buy_score": 5,
            "demo_score": 0, "availability_score": 8,
            "commission_estimate": 0, "competition_score": 5,
        })
        db.add(product)
        imported += 1

    db.commit()
    return {"status": "ok", "shop": shop_name, "imported": imported}
