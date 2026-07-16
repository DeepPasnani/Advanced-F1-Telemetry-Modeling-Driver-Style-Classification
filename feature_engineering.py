"""
Feature engineering module for F1 telemetry data.
Computes per-driver metrics from telemetry DataFrames.
"""

import pandas as pd
from typing import Dict


def extract_features(driver_telemetry_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build a feature matrix from per-driver telemetry DataFrames.

    Each row is a driver, columns are:
      - mean_speed
      - mean_throttle
      - brake_frequency
      - aggression_index (throttle * brake / speed)
      - mean_gear
    """
    rows = []
    for driver, telemetry in driver_telemetry_dict.items():
        mean_speed = telemetry["Speed"].mean()
        mean_throttle = telemetry["Throttle"].mean()
        brake_freq = telemetry["Brake"].mean()
        gear_col = "nGear" if "nGear" in telemetry.columns else "Gear"
        rows.append({
            "mean_speed": mean_speed,
            "mean_throttle": mean_throttle,
            "brake_frequency": brake_freq,
            "aggression_index": (mean_throttle * brake_freq) / max(mean_speed, 1),
            "mean_gear": telemetry[gear_col].mean(),
        })
    return pd.DataFrame(rows, index=list(driver_telemetry_dict.keys()))
