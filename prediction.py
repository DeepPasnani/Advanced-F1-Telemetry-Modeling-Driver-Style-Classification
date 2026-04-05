"""
Lap time prediction module using RandomForestRegressor.

This module provides functions to:
- Prepare lap features from session data
- Train RandomForest model
- Predict lap times for drivers

TODO: Replace RandomForest with LSTM/Transformer for deep learning lap prediction (Future Work)
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error
from typing import Tuple, Optional, Dict, Any
import fastf1


def prepare_lap_features(session: fastf1.core.Session, driver_codes: list) -> pd.DataFrame:
    """
    Build per-lap feature matrix across all selected drivers' laps.

    Args:
        session: FastF1 Session object
        driver_codes: List of driver codes to analyze

    Returns:
        DataFrame with per-lap features and lap duration
    """
    from feature_engineering import extract_features, get_lap_duration, get_sector_times
    
    all_laps_data = []
    
    for driver_code in driver_codes:
        try:
            driver_laps = session.laps[session.laps["Driver"] == driver_code].pick_valid()
            
            for _, lap in driver_laps.iterrows():
                try:
                    telemetry = lap.get_car_data()
                    if telemetry.empty:
                        continue
                    
                    features = extract_features(telemetry)
                    features["driver"] = driver_code
                    features["lap_duration"] = get_lap_duration(lap)
                    
                    s1, s2, s3 = get_sector_times(lap)
                    features["sector_1"] = s1
                    features["sector_2"] = s2
                    features["sector_3"] = s3
                    
                    all_laps_data.append(features)
                except Exception:
                    continue
        except Exception as e:
            print(f"Error processing laps for {driver_code}: {e}")
            continue
    
    if not all_laps_data:
        return pd.DataFrame()
    
    return pd.DataFrame(all_laps_data)


def train_lap_time_model(X: pd.DataFrame, y: pd.Series) -> Tuple[RandomForestRegressor, float, float]:
    """
    Train a RandomForestRegressor to predict lap times.

    Args:
        X: Feature DataFrame
        y: Target lap duration Series

    Returns:
        Tuple of (trained_model, r2_score, mean_absolute_error)
    """
    if len(X) < 2 or len(y) < 2:
        return None, 0.0, 0.0
    
    feature_cols = ["mean_speed", "mean_throttle", "brake_frequency", "mean_rpm", "mean_gear"]
    available_cols = [col for col in feature_cols if col in X.columns]
    
    if not available_cols:
        return None, 0.0, 0.0
    
    X_train = X[available_cols].fillna(0)
    y_train = y.fillna(0)
    
    model = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_train)
    
    r2 = r2_score(y_train, y_pred)
    mae = mean_absolute_error(y_train, y_pred)
    
    return model, r2, mae


def predict_driver_lap_time(model: RandomForestRegressor, driver_feature_vector: pd.Series) -> float:
    """
    Predict lap time for a driver's feature profile.

    Args:
        model: Trained RandomForestRegressor
        driver_feature_vector: Series with driver features

    Returns:
        Predicted lap time in seconds
    """
    if model is None:
        return 0.0
    
    feature_cols = ["mean_speed", "mean_throttle", "brake_frequency", "mean_rpm", "mean_gear"]
    available_cols = [col for col in feature_cols if col in driver_feature_vector.index]
    
    if not available_cols:
        return 0.0
    
    X = driver_feature_vector[available_cols].fillna(0).values.reshape(1, -1)
    
    predicted_time = model.predict(X)[0]
    
    return float(predicted_time)


def get_prediction_results(feature_df: pd.DataFrame, lap_data: pd.DataFrame, model: RandomForestRegressor) -> Dict[str, Any]:
    """
    Get prediction results for all drivers in the feature DataFrame.

    Args:
        feature_df: DataFrame with driver features
        lap_data: DataFrame with lap-level data
        model: Trained RandomForestRegressor

    Returns:
        Dictionary with prediction results
    """
    results = {
        "predicted_times": {},
        "actual_times": {},
        "r2": 0.0,
        "mae": 0.0
    }
    
    if model is None or feature_df.empty:
        return results
    
    for driver in feature_df.index:
        try:
            driver_features = feature_df.loc[driver]
            predicted_time = predict_driver_lap_time(model, driver_features)
            results["predicted_times"][driver] = predicted_time
            
            driver_laps = lap_data[lap_data["driver"] == driver]
            if not driver_laps.empty:
                actual_time = driver_laps["lap_duration"].min()
                results["actual_times"][driver] = actual_time
        except Exception as e:
            print(f"Error predicting for {driver}: {e}")
            continue
    
    return results
