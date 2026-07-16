"""
Lap time prediction module using MLPRegressor (neural network).
"""

import warnings
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


def train_lap_time_predictor(feature_df, target_times):
    """
    Train an MLPRegressor on driver features and target lap times.
    Returns dict with 'model' and 'scaler'.
    """
    scaler = StandardScaler()
    X = scaler.fit_transform(feature_df.values)
    model = MLPRegressor(hidden_layer_sizes=(32, 16), max_iter=5000, random_state=42)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=UserWarning)
        model.fit(X, target_times.values)
    return {"model": model, "scaler": scaler}


def predict_lap_time(model_pack, features):
    """Predict lap time from a feature vector using a trained model pack."""
    scaler = model_pack["scaler"]
    model = model_pack["model"]
    X = scaler.transform([features])
    return float(model.predict(X)[0])
