"""
Report generation module for F1 driver analysis.
Produces a formatted text summary from features and cluster labels.
"""

import pandas as pd
from typing import Dict, List, Tuple


def generate_report(
    feature_df: pd.DataFrame,
    style_labels: List[str],
    sector_times_dict: Dict[str, Tuple[float, float, float]],
) -> str:
    """Generate a formatted text report summarizing driver styles and performance."""
    lines = ["=" * 50, "F1 DRIVER ANALYSIS REPORT", "=" * 50, ""]
    for i, driver in enumerate(feature_df.index):
        lines.append(f"Driver: {driver}")
        lines.append(f"  Style Classification: {style_labels[i]}")
        lines.append(f"  Mean Speed: {feature_df.loc[driver, 'mean_speed']:.1f} km/h")
        lines.append(f"  Brake Frequency: {feature_df.loc[driver, 'brake_frequency']:.3f}")
        lines.append(f"  Aggression Index: {feature_df.loc[driver, 'aggression_index']:.3f}")
        if driver in sector_times_dict:
            s1, s2, s3 = sector_times_dict[driver]
            lines.append(f"  Sector Times: {s1:.2f}s / {s2:.2f}s / {s3:.2f}s")
        lines.append("")
    lines.append("=" * 50)
    return "\n".join(lines)
