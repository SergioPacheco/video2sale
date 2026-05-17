import io
from unittest.mock import patch, AsyncMock

import pytest

needs_db = pytest.mark.skipif(
    True, reason="Testes de integração requerem PostgreSQL (docker compose up)"
)


def _import_products(client):
    """Helper: importa produtos para usar nos testes."""
    csv = (
        "name,category,pain_score,visual_score,demo_score,impulse_buy_score,"
        "trend_score,availability_score,commission_estimate,competition_score\n"
        "Cortador,Cozinha,8,9,10,8,7,8,3,5\n"
        "Organizador,Casa,9,8,8,7,7,8,3,6\n"
    )
    client.post("/products/import-csv", files={"file": ("p.csv", io.BytesIO(csv.encode()), "text/csv")})


@needs_db
def test_weekly_winner(client):
    _import_products(client)
    resp = client.post("/weekly-winner", json={"week": "2026-W21"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["week"] == "2026-W21"
    assert data["score"] > 0
    assert "product" in data


@needs_db
def test_weekly_winner_no_products(client):
    resp = client.post("/weekly-winner", json={"week": "2026-W21"})
    assert resp.status_code == 404


@needs_db
def test_list_videos_empty(client):
    resp = client.get("/videos")
    assert resp.status_code == 200
    assert resp.json() == []


@needs_db
def test_list_videos_after_winner(client):
    _import_products(client)
    client.post("/weekly-winner", json={"week": "2026-W21"})
    resp = client.get("/videos")
    assert resp.status_code == 200
    videos = resp.json()
    assert len(videos) == 1
    assert videos[0]["status"] == "pending_creative"


@needs_db
def test_get_video_detail(client):
    _import_products(client)
    client.post("/weekly-winner", json={"week": "2026-W21"})
    resp = client.get("/videos/1")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert "events" in data
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "product_ranked"


@needs_db
def test_select_pack_not_found(client):
    resp = client.post("/videos/999/select-pack", params={"pack_id": 1})
    assert resp.status_code == 404


@patch("app.agents.script_agent.client")
@needs_db
def test_generate_creative(mock_openai, client):
    """Testa geração de creative packs com OpenAI mockada."""
    _import_products(client)
    client.post("/weekly-winner", json={"week": "2026-W21"})

    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '''{"packs": [
        {"hook": "¿Sigues cortando así?", "scenes": [{"start":0,"end":3,"text":"Hook","voiceover":"Hook","visual":"Close up"}], "caption": "Test", "hashtags": ["#test"]},
        {"hook": "Variación 2", "scenes": [{"start":0,"end":3,"text":"V2","voiceover":"V2","visual":"Wide"}], "caption": "Test2", "hashtags": ["#v2"]},
        {"hook": "Variación 3", "scenes": [{"start":0,"end":3,"text":"V3","voiceover":"V3","visual":"Medium"}], "caption": "Test3", "hashtags": ["#v3"]}
    ]}'''
    mock_response.usage = AsyncMock()
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 900

    mock_openai.chat.completions.create = AsyncMock(return_value=mock_response)

    resp = client.post("/videos/1/generate-creative")
    assert resp.status_code == 200
    packs = resp.json()
    assert len(packs) == 3
    assert packs[0]["hook"] == "¿Sigues cortando así?"
