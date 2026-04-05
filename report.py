"""
Report generation module for F1 telemetry analysis.

This module provides functions to:
- Generate a structured text report
- Print to console
- Save to output/report.txt

The report includes:
- Session info (year, GP, session)
- Driver cluster assignments and style labels
- Sector time comparison table
- Feature table
- Lap time prediction results
- Strategy recommendations per driving style
"""

import os
import pandas as pd
from typing import Dict, Any, List, Tuple


OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_strategy_recommendation(style: str) -> str:
    """
    Get strategy recommendation based on driving style.

    Args:
        style: Driving style label

    Returns:
        Strategy recommendation string
    """
    recommendations = {
        "Aggressive": "Recommend softer compounds, shorter stints, aggressive undercut strategy",
        "Late Braker": "Recommend high-downforce setup, late-braking zones exploitation",
        "Smooth Cornering": "Recommend medium/hard compounds, longer stints, overcut strategy"
    }
    return recommendations.get(style, "No specific recommendation available")


def generate_report(
    session_info: Dict[str, Any],
    cluster_summary: pd.DataFrame,
    sector_times: Dict[str, Tuple[float, float, float]],
    feature_df: pd.DataFrame,
    prediction_results: Dict[str, Any],
    kmeans_styles: List[str],
    hierarchical_styles: List[str]
) -> str:
    """
    Generate a structured text report.

    Args:
        session_info: Dictionary with session information
        cluster_summary: DataFrame with cluster and style info
        sector_times: Dictionary mapping driver to (s1, s2, s3)
        feature_df: DataFrame with driver features
        prediction_results: Dictionary with prediction results
        kmeans_styles: List of KMeans style labels
        hierarchical_styles: List of Hierarchical style labels

    Returns:
        Complete report as string
    """
    lines = []
    
    lines.append("=" * 70)
    lines.append("           F1 TELEMETRY ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("SESSION INFORMATION")
    lines.append("-" * 70)
    lines.append(f"Year:           {session_info.get('year', 'N/A')}")
    lines.append(f"Grand Prix:     {session_info.get('gp', 'N/A')}")
    lines.append(f"Session Type:   {session_info.get('session_type', 'N/A')}")
    lines.append(f"Date:           {session_info.get('date', 'N/A')}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("DRIVER CLUSTER ASSIGNMENTS")
    lines.append("-" * 70)
    lines.append(f"{'Driver':<10} {'KMeans Style':<20} {'Hierarchical Style':<20}")
    lines.append("-" * 70)
    
    if not cluster_summary.empty:
        for i, driver in enumerate(cluster_summary.index):
            kmeans_style = kmeans_styles[i] if i < len(kmeans_styles) else "N/A"
            hier_style = hierarchical_styles[i] if i < len(hierarchical_styles) else "N/A"
            lines.append(f"{driver:<10} {kmeans_style:<20} {hier_style:<20}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("SECTOR TIME COMPARISON (in seconds)")
    lines.append("-" * 70)
    lines.append(f"{'Driver':<10} {'Sector 1':<12} {'Sector 2':<12} {'Sector 3':<12} {'Total':<12}")
    lines.append("-" * 70)
    
    for driver, (s1, s2, s3) in sector_times.items():
        total = s1 + s2 + s3
        lines.append(f"{driver:<10} {s1:<12.3f} {s2:<12.3f} {s3:<12.3f} {total:<12.3f}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("DRIVER FEATURES")
    lines.append("-" * 70)
    
    if not feature_df.empty:
        feature_cols = ["mean_speed", "max_speed", "mean_throttle", "brake_frequency",
                       "mean_rpm", "mean_gear", "aggression_index"]
        available_cols = [col for col in feature_cols if col in feature_df.columns]
        
        lines.append(f"{'Driver':<10}", end="")
        for col in available_cols:
            lines.append(f" {col:<18}", end="")
        lines.append("")
        lines.append("-" * (10 + 18 * len(available_cols)))
        
        for driver in feature_df.index:
            lines.append(f"{driver:<10}", end="")
            for col in available_cols:
                val = feature_df.loc[driver, col]
                lines.append(f" {val:<18.2f}", end="")
            lines.append("")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("LAP TIME PREDICTION RESULTS")
    lines.append("-" * 70)
    
    r2 = prediction_results.get("r2", 0.0)
    mae = prediction_results.get("mae", 0.0)
    lines.append(f"Model R² Score:  {r2:.4f}")
    lines.append(f"Mean Absolute Error: {mae:.3f} seconds")
    lines.append("")
    
    predicted_times = prediction_results.get("predicted_times", {})
    actual_times = prediction_results.get("actual_times", {})
    
    lines.append(f"{'Driver':<10} {'Actual Time (s)':<18} {'Predicted Time (s)':<20}")
    lines.append("-" * 50)
    
    for driver in predicted_times.keys():
        actual = actual_times.get(driver, 0.0)
        predicted = predicted_times[driver]
        lines.append(f"{driver:<10} {actual:<18.3f} {predicted:<20.3f}")
    lines.append("")
    
    lines.append("-" * 70)
    lines.append("STRATEGY RECOMMENDATIONS BY DRIVING STYLE")
    lines.append("-" * 70)
    
    style_recommendations = {
        "Aggressive": "Aggressive drivers tend to push harder and wear tires more. Recommendations:",
        "Late Braker": "Late Brakers maximize speed through corners. Recommendations:",
        "Smooth Cornering": "Smooth Cornering drivers maximize tire life. Recommendations:"
    }
    
    for style, description in style_recommendations.items():
        lines.append(f"\n{style}:")
        lines.append(f"  {description}")
        lines.append(f"  -> {get_strategy_recommendation(style)}")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("                    END OF REPORT")
    lines.append("=" * 70)
    
    report_text = "\n".join(lines)
    
    return report_text


def save_report(report_text: str, filename: str = "report.txt") -> None:
    """
    Save report to file.

    Args:
        report_text: Report content as string
        filename: Output filename
    """
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    with open(output_path, "w") as f:
        f.write(report_text)
    
    print(f"Report saved to: {output_path}")


def print_report(report_text: str) -> None:
    """
    Print report to console.

    Args:
        report_text: Report content as string
    """
    print(report_text)


def generate_and_save_report(
    session_info: Dict[str, Any],
    cluster_summary: pd.DataFrame,
    sector_times: Dict[str, Tuple[float, float, float]],
    feature_df: pd.DataFrame,
    prediction_results: Dict[str, Any],
    kmeans_styles: List[str],
    hierarchical_styles: List[str]
) -> str:
    """
    Generate, print, and save the report.

    Args:
        session_info: Dictionary with session information
        cluster_summary: DataFrame with cluster and style info
        sector_times: Dictionary mapping driver to (s1, s2, s3)
        feature_df: DataFrame with driver features
        prediction_results: Dictionary with prediction results
        kmeans_styles: List of KMeans style labels
        hierarchical_styles: List of Hierarchical style labels

    Returns:
        Complete report as string
    """
    print("\n" + "=" * 70)
    print("GENERATING REPORT...")
    print("=" * 70)
    
    report_text = generate_report(
        session_info,
        cluster_summary,
        sector_times,
        feature_df,
        prediction_results,
        kmeans_styles,
        hierarchical_styles
    )
    
    print_report(report_text)
    save_report(report_text)
    
    print("\n" + "=" * 70)
    print("REPORT GENERATION COMPLETE")
    print("=" * 70)
    
    return report_text
