"""
Generates short, data-driven captions explaining what each plot actually
shows for one specific analysis — an interpretation of the selected
drivers' real numbers, not a generic description of the chart type.
"""

from typing import Dict, List, Tuple
import pandas as pd


def _metric_col(feature_df: pd.DataFrame, base: str) -> str:
    """extract_features(laps="all") suffixes columns with "_mean"; fall
    back to the bare name for the single-lap feature set."""
    return f"{base}_mean" if f"{base}_mean" in feature_df.columns else base


def _extreme(feature_df: pd.DataFrame, drivers: List[str], base: str, mode: str = "max") -> Tuple[str, float]:
    col = _metric_col(feature_df, base)
    if col not in feature_df.columns:
        return None, None
    values = [(d, feature_df.loc[d, col]) for d in drivers if d in feature_df.index]
    values = [(d, v) for d, v in values if pd.notna(v)]
    if not values:
        return None, None
    pick = max if mode == "max" else min
    return pick(values, key=lambda x: x[1])


def generate_plot_insights(
    feature_df: pd.DataFrame,
    style_labels: List[str],
    sector_times_dict: Dict[str, tuple],
) -> Dict[str, str]:
    """Returns one caption per plot name, describing what actually happened
    in this analysis rather than what the chart type shows in general."""
    drivers = list(feature_df.index)
    styles = dict(zip(drivers, style_labels))
    insights: Dict[str, str] = {}

    # ── cluster_scatter ──
    groups: Dict[str, list] = {}
    for d in drivers:
        groups.setdefault(styles[d], []).append(d)
    group_parts = [f"{', '.join(codes)} as {style}" for style, codes in groups.items()]
    insights["cluster_scatter"] = f"In this session, drivers cluster {'; '.join(group_parts)}."

    # ── radar_chart ──
    fastest_d, fastest_v = _extreme(feature_df, drivers, "mean_speed", "max")
    aggr_d, aggr_v = _extreme(feature_df, drivers, "aggression_index", "max")
    smooth_d, _ = _extreme(feature_df, drivers, "aggression_index", "min")
    parts = []
    if fastest_d:
        parts.append(f"{fastest_d} carries the highest average speed")
    if aggr_d and aggr_d != fastest_d:
        parts.append(f"{aggr_d} posts the highest aggression index")
    if smooth_d and smooth_d not in (fastest_d, aggr_d):
        parts.append(f"{smooth_d} shows the smoothest inputs")
    insights["radar_chart"] = (
        f"{', '.join(parts)} among the drivers shown here." if parts
        else "Not enough data to compare driver profiles in this session."
    )

    # ── speed_trace ──
    if fastest_d:
        slow_d, slow_v = _extreme(feature_df, drivers, "mean_speed", "min")
        insights["speed_trace"] = (
            f"{fastest_d} posts the highest mean lap speed ({fastest_v:.1f} km/h) among these drivers"
            + (f", {slow_d} the lowest ({slow_v:.1f} km/h)." if slow_d and slow_d != fastest_d else ".")
        )
    else:
        insights["speed_trace"] = "Speed data wasn't available for these drivers in this session."

    # ── throttle_brake ──
    brake_hi_d, brake_hi_v = _extreme(feature_df, drivers, "brake_frequency", "max")
    brake_lo_d, brake_lo_v = _extreme(feature_df, drivers, "brake_frequency", "min")
    if brake_hi_d:
        insights["throttle_brake"] = (
            f"{brake_hi_d} brakes most often ({brake_hi_v:.0%} of the lap) in this session"
            + (f", {brake_lo_d} least ({brake_lo_v:.0%})." if brake_lo_d and brake_lo_d != brake_hi_d else ".")
        )
    else:
        insights["throttle_brake"] = "Brake data wasn't available for these drivers in this session."

    # ── sector_comparison ──
    sector_winners = []
    for i, name in enumerate(["Sector 1", "Sector 2", "Sector 3"]):
        candidates = [
            (d, sector_times_dict[d][i])
            for d in drivers
            if d in sector_times_dict and sector_times_dict[d][i] is not None
        ]
        if candidates:
            winner, _ = min(candidates, key=lambda x: x[1])
            sector_winners.append(f"{winner} set the fastest {name}")
    insights["sector_comparison"] = (
        f"{', '.join(sector_winners)} among these drivers." if sector_winners
        else "Sector time data wasn't available for these drivers in this session."
    )

    return insights
