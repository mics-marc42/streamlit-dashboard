"""
Prediction model utilities.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, accuracy_score, classification_report
import pickle
import os
from typing import Optional, Tuple, Dict, Any

PRODUCT_UTILITY_SCORE = {
    "Utility": 3,
    "Semi-Utility": 2,
    "Non-Utility": 1
}

BRAND_SCORE = {
    "Established": 3,
    "Mid": 2,
    "New": 1
}

PARTICIPATION_RATE_BY_SCORE = {
    (7, 9): 0.80,
    (5, 6): 0.55,
    (3, 4): 0.30
}

PLATFORM_CONFIDENCE = {
    ("Review", "Paid"): 0.90,
    ("Instagram", "Paid"): 0.60,
    ("Instagram", "Barter"): 0.40
}
