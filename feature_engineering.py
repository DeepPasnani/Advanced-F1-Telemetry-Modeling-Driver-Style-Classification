"""
Feature engineering module for extracting telemetry features from F1 data.

This module provides functions to:
- Extract telemetry features (mean_speed, max_speed, etc.)
- Compute acceleration from speed data
- Get sector times
- Build feature matrix for all drivers

TODO: Incorporate weather API data (wind speed, track temp, rainfall) as features (Future Work)
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional


def extract_features(telemetry_df: pd.DataFrame) -> Dict[str, float]:
    """
    Extract telemetry features from a telemetry DataFrame.

    Args:
        telemetry_df: DataFrame with Speed, Throttle, Brake, RPM, nGear columns

    Returns:
        Dictionary containing:
        - mean_speed: Average speed in km/h
        - max_speed: Maximum speed in km/h
        - mean_throttle: Average throttle percentage (0-100)
        - brake_frequency: Fraction of time with brake > 0
        - mean_rpm: Average RPM
        - mean_gear: Average gear
        - aggression_index: Combined aggression metric
    """
    if telemetry_df.empty:
        return {
            "mean_speed": 0.0,
            "max_speed": 0.0,
            "mean_throttle": 0.0,
            "brake_frequency": 0.0,
            "mean_rpm": 0.0,
            "mean_gear": 0.0,
            "aggression_index": 0.0
        }
    
    mean_speed = float(telemetry_df["Speed"].mean()) if "Speed" in telemetry_df.columns else 0.0
    max_speed = float(telemetry_df["Speed"].max()) if "Speed" in telemetry_df.columns else 0.0
    mean_throttle = float(telemetry_df["Throttle"].mean()) if "Throttle" in telemetry_df.columns else 0.0
    
    brake_column = telemetry_df["Brake"] if "Brake" in telemetry_df.columns else pd.Series([0])
    brake_frequency = float((brake_column > 0).sum() / len(telemetry_df)) if len(telemetry_df) > 0 else 0.0
    
    mean_rpm = float(telemetry_df["RPM"].mean()) if "RPM" in telemetry_df.columns else 0.0
    mean_gear = float(telemetry_df["nGear"].mean()) if "nGear" in telemetry_df.columns else 0.0
    
    aggression_index = (brake_frequency * 100) + (1 - mean_throttle / 100) * 50
    
    return {
        "mean_speed": mean_speed,
        "max_speed": max_speed,
        "mean_throttle": mean_throttle,
        "brake_frequency": brake_frequency,
        "mean_rpm": mean_rpm,
        "mean_gear": mean_gear,
        "aggression_index": aggression_index
    }


def compute_acceleration(telemetry_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add acceleration column to telemetry DataFrame using numpy gradient.

    Args:
        telemetry_df: DataFrame with Speed and Time columns

    Returns:
        DataFrame with added Acceleration column
    """
    telemetry_df = telemetry_df.copy()
    
    if "Speed" not in telemetry_df.columns or "Time" not in telemetry_df.columns:
        telemetry_df["Acceleration"] = 0.0
        return telemetry_df
    
    time_values = telemetry_df["Time"].values
    speed_values = telemetry_df["Speed"].values
    
    if len(time_values) > 1:
        acceleration = np.gradient(speed_values, time_values)
        telemetry_df["Acceleration"] = acceleration
    else:
        telemetry_df["Acceleration"] = 0.0
    
    telemetry_df["Acceleration"] = telemetry_df["Acceleration"].fillna(0).replace([np.inf, -np.inf], 0)
    
    return telemetry_df


def get_sector_times(lap) -> Tuple[float, float, float]:
    """
    Get sector times (S1, S2, S3) from a lap object.

    Args:
        lap: FastF1 Lap object

    Returns:
        Tuple of (sector1_time, sector2_time, sector3_time) in seconds
    """
    try:
        s1 = float(lap["Sector1Time"].total_seconds()) if pd.notna(lap.get("Sector1Time")) else 0.0
        s2 = float(lap["Sector2Time"].total_seconds()) if pd.notna(lap.get("Sector2Time")) else 0.0
        s3 = float(lap["Sector3Time"].total_seconds()) if pd.notna(lap.get("Sector3Time")) else 0.0
        return (s1, s2, s3)
    except Exception as e:
        print(f"Error getting sector times: {e}")
        return (0.0, 0.0, 0.0)


def build_feature_matrix(driver_telemetry_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build a feature matrix from driver telemetry dictionaries.

    Args:
        driver_telemetry_dict: Dictionary mapping driver codes to telemetry DataFrames

    Returns:
        DataFrame with one row per driver, columns = feature names
    """
    feature_rows = []
    
    for driver_code, telemetry in driver_telemetry_dict.items():
        features = extract_features(telemetry)
        features["driver"] = driver_code
        feature_rows.append(features)
    
    if not feature_rows:
        return pd.DataFrame()
    
    feature_df = pd.DataFrame(feature_rows)
    feature_df = feature_df.set_index("driver")
    
    return feature_df


def get_lap_duration(lap) -> float:
    """
    Get lap duration in seconds.

    Args:
        lap: FastF1 Lap object

    Returns:
        Lap duration in seconds
    """
    try:
        if pd.notna(lap.get("LapTime")):
            return float(lap["LapTime"].total_seconds())
        return 0.0
    except Exception:
        return 0.0


def get_all_laps_features(session, driver_codes: list) -> pd.DataFrame:
    """
    Build per-lap feature matrix across all selected drivers' laps.

    Args:
        session: FastF1 Session object
        driver_codes: List of driver codes to analyze

    Returns:
        DataFrame with per-lap features and lap duration
    """
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