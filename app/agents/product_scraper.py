"""Product Scraper — extrai info de produto a partir de URL."""

import re
import httpx
from bs4 import BeautifulSoup


async def scrape_product_url(url: str) -> dict:
    """Extrai nome, preço, imagem e descrição de uma URL de produto.

    Suporta: Amazon, AliExpress, páginas genéricas com meta tags.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.get(url, headers=headers, timeout=15)

    if resp.status_code != 200:
        return {"error": f"HTTP {resp.status_code}"}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Extrair dados usando meta tags (funciona para maioria dos sites)
    name = (
        _meta(soup, "og:title")
        or _meta(soup, "twitter:title")
        or _tag_text(soup, "h1")
        or _tag_text(soup, "title")
        or ""
    )

    image_url = (
        _meta(soup, "og:image")
        or _meta(soup, "twitter:image")
        or _first_img(soup)
        or ""
    )

    description = (
        _meta(soup, "og:description")
        or _meta(soup, "description")
        or ""
    )

    price = _extract_price(soup, resp.text)

    # Imagens adicionais
    images = _extract_images(soup, url)

    return {
        "name": name.strip()[:200],
        "description": description.strip()[:500],
        "image_url": image_url,
        "price": price,
        "product_url": url,
        "images": images[:9],
    }


def _meta(soup: BeautifulSoup, name: str) -> str | None:
    tag = soup.find("meta", attrs={"property": name}) or soup.find("meta", attrs={"name": name})
    return tag.get("content") if tag else None


def _tag_text(soup: BeautifulSoup, tag: str) -> str | None:
    el = soup.find(tag)
    return el.get_text(strip=True) if el else None


def _first_img(soup: BeautifulSoup) -> str | None:
    for img in soup.find_all("img", src=True):
        src = img["src"]
        if src.startswith("http") and any(ext in src.lower() for ext in [".jpg", ".png", ".webp"]):
            return src
    return None


def _extract_price(soup: BeautifulSoup, html: str) -> float | None:
    """Tenta extrair preço da página."""
    # Meta tag de preço
    price_meta = soup.find("meta", attrs={"property": "product:price:amount"})
    if price_meta:
        try:
            return float(price_meta["content"])
        except (ValueError, KeyError):
            pass

    # Padrões comuns de preço no HTML
    patterns = [
        r'\"price\":\s*\"?([\d.,]+)',
        r'class="[^"]*price[^"]*"[^>]*>[\s€$£]*?([\d.,]+)',
        r'€\s*([\d.,]+)',
        r'\$([\d.,]+)',
        r'([\d]+[.,]\d{2})\s*€',
    ]
    for pattern in patterns:
        m = re.search(pattern, html)
        if m:
            try:
                price_str = m.group(1).replace(",", ".")
                return float(price_str)
            except ValueError:
                continue
    return None


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extrai imagens relevantes do produto."""
    images = set()

    # og:image já capturado separadamente
    # Buscar imagens grandes (provavelmente do produto)
    for img in soup.find_all("img", src=True):
        src = img.get("src", "")
        # Filtrar imagens pequenas (ícones, logos)
        width = img.get("width", "")
        height = img.get("height", "")
        if width and int(width) < 100:
            continue
        if height and int(height) < 100:
            continue
        if src.startswith("http") and any(ext in src.lower() for ext in [".jpg", ".png", ".webp"]):
            if "logo" not in src.lower() and "icon" not in src.lower():
                images.add(src)

    # data-src (lazy loading)
    for img in soup.find_all("img", attrs={"data-src": True}):
        src = img["data-src"]
        if src.startswith("http"):
            images.add(src)

    return list(images)[:9]
