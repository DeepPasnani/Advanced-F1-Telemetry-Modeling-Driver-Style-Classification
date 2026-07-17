"""
Visualization module for F1 telemetry data.

This module provides functions to generate and save plots:
- Speed traces for multiple drivers
- Throttle and brake traces
- Sector comparison bar charts
- Radar charts for driver profiles
- Cluster scatter plots using PCA

All plots are saved to output/ folder as PNG files.
"""

import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for server use
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Polygon
from typing import Dict


OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sns.set_theme(style="darkgrid")

DRIVER_COLORS = {
    "VER": "#3671C6",
    "HAM": "#27F4D2",
    "LEC": "#E8002D",
    "NOR": "#FF8000",
    "ALO": "#229971",
    "PER": "#3671C6",
    "SAI": "#E8002D",
    "RUS": "#27F4D2",
    "GAS": "#67C0F8",
    "TSU": "#67C0F8",
    "VET": "#209B96",
    "STR": "#209B96",
    "MAG": "#C92BE2",
    "ZHO": "#F5C1C1",
    "ALB": "#D7D7D7",
    "PIA": "#D7D7D7",
    "BOT": "#A7F3FC",
    "ZHO": "#F5C1C1",
    "RIC": "#229971",
    "DEV": "#FF8000",
}


def get_driver_color(driver_code: str) -> str:
    """Get the team color for a driver."""
    return DRIVER_COLORS.get(driver_code, "#888888")


