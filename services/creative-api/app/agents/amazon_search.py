"""Amazon Product Advertising API — busca de produtos."""

import os
import hashlib
import hmac
import json
from datetime import datetime

import httpx


async def search_products(keywords: str, category: str = "All") -> list[dict]:
    """Busca produtos na Amazon PA-API 5.0."""
    access_key = os.getenv("AMAZON_ACCESS_KEY")
    secret_key = os.getenv("AMAZON_SECRET_KEY")
    partner_tag = os.getenv("AMAZON_PARTNER_TAG")

    if not all([access_key, secret_key, partner_tag]):
        # Fallback: retorna lista vazia se credenciais não configuradas
        return []

    # Amazon PA-API 5.0 endpoint (Espanha)
    host = "webservices.amazon.es"
    endpoint = f"https://{host}/paapi5/searchitems"

    payload = {
        "Keywords": keywords,
        "SearchIndex": category,
        "ItemCount": 20,
        "Resources": [
            "ItemInfo.Title",
            "ItemInfo.Features",
            "Images.Primary.Large",
            "Offers.Listings.Price",
            "CustomerReviews.StarRating",
            "CustomerReviews.Count",
        ],
        "PartnerTag": partner_tag,
        "PartnerType": "Associates",
        "Marketplace": "www.amazon.es",
    }

    # TODO: Implementar assinatura AWS Signature V4 para PA-API
    # Por enquanto retorna lista vazia se não tiver SDK configurado
    try:
        async with httpx.AsyncClient() as client:
            # Placeholder — precisa de assinatura real
            # resp = await client.post(endpoint, json=payload, headers=signed_headers)
            pass
    except Exception:
        pass

    return []


def parse_pa_api_response(data: dict) -> list[dict]:
    """Converte resposta da PA-API em formato interno."""
    items = data.get("SearchResult", {}).get("Items", [])
    results = []

    for item in items:
        info = item.get("ItemInfo", {})
        images = item.get("Images", {})
        offers = item.get("Offers", {})
        reviews = item.get("CustomerReviews", {})

        price = None
        listings = offers.get("Listings", [])
        if listings:
            price = listings[0].get("Price", {}).get("Amount")

        results.append({
            "asin": item.get("ASIN"),
            "name": info.get("Title", {}).get("DisplayValue", ""),
            "url": item.get("DetailPageURL"),
            "affiliate_url": item.get("DetailPageURL"),  # PA-API já retorna com tag
            "image_url": images.get("Primary", {}).get("Large", {}).get("URL"),
            "price": price,
            "rating": reviews.get("StarRating", {}).get("Value"),
            "reviews_count": reviews.get("Count"),
        })

    return results
