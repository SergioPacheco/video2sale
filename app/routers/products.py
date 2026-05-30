from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
import pandas as pd
import io

from app.database import get_db
from app.models import Product, ProductSearch
from app.schemas import ProductOut, ProductBase, ProductImportResponse
from app.agents.product_ranker import calculate_score

router = APIRouter(prefix="/products", tags=["products"])


@router.post("/import-csv", response_model=ProductImportResponse)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Importa produtos de um arquivo CSV."""
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser .csv")

    content = await file.read()
    df = pd.read_csv(io.BytesIO(content))

    # Registrar busca
    search = ProductSearch(
        source="manual_csv",
        keywords=file.filename,
        results_count=len(df),
    )
    db.add(search)
    db.flush()

    # Importar produtos
    imported = 0
    for _, row in df.iterrows():
        product = Product(
            search_id=search.id,
            name=row.get("name", ""),
            category=row.get("category", ""),
            source=row.get("source", "TikTok Shop"),
            asin=row.get("asin"),
            product_url=row.get("product_url"),
            shop_url=row.get("shop_url"),
            image_url=row.get("image_url"),
            price=row.get("price"),
            rating=row.get("rating"),
            reviews_count=int(row.get("reviews_count", 0)),
            pain_score=int(row.get("pain_score", 0)),
            visual_score=int(row.get("visual_score", 0)),
            trend_score=int(row.get("trend_score", 0)),
            competition_score=int(row.get("competition_score", 0)),
            availability_score=int(row.get("availability_score", 0)),
            demo_score=int(row.get("demo_score", 0)),
            impulse_buy_score=int(row.get("impulse_buy_score", 0)),
            commission_estimate=float(row.get("commission_estimate", 0)),
            notes=row.get("notes"),
        )
        product.total_score = calculate_score(row.to_dict())
        db.add(product)
        imported += 1

    db.commit()

    return ProductImportResponse(
        source="manual_csv",
        imported=imported,
        search_id=search.id,
    )


@router.post("/search-amazon", response_model=ProductImportResponse)
async def search_amazon(keywords: str, category: str = "All", db: Session = Depends(get_db)):
    """Busca produtos na Amazon via PA-API e importa no banco."""
    from app.agents.amazon_search import search_products

    results = await search_products(keywords, category)

    search = ProductSearch(
        source="amazon_pa_api",
        keywords=keywords,
        category=category,
        marketplace="amazon.es",
        results_count=len(results),
    )
    db.add(search)
    db.flush()

    for item in results:
        product = Product(
            search_id=search.id,
            name=item["name"],
            category=category,
            source="Amazon",
            asin=item.get("asin"),
            product_url=item.get("url"),
            affiliate_url=item.get("affiliate_url"),
            image_url=item.get("image_url"),
            price=item.get("price"),
            rating=item.get("rating"),
            reviews_count=item.get("reviews_count", 0),
        )
        product.total_score = 0  # Scores preenchidos pelo humano depois
        db.add(product)

    db.commit()

    return ProductImportResponse(
        source="amazon_pa_api",
        imported=len(results),
        search_id=search.id,
    )


@router.get("/", response_model=list[ProductOut])
def list_products(active: bool = True, db: Session = Depends(get_db)):
    """Lista todos os produtos."""
    query = db.query(Product).filter(Product.active == active)
    return query.order_by(Product.total_score.desc()).all()


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Detalhe de um produto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product


@router.post("/", response_model=ProductOut, status_code=201)
def create_product(data: ProductBase, db: Session = Depends(get_db)):
    """Cria um produto manualmente."""
    product = Product(**data.model_dump())
    product.total_score = calculate_score(data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductBase, db: Session = Depends(get_db)):
    """Atualiza um produto."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    product.total_score = calculate_score(data.model_dump())
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Desativa um produto (soft delete)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    product.active = False
    db.commit()
    return {"status": "ok", "id": product_id}


@router.post("/{product_id}/fetch-images")
async def fetch_product_images(
    product_id: int,
    tiktok_video_ids: list[str] = [],
    limit: int = 5,
    db: Session = Depends(get_db),
):
    """Busca imagens para um produto: TikTok thumbnails + Bing fallback.

    Salva em product.assets e retorna as imagens encontradas.
    """
    from app.agents.image_fetcher import fetch_images_for_product

    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")

    images = await fetch_images_for_product(
        product_name=product.name,
        category=product.category or "",
        tiktok_video_ids=tiktok_video_ids or [],
        limit=limit,
    )

    # Mesclar com assets existentes (evitar duplicatas por URL)
    existing_urls = {a.get("url") for a in (product.assets or [])}
    new_assets = [img for img in images if img["url"] not in existing_urls]
    product.assets = (product.assets or []) + new_assets
    db.commit()

    return {
        "product_id": product_id,
        "found": len(images),
        "added": len(new_assets),
        "assets": product.assets,
    }
