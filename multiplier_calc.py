"""
Multiplier calculation for collaboration predictions.
Edit this file to adjust multiplier logic.
"""
from typing import Optional


# Default safety number - adjust this value as needed
DEFAULT_SAFETY_NUMBER = 0.09


def calculate_multiplier(
    product_desirability: Optional[float] = None,
    average_price: Optional[float] = None,
    utility_score: Optional[float] = None,
    default_safety: float = DEFAULT_SAFETY_NUMBER
) -> float:
    """
    Calculate multiplier based on product desirability, average price, utility score, and safety number.
    
    Args:
        product_desirability: Product desirability score (out of 10)
        average_price: Average product price
        utility_score: Utility score (out of 10)
        default_safety: Default safety multiplier (default: 0.7)
    
    Returns:
        Calculated multiplier value
    """
    multiplier = default_safety
    
    # Normalize product desirability (0-10 scale to 0-1)
    if product_desirability is not None:
        desirability_factor = product_desirability /10.0
        multiplier += (0.35 * desirability_factor)  # Weight: 0.5 to 1.0
    
    # Normalize utility score (0-10 scale to 0-1)
    if utility_score is not None:
        utility_factor = utility_score / 10.0
        multiplier += (0.35 * utility_factor)  # Weight: 0.5 to 1.0
    
    # Price factor - range-based model
    if average_price is not None:
        if average_price < 100:
            price_factor = 0.5
        elif 100 <= average_price < 200:
            price_factor = 0.6
        elif 200 <= average_price < 300:
            price_factor = 0.7
        elif 300 <= average_price < 400:
            price_factor = 0.8
        elif 400 <= average_price <= 1000:
            price_factor = 0.9
        else:  # > 1000
            price_factor = 0.75
        multiplier += (0.2 * price_factor) 
    
    return multiplier - 0.1

def calculate_collaborations(
    filtered_count: int,
    product_desirability: Optional[float] = None,
    average_price: Optional[float] = None,
    utility_score: Optional[float] = None,
    default_safety: float = DEFAULT_SAFETY_NUMBER
) -> dict:
    """
    Calculate total number of collaborations that can be executed.
    
    Args:
        filtered_count: Number of filtered results from BigQuery
        product_desirability: Product desirability score (out of 10)
        average_price: Average product price
        utility_score: Utility score (out of 10)
        default_safety: Default safety multiplier
    
    Returns:
        Dictionary with multiplier and total collaborations
    """
    multiplier = calculate_multiplier(
        product_desirability=product_desirability,
        average_price=average_price,
        utility_score=utility_score,
        default_safety=default_safety
    )
    
    total_collaborations = int(filtered_count * multiplier)
    
    return {
        "filtered_count": filtered_count,
        "multiplier": multiplier,
        "total_collaborations": total_collaborations,
        "product_desirability": product_desirability,
        "average_price": average_price,
        "utility_score": utility_score,
        "default_safety": default_safety
    }
