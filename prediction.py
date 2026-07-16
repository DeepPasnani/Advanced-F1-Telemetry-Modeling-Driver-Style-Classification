"""
Lap time prediction module using RandomForest regression.
"""

import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler


def train_lap_time_predictor(feature_df, target_times):
    """
    Train a RandomForestRegressor on driver features and target lap times.
    Returns dict with 'model' and 'scaler'.
    """
    scaler = StandardScaler()
    X = scaler.fit_transform(feature_df.values)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, target_times.values)
    return {"model": model, "scaler": scaler}


def predict_lap_time(model_pack, features):
    """Predict lap time from a feature vector using a trained model pack."""
    scaler = model_pack["scaler"]
    model = model_pack["model"]
    X = scaler.transform([features])
    return float(model.predict(X)[0])
