"""
Feature engineering module for F1 telemetry data.
Computes per-driver metrics from telemetry DataFrames.
"""

import pandas as pd
from typing import Dict, Optional


def extract_features(
    driver_telemetry_dict: Dict[str, pd.DataFrame],
    laps: str = "fastest",
    weather_dict: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Build a feature matrix from per-driver telemetry DataFrames.

    Args:
        driver_telemetry_dict: dict of driver_code -> telemetry DataFrame.
        laps: "fastest" (5 base features) or "all" (per-lap mean/std + lap_count).
        weather_dict: optional dict with track_temp, air_temp, rainfall.

    Returns:
        DataFrame indexed by driver code.
    """
    rows = []
    for driver, telemetry in driver_telemetry_dict.items():
        gear_col = "nGear" if "nGear" in telemetry.columns else "Gear"

        if laps == "all" and "LapNumber" in telemetry.columns:
            per_lap = []
            for _, lap_data in telemetry.groupby("LapNumber"):
                ms = lap_data["Speed"].mean()
                mt = lap_data["Throttle"].mean()
                bf = lap_data["Brake"].mean()
                drs = lap_data["DRS"].mean() if "DRS" in lap_data.columns else 0.0
                per_lap.append({
                    "mean_speed": ms,
                    "mean_throttle": mt,
                    "brake_frequency": bf,
                    "aggression_index": (mt * bf) / max(ms, 1),
                    "mean_gear": lap_data[gear_col].mean(),
                    "drs_usage": drs,
                })
            lap_df = pd.DataFrame(per_lap)
            row = {
                "mean_speed_mean": lap_df["mean_speed"].mean(),
                "mean_speed_std": lap_df["mean_speed"].std(ddof=0),
                "mean_throttle_mean": lap_df["mean_throttle"].mean(),
                "mean_throttle_std": lap_df["mean_throttle"].std(ddof=0),
                "brake_frequency_mean": lap_df["brake_frequency"].mean(),
                "brake_frequency_std": lap_df["brake_frequency"].std(ddof=0),
                "aggression_index_mean": lap_df["aggression_index"].mean(),
                "aggression_index_std": lap_df["aggression_index"].std(ddof=0),
                "mean_gear_mean": lap_df["mean_gear"].mean(),
                "mean_gear_std": lap_df["mean_gear"].std(ddof=0),
                "drs_usage_mean": lap_df["drs_usage"].mean(),
                "drs_usage_std": lap_df["drs_usage"].std(ddof=0),
                "lap_count": len(lap_df),
            }
        else:
            mean_speed = telemetry["Speed"].mean()
            mean_throttle = telemetry["Throttle"].mean()
            brake_freq = telemetry["Brake"].mean()
            row = {
                "mean_speed": mean_speed,
                "mean_throttle": mean_throttle,
                "brake_frequency": brake_freq,
                "aggression_index": (mean_throttle * brake_freq) / max(mean_speed, 1),
                "mean_gear": telemetry[gear_col].mean(),
                "drs_usage": telemetry["DRS"].mean() if "DRS" in telemetry.columns else 0.0,
            }

        if weather_dict:
            row["track_temp"] = weather_dict.get("track_temp", 0.0)
            row["air_temp"] = weather_dict.get("air_temp", 0.0)
            row["rainfall"] = 1 if weather_dict.get("rainfall", False) else 0

        rows.append(row)

    return pd.DataFrame(rows, index=list(driver_telemetry_dict.keys()))