def plot_speed_traces(driver_telemetry_dict: Dict[str, pd.DataFrame], driver_colors: Dict[str, str] = None) -> None:
    """
    Plot overlaid speed traces for all selected drivers.

    Args:
        driver_telemetry_dict: Dictionary mapping driver codes to telemetry DataFrames
        driver_colors: Optional dictionary mapping driver codes to colors
    """
    if not driver_telemetry_dict:
        print("No telemetry data to plot")
        return
    
    fig, ax = plt.subplots(figsize=(14, 8))
    
    for driver_code, telemetry in driver_telemetry_dict.items():
        if telemetry.empty or "Distance" not in telemetry.columns or "Speed" not in telemetry.columns:
            continue
        
        color = driver_colors.get(driver_code) if driver_colors else get_driver_color(driver_code)
        
        ax.plot(telemetry["Distance"], telemetry["Speed"], 
                label=driver_code, color=color, linewidth=2, alpha=0.8)
    
    ax.set_xlabel("Distance (m)", fontsize=12)
    ax.set_ylabel("Speed (km/h)", fontsize=12)
    ax.set_title("Speed Traces - Fastest Lap Comparison", fontsize=14, fontweight="bold")
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "speed_trace.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_throttle_brake(driver_telemetry_dict: Dict[str, pd.DataFrame]) -> None:
    """
    Plot side-by-side throttle and brake traces for each driver.

    Args:
        driver_telemetry_dict: Dictionary mapping driver codes to telemetry DataFrames
    """
    if not driver_telemetry_dict:
        print("No telemetry data to plot")
        return
    
    n_drivers = len(driver_telemetry_dict)
    fig, axes = plt.subplots(n_drivers, 2, figsize=(14, 4 * n_drivers), sharex=True)
    
    if n_drivers == 1:
        axes = axes.reshape(1, -1)
    
    for idx, (driver_code, telemetry) in enumerate(driver_telemetry_dict.items()):
        if telemetry.empty:
            continue
        
        color = get_driver_color(driver_code)
        
        if "Distance" in telemetry.columns:
            distance = telemetry["Distance"]
        else:
            distance = range(len(telemetry))
        
        if "Throttle" in telemetry.columns:
            axes[idx, 0].plot(distance, telemetry["Throttle"], 
                             color=color, linewidth=2, alpha=0.8)
            axes[idx, 0].set_ylabel("Throttle (%)", fontsize=10)
            axes[idx, 0].set_ylim(0, 105)
            axes[idx, 0].grid(True, alpha=0.3)
        
        if "Brake" in telemetry.columns:
            axes[idx, 1].plot(distance, telemetry["Brake"], 
                             color=color, linewidth=2, alpha=0.8)
            axes[idx, 1].set_ylabel("Brake", fontsize=10)
            axes[idx, 1].set_ylim(-0.1, 1.2)
            axes[idx, 1].grid(True, alpha=0.3)
        
        axes[idx, 0].set_title(f"{driver_code} - Throttle", fontsize=12, fontweight="bold")
        axes[idx, 1].set_title(f"{driver_code} - Brake", fontsize=12, fontweight="bold")
    
    axes[-1, 0].set_xlabel("Distance (m)", fontsize=10)
    axes[-1, 1].set_xlabel("Distance (m)", fontsize=10)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "throttle_brake.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_sector_comparison(sector_times_dict: Dict[str, tuple]) -> None:
    """
    Plot bar chart comparing sector times across drivers.

    Args:
        sector_times_dict: Dictionary mapping driver codes to (s1, s2, s3) tuples
    """
    if not sector_times_dict:
        print("No sector times to plot")
        return
    
    drivers = list(sector_times_dict.keys())
    s1_times = [sector_times_dict[d][0] for d in drivers]
    s2_times = [sector_times_dict[d][1] for d in drivers]
    s3_times = [sector_times_dict[d][2] for d in drivers]
    
    x = np.arange(len(drivers))
    width = 0.25
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    colors = [get_driver_color(d) for d in drivers]
    
    bars1 = ax.bar(x - width, s1_times, width, label="Sector 1", color="#FF6B6B", alpha=0.8)
    bars2 = ax.bar(x, s2_times, width, label="Sector 2", color="#4ECDC4", alpha=0.8)
    bars3 = ax.bar(x + width, s3_times, width, label="Sector 3", color="#45B7D1", alpha=0.8)
    
    ax.set_xlabel("Driver", fontsize=12)
    ax.set_ylabel("Time (seconds)", fontsize=12)
    ax.set_title("Sector Time Comparison", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(drivers, fontsize=10)
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis="y")
    
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(f"{height:.2f}",
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha="center", va="bottom", fontsize=8)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "sector_comparison.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_radar_chart(feature_df: pd.DataFrame, drivers: list) -> None:
    """
    Plot radar/spider chart showing normalized metrics per driver.

    Args:
        feature_df: DataFrame with driver features
        drivers: List of driver codes to plot
    """
    if feature_df.empty or not drivers:
        print("No feature data to plot")
        return
    
    categories = ["mean_speed", "mean_throttle", "brake_frequency", "aggression_index", "mean_gear"]
    available_categories = [cat for cat in categories if cat in feature_df.columns]
    
    if not available_categories:
        print("No valid categories for radar chart")
        return
    
    N = len(available_categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]
    
    fig = plt.figure(figsize=(12, 10))
    ax = fig.add_subplot(111, projection="polar")
    
    for driver in drivers:
        if driver not in feature_df.index:
            continue
        
        values = feature_df.loc[driver, available_categories].values.tolist()
        
        for i, val in enumerate(values):
            col_range = feature_df[available_categories[i]].max() - feature_df[available_categories[i]].min()
            if col_range > 0:
                values[i] = (val - feature_df[available_categories[i]].min()) / col_range
            else:
                values[i] = 0.5
        
        values += values[:1]
        
        color = get_driver_color(driver)
        ax.plot(angles, values, "o-", linewidth=2, label=driver, color=color, alpha=0.8)
        ax.fill(angles, values, alpha=0.25, color=color)
    
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([cat.replace("_", " ").title() for cat in available_categories], fontsize=10)
    ax.set_ylim(0, 1)
    ax.set_title("Driver Style Profile - Radar Chart", fontsize=14, pad=30, fontweight="bold")
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0), fontsize=10)
    ax.grid(True)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "radar_chart.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def plot_cluster_scatter(feature_df: pd.DataFrame, style_labels: list) -> None:
    """
    Plot 2D scatter using PCA on features, colored by cluster.

    Args:
        feature_df: DataFrame with driver features
        style_labels: List of style labels for each driver
    """
    if feature_df.empty or not style_labels:
        print("No data for cluster scatter plot")
        return
    
    from clustering import perform_pca
    
    X_pca, pca_model = perform_pca(feature_df)
    
    if X_pca is None or len(X_pca) == 0:
        print("PCA failed")
        return
    
    style_colors = {
        "Aggressive": "#FF4444",
        "Late Braker": "#4444FF",
        "Smooth Cornering": "#44FF44"
    }
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    for i, driver in enumerate(feature_df.index):
        color = style_colors.get(style_labels[i], "#888888")
        ax.scatter(X_pca[i, 0], X_pca[i, 1], 
                   c=color, s=200, alpha=0.8, edgecolors="black", linewidth=1)
        
        ax.annotate(str(driver), (X_pca[i, 0], X_pca[i, 1]),
                   xytext=(5, 5), textcoords="offset points",
                   fontsize=12, fontweight="bold")
    
    ax.set_xlabel("PC1", fontsize=12)
    ax.set_ylabel("PC2", fontsize=12)
    ax.set_title("Driver Clustering - PCA Visualization", fontsize=14, fontweight="bold")
    ax.grid(True, alpha=0.3)
    
    legend_elements = [plt.scatter([], [], c=color, s=150, label=style) 
                      for style, color in style_colors.items()]
    ax.legend(handles=legend_elements, loc="best", fontsize=10)
    
    plt.tight_layout()
    output_path = os.path.join(OUTPUT_DIR, "cluster_scatter.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")


def generate_all_visualizations(
    driver_telemetry_dict: Dict[str, pd.DataFrame],
    sector_times_dict: Dict[str, tuple],
    feature_df: pd.DataFrame,
    style_labels: list
) -> None:
    """
    Generate all visualization plots.

    Args:
        driver_telemetry_dict: Dictionary mapping driver codes to telemetry DataFrames
        sector_times_dict: Dictionary mapping driver codes to sector times
        feature_df: DataFrame with driver features
        style_labels: List of style labels
    """
    print("\n" + "="*50)
    print("Generating Visualizations...")
    print("="*50)
    
    driver_colors = {driver: get_driver_color(driver) for driver in driver_telemetry_dict.keys()}
    plot_speed_traces(driver_telemetry_dict, driver_colors)
    plot_throttle_brake(driver_telemetry_dict)
    plot_sector_comparison(sector_times_dict)
    
    drivers = list(feature_df.index)
    plot_radar_chart(feature_df, drivers)
    plot_cluster_scatter(feature_df, style_labels)
    
    print("="*50)
    print("All visualizations saved to output/")
    print("="*50)