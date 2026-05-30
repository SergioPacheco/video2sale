"""Busca imagens para produtos.

Estratégia (em ordem de prioridade):
1. Serper.dev (Google Images API) — se SERPER_API_KEY configurada
2. Extração da URL do produto (Amazon/TikTok Shop têm og:image acessível)
3. TikTok oEmbed — thumbnails de vídeos da categoria

Salva em product.assets como lista de {"url": str, "type": "image", "source": str}
"""

import re
import httpx
from app.config import settings

SERPER_URL = "https://google.serper.dev/images"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


async def fetch_serper_images(query: str, limit: int = 5) -> list[dict]:
    """Busca imagens via Serper.dev (Google Images). Requer SERPER_API_KEY."""
    if not settings.serper_api_key:
        return []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                SERPER_URL,
                json={"q": query, "num": limit, "gl": "es", "hl": "es"},
                headers={"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"},
            )
        if resp.status_code != 200:
            return []
        data = resp.json()
        return [
            {"url": img["imageUrl"], "type": "image", "source": "serper"}
            for img in data.get("images", [])[:limit]
            if img.get("imageUrl")
        ]
    except Exception as e:
        print(f"[IMAGE] Serper error: {e}")
        return []


async def fetch_og_image(product_url: str) -> list[dict]:
    """Extrai og:image da página do produto (Amazon, TikTok Shop, etc.)."""
    if not product_url:
        return []
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            resp = await client.get(product_url, headers={"User-Agent": USER_AGENT})
        if resp.status_code != 200:
            return []
        # og:image
        m = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', resp.text)
        if not m:
            m = re.search(r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', resp.text)
        if m:
            return [{"url": m.group(1), "type": "image", "source": "product_page"}]
    except Exception as e:
        print(f"[IMAGE] og:image error: {e}")
    return []


async def fetch_tiktok_thumbnails(video_ids: list[str], limit: int = 5) -> list[dict]:
    """Busca thumbnails via TikTok oEmbed para uma lista de video IDs."""
    results = []
    async with httpx.AsyncClient(timeout=8) as client:
        for vid in video_ids[:limit]:
            try:
                resp = await client.get(
                    "https://www.tiktok.com/oembed",
                    params={"url": f"https://www.tiktok.com/@/video/{vid}"},
                )
                if resp.status_code == 200:
                    thumb = resp.json().get("thumbnail_url", "")
                    if thumb:
                        results.append({"url": thumb, "type": "image", "source": "tiktok"})
            except Exception:
                continue
    return results


async def fetch_images_for_product(
    product_name: str,
    category: str = "",
    product_url: str = "",
    tiktok_video_ids: list[str] | None = None,
    limit: int = 5,
) -> list[dict]:
    """Busca imagens para um produto com fallback em cascata.

    Ordem: Serper → og:image da URL do produto → TikTok oEmbed
    """
    images: list[dict] = []

    # 1. Serper (Google Images) — melhor qualidade
    if len(images) < limit:
        query = f"{product_name} {category}".strip()
        images += await fetch_serper_images(query, limit=limit - len(images))

    # 2. og:image da página do produto
    if len(images) < limit and product_url:
        images += await fetch_og_image(product_url)

    # 3. TikTok oEmbed
    if len(images) < limit and tiktok_video_ids:
        images += await fetch_tiktok_thumbnails(tiktok_video_ids, limit=limit - len(images))

    return images[:limit]
