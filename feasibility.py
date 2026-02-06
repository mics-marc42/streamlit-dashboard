from predictor import (
    PRODUCT_UTILITY_SCORE,
    BRAND_SCORE,
    PARTICIPATION_RATE_BY_SCORE,
    PLATFORM_CONFIDENCE
)

def get_participation_rate(score):
    for (low, high), rate in PARTICIPATION_RATE_BY_SCORE.items():
        if low <= score <= high:
            return rate
    return 0.2

def calculate_feasibility(
    eligible_users: int,
    product_category: str,
    brand_strength: str,
    campaign_type: str,
    incentive_type: str
):
    score = (
        PRODUCT_UTILITY_SCORE[product_category] +
        BRAND_SCORE[brand_strength]
    )

    participation_rate = get_participation_rate(score)
    platform_confidence = PLATFORM_CONFIDENCE[(campaign_type, incentive_type)]

    max_safe_volume = int(
        eligible_users *
        participation_rate *
        platform_confidence
    )

    confidence_pct = int(participation_rate * platform_confidence * 100)

    return {
        "score": score,
        "participation_rate": participation_rate,
        "platform_confidence": platform_confidence,
        "max_safe_volume": max_safe_volume,
        "confidence_pct": confidence_pct
    }
