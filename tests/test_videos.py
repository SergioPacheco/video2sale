import io
from unittest.mock import patch, AsyncMock


def _import_products(client):
    """Helper: importa produtos para usar nos testes."""
    csv = (
        "name,category,pain_score,visual_score,demo_score,impulse_buy_score,"
        "trend_score,availability_score,commission_estimate,competition_score\n"
        "Cortador,Cozinha,8,9,10,8,7,8,3,5\n"
        "Organizador,Casa,9,8,8,7,7,8,3,6\n"
    )
    client.post("/products/import-csv", files={"file": ("p.csv", io.BytesIO(csv.encode()), "text/csv")})


def test_weekly_winner(client):
    _import_products(client)
    resp = client.post("/weekly-winner", json={"week": "2026-W21"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["week"] == "2026-W21"
    assert data["score"] > 0
    assert "product" in data


def test_weekly_winner_no_products(client):
    resp = client.post("/weekly-winner", json={"week": "2026-W21"})
    assert resp.status_code == 404


def test_list_videos_empty(client):
    resp = client.get("/videos")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_videos_after_winner(client):
    _import_products(client)
    client.post("/weekly-winner", json={"week": "2026-W21"})
    resp = client.get("/videos")
    assert resp.status_code == 200
    videos = resp.json()
    assert len(videos) == 1
    assert videos[0]["status"] == "pending_creative"


def test_get_video_detail(client):
    _import_products(client)
    client.post("/weekly-winner", json={"week": "2026-W21"})
    videos = client.get("/videos").json()
    video_id = videos[0]["id"]
    resp = client.get(f"/videos/{video_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert "events" in data
    assert len(data["events"]) == 1
    assert data["events"][0]["event_type"] == "product_ranked"


def test_select_pack_not_found(client):
    resp = client.post("/videos/999/select-pack", params={"pack_id": 1})
    assert resp.status_code == 404


@patch("app.agents.script_agent._get_client")
def test_generate_creative(mock_get_client, client):
    """Testa geração de creative packs com OpenAI mockada."""
    _import_products(client)
    client.post("/weekly-winner", json={"week": "2026-W21"})
    videos = client.get("/videos").json()
    video_id = videos[0]["id"]

    mock_client = AsyncMock()
    mock_response = AsyncMock()
    mock_response.choices = [AsyncMock()]
    mock_response.choices[0].message.content = '{"packs": [{"hook": "Hook1", "scenes": [{"start":0,"end":3,"text":"T","voiceover":"V","visual":"Vis"}], "caption": "Cap", "hashtags": ["#t"]}, {"hook": "Hook2", "scenes": [{"start":0,"end":3,"text":"T2","voiceover":"V2","visual":"Vis2"}], "caption": "Cap2", "hashtags": ["#t2"]}, {"hook": "Hook3", "scenes": [{"start":0,"end":3,"text":"T3","voiceover":"V3","visual":"Vis3"}], "caption": "Cap3", "hashtags": ["#t3"]}]}'
    mock_response.usage = AsyncMock()
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 900
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    mock_get_client.return_value = mock_client

    resp = client.post(f"/videos/{video_id}/generate-creative")
    assert resp.status_code == 200
    packs = resp.json()
    assert len(packs) == 3
    assert packs[0]["hook"] == "Hook1"
