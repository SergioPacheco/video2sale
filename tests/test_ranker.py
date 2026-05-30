from app.agents.product_ranker import calculate_score


def test_calculate_score_basic():
    product = {
        "pain_score": 8, "visual_score": 9, "demo_score": 10,
        "impulse_buy_score": 8, "trend_score": 7, "availability_score": 8,
        "commission_estimate": 3, "competition_score": 5,
    }
    score = calculate_score(product)
    assert score > 0
    assert isinstance(score, float)


def test_calculate_score_zeros():
    product = {
        "pain_score": 0, "visual_score": 0, "demo_score": 0,
        "impulse_buy_score": 0, "trend_score": 0, "availability_score": 0,
        "commission_estimate": 0, "competition_score": 0,
    }
    assert calculate_score(product) == 0.0


def test_calculate_score_high_competition_reduces():
    base = {
        "pain_score": 5, "visual_score": 5, "demo_score": 5,
        "impulse_buy_score": 5, "trend_score": 5, "availability_score": 5,
        "commission_estimate": 5, "competition_score": 0,
    }
    high_comp = {**base, "competition_score": 10}

    score_low = calculate_score(base)
    score_high = calculate_score(high_comp)
    assert score_low > score_high
