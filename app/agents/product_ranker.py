"""Product Ranker — calcula score e seleciona produto vencedor da semana."""

import pandas as pd
from app.config import settings


def calculate_score(product: dict) -> float:
    """Calcula score ponderado para TikTok Shop."""
    score = (
        product.get("pain_score", 0) * settings.weight_pain
        + product.get("visual_score", 0) * settings.weight_visual
        + product.get("demo_score", 0) * settings.weight_demo
        + product.get("impulse_buy_score", 0) * settings.weight_impulse
        + product.get("trend_score", 0) * settings.weight_trend
        + product.get("availability_score", 0) * settings.weight_availability
        + product.get("commission_estimate", 0) * settings.weight_commission
        - product.get("competition_score", 0) * settings.weight_competition
    )
    return round(score, 2)


def select_winner(csv_path: str) -> dict:
    """Lê CSV, calcula scores e retorna o produto vencedor."""
    df = pd.read_csv(csv_path)
    df["score"] = df.apply(lambda row: calculate_score(row.to_dict()), axis=1)
    winner = df.sort_values("score", ascending=False).iloc[0]
    return {
        "id": str(winner["id"]),
        "name": winner["name"],
        "score": winner["score"],
        "category": winner.get("category", ""),
    }
