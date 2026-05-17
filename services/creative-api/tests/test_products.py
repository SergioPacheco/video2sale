import io

import pytest

needs_db = pytest.mark.skipif(
    True, reason="Testes de integração requerem PostgreSQL (docker compose up)"
)


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@needs_db
def test_import_csv(client):
    csv_content = (
        "name,category,source,price,pain_score,visual_score,trend_score,"
        "competition_score,availability_score,demo_score,impulse_buy_score,commission_estimate\n"
        "Cortador de legumes,Cozinha,TikTok Shop,14.99,8,9,8,7,8,10,8,3\n"
        "Organizador,Casa,TikTok Shop,19.99,9,8,7,5,8,8,7,3\n"
    )
    resp = client.post(
        "/products/import-csv",
        files={"file": ("products.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["source"] == "manual_csv"


@needs_db
def test_list_products_empty(client):
    resp = client.get("/products/")
    assert resp.status_code == 200
    assert resp.json() == []


@needs_db
def test_list_products_after_import(client):
    csv_content = (
        "name,category,pain_score,visual_score,demo_score,impulse_buy_score,"
        "trend_score,availability_score,commission_estimate,competition_score\n"
        "Produto A,Casa,8,9,10,8,7,8,3,5\n"
    )
    client.post(
        "/products/import-csv",
        files={"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")},
    )
    resp = client.get("/products/")
    assert resp.status_code == 200
    products = resp.json()
    assert len(products) == 1
    assert products[0]["name"] == "Produto A"
    assert products[0]["total_score"] > 0


@needs_db
def test_get_product_not_found(client):
    resp = client.get("/products/999")
    assert resp.status_code == 404
