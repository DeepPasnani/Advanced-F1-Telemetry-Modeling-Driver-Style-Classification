"""
Report generation module for F1 driver analysis.
Produces a formatted text summary from features and cluster labels.
"""

import pandas as pd
from typing import Dict, List, Tuple, Optional


def generate_report(
    feature_df: pd.DataFrame,
    style_labels: List[str],
    sector_times_dict: Dict[str, Tuple[float, float, float]],
    weather_dict: Optional[dict] = None,
) -> str:
    """Generate a formatted text report summarizing driver styles and performance."""
    lines = ["=" * 50, "F1 DRIVER ANALYSIS REPORT", "=" * 50, ""]
    for i, driver in enumerate(feature_df.index):
        lines.append(f"Driver: {driver}")
        lines.append(f"  Style Classification: {style_labels[i]}")

        if "mean_speed_mean" in feature_df.columns:
            lines.append(f"  Mean Speed: {feature_df.loc[driver, 'mean_speed_mean']:.1f} km/h")
            lines.append(f"  Speed Std Dev: {feature_df.loc[driver, 'mean_speed_std']:.1f} km/h")
            lines.append(f"  Brake Frequency: {feature_df.loc[driver, 'brake_frequency_mean']:.3f}")
            lines.append(f"  Aggression Index: {feature_df.loc[driver, 'aggression_index_mean']:.3f}")
            if "drs_usage_mean" in feature_df.columns:
                lines.append(f"  DRS Usage: {feature_df.loc[driver, 'drs_usage_mean']:.2%}")
        else:
            lines.append(f"  Mean Speed: {feature_df.loc[driver, 'mean_speed']:.1f} km/h")
            lines.append(f"  Brake Frequency: {feature_df.loc[driver, 'brake_frequency']:.3f}")
            lines.append(f"  Aggression Index: {feature_df.loc[driver, 'aggression_index']:.3f}")
            if "drs_usage" in feature_df.columns:
                lines.append(f"  DRS Usage: {feature_df.loc[driver, 'drs_usage']:.2%}")

        if driver in sector_times_dict:
            s1, s2, s3 = sector_times_dict[driver]
            lines.append(f"  Sector Times: {s1:.2f}s / {s2:.2f}s / {s3:.2f}s")

        if "lap_count" in feature_df.columns:
            lines.append(f"  Laps Analyzed: {int(feature_df.loc[driver, 'lap_count'])}")

        lines.append("")

    if weather_dict:
        lines.append("---")
        lines.append("Session Conditions:")
        lines.append(f"  Track Temp: {weather_dict.get('track_temp', 0):.1f}°C")
        lines.append(f"  Air Temp: {weather_dict.get('air_temp', 0):.1f}°C")
        lines.append(f"  Rainfall: {'Yes' if weather_dict.get('rainfall', False) else 'No'}")
        lines.append("")

    lines.append("=" * 50)
    return "\n".join(lines)
