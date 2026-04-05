"""
Background pipeline service for running ML analysis.
"""

import io
import base64
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import data_loader
import feature_engineering
import clustering
import prediction
import visualization
import report as report_module

import matplotlib.pyplot as plt
import seaborn as sns

from server.cache import job_store


executor = ThreadPoolExecutor(max_workers=1)


def figure_to_base64(fig) -> str:
    """Convert matplotlib figure to base64 PNG."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    plt.close(fig)
    return img_base64


def run_analysis(job_id: str, year: int, gp: str, session: str, driver_codes: list) -> None:
    """Run the full analysis pipeline in background thread."""
    try:
        job_store.update_job(job_id, "running", 5, "Loading session...")
        
        data_loader.enable_cache(cache_dir="./cache")
        session_obj = data_loader.load_session(year, gp, session)
        
        job_store.update_job(job_id, "running", 20, "Fetching telemetry...")
        
        driver_telemetry = {}
        sector_times_dict = {}
        skipped_drivers = []
        
        for i, driver_code in enumerate(driver_codes):
            try:
                fastest_lap = data_loader.get_driver_fastest_lap(session_obj, driver_code)
                
                if fastest_lap is None:
                    skipped_drivers.append(driver_code)
                    continue
                
                telemetry = data_loader.get_lap_telemetry(fastest_lap)
                
                if telemetry.empty:
                    skipped_drivers.append(driver_code)
                    continue
                
                driver_telemetry[driver_code] = telemetry
                s1, s2, s3 = feature_engineering.get_sector_times(fastest_lap)
                sector_times_dict[driver_code] = (s1, s2, s3)
                
            except Exception as e:
                print(f"Error processing {driver_code}: {e}")
                skipped_drivers.append(driver_code)
                continue
        
        if not driver_telemetry:
            raise ValueError("No valid driver data collected")
        
        job_store.update_job(job_id, "running", 40, "Engineering features...")
        
        feature_df = feature_engineering.build_feature_matrix(driver_telemetry)
        
        job_store.update_job(job_id, "running", 60, "Clustering drivers...")
        
        kmeans_labels = clustering.cluster_drivers(feature_df, method="kmeans")
        kmeans_styles = clustering.assign_style_labels(feature_df, kmeans_labels)
        
        hierarchical_labels = clustering.cluster_drivers(feature_df, method="agglomerative")
        hierarchical_styles = clustering.assign_style_labels(feature_df, hierarchical_labels)
        
        job_store.update_job(job_id, "running", 75, "Training prediction model...")
        
        valid_drivers = list(driver_telemetry.keys())
        lap_data = feature_engineering.get_all_laps_features(session_obj, valid_drivers)
        
        prediction_results = {"r2": 0.0, "mae": 0.0, "predicted_times": {}, "actual_times": {}}
        model = None
        
        if not lap_data.empty and len(lap_data) > 2:
            X = lap_data[["mean_speed", "mean_throttle", "brake_frequency", "mean_rpm", "mean_gear"]]
            y = lap_data["lap_duration"]
            model, r2, mae = prediction.train_lap_time_model(X, y)
            
            prediction_results = {"r2": r2, "mae": mae, "predicted_times": {}, "actual_times": {}}
            
            for driver in feature_df.index:
                try:
                    pred_time = prediction.predict_driver_lap_time(model, feature_df.loc[driver])
                    prediction_results["predicted_times"][driver] = pred_time
                except:
                    continue
        else:
            for driver in feature_df.index:
                prediction_results["predicted_times"][driver] = 0.0
        
        job_store.update_job(job_id, "running", 85, "Generating visualizations...")
        
        import matplotlib.pyplot as plt
        import seaborn as sns
        sns.set_theme(style="darkgrid")
        
        plots = {}
        
        driver_colors = {driver: visualization.get_driver_color(driver) for driver in driver_telemetry.keys()}
        
        fig = plt.figure(figsize=(14, 8))
        ax = plt.gca()
        for driver_code, telemetry in driver_telemetry.items():
            if not telemetry.empty and "Distance" in telemetry.columns and "Speed" in telemetry.columns:
                color = driver_colors.get(driver_code, "#888888")
                ax.plot(telemetry["Distance"], telemetry["Speed"], label=driver_code, color=color, linewidth=2, alpha=0.8)
        ax.set_xlabel("Distance (m)", fontsize=12)
        ax.set_ylabel("Speed (km/h)", fontsize=12)
        ax.set_title("Speed Traces - Fastest Lap Comparison", fontsize=14, fontweight="bold")
        ax.legend(loc="upper right", fontsize=10)
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plots["speed_trace"] = figure_to_base64(fig)
        
        n_drivers = len(driver_telemetry)
        fig, axes = plt.subplots(n_drivers, 2, figsize=(14, 4 * max(n_drivers, 1)), sharex=True)
        if n_drivers == 1:
            axes = axes.reshape(1, -1)
        for idx, (driver_code, telemetry) in enumerate(driver_telemetry.items()):
            color = driver_colors.get(driver_code, "#888888")
            distance = telemetry["Distance"].values if "Distance" in telemetry.columns else range(len(telemetry))
            if "Throttle" in telemetry.columns:
                axes[idx, 0].plot(distance, telemetry["Throttle"], color=color, linewidth=2, alpha=0.8)
                axes[idx, 0].set_ylabel("Throttle (%)", fontsize=10)
                axes[idx, 0].set_ylim(0, 105)
                axes[idx, 0].grid(True, alpha=0.3)
            if "Brake" in telemetry.columns:
                axes[idx, 1].plot(distance, telemetry["Brake"], color=color, linewidth=2, alpha=0.8)
                axes[idx, 1].set_ylabel("Brake", fontsize=10)
                axes[idx, 1].set_ylim(-0.1, 1.2)
                axes[idx, 1].grid(True, alpha=0.3)
            axes[idx, 0].set_title(f"{driver_code} - Throttle", fontsize=12, fontweight="bold")
            axes[idx, 1].set_title(f"{driver_code} - Brake", fontsize=12, fontweight="bold")
        if n_drivers > 0:
            axes[-1, 0].set_xlabel("Distance (m)", fontsize=10)
            axes[-1, 1].set_xlabel("Distance (m)", fontsize=10)
        plt.tight_layout()
        plots["throttle_brake"] = figure_to_base64(fig)
        
        drivers = list(sector_times_dict.keys())
        s1_times = [sector_times_dict[d][0] for d in drivers]
        s2_times = [sector_times_dict[d][1] for d in drivers]
        s3_times = [sector_times_dict[d][2] for d in drivers]
        x = np.arange(len(drivers))
        width = 0.25
        fig, ax = plt.subplots(figsize=(12, 8))
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
        plt.tight_layout()
        plots["sector_comparison"] = figure_to_base64(fig)
        
        import numpy as np
        categories = ["mean_speed", "mean_throttle", "brake_frequency", "aggression_index", "mean_gear"]
        available_categories = [cat for cat in categories if cat in feature_df.columns]
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
            color = driver_colors.get(driver, "#888888")
            ax.plot(angles, values, "o-", linewidth=2, label=driver, color=color, alpha=0.8)
            ax.fill(angles, values, alpha=0.25, color=color)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels([cat.replace("_", " ").title() for cat in available_categories], fontsize=10)
        ax.set_ylim(0, 1)
        ax.set_title("Driver Style Profile - Radar Chart", fontsize=14, pad=30, fontweight="bold")
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.0), fontsize=10)
        ax.grid(True)
        plt.tight_layout()
        plots["radar_chart"] = figure_to_base64(fig)
        
        X_pca, _ = clustering.perform_pca(feature_df)
        style_colors = {"Aggressive": "#FF4444", "Late Braker": "#4444FF", "Smooth Cornering": "#44FF44"}
        fig, ax = plt.subplots(figsize=(12, 8))
        for i, driver in enumerate(feature_df.index):
            color = style_colors.get(kmeans_styles[i], "#888888")
            ax.scatter(X_pca[i, 0], X_pca[i, 1], c=color, s=200, alpha=0.8, edgecolors="black", linewidth=1)
            ax.annotate(driver, (X_pca[i, 0], X_pca[i, 1]), xytext=(5, 5), textcoords="offset points", fontsize=12, fontweight="bold")
        ax.set_xlabel("PC1", fontsize=12)
        ax.set_ylabel("PC2", fontsize=12)
        ax.set_title("Driver Clustering - PCA Visualization", fontsize=14, fontweight="bold")
        ax.grid(True, alpha=0.3)
        legend_elements = [plt.scatter([], [], c=color, s=150, label=style) for style, color in style_colors.items()]
        ax.legend(handles=legend_elements, loc="best", fontsize=10)
        plt.tight_layout()
        plots["cluster_scatter"] = figure_to_base64(fig)
        
        job_store.update_job(job_id, "running", 95, "Building report...")
        
        session_info = {"year": year, "gp": gp, "session_type": session, "date": f"{year} {gp} {session}"}
        
        cluster_summary = clustering.get_cluster_summary(feature_df, kmeans_styles)
        
        if skipped_drivers:
            warning_note = f"\n\nWARNING: Skipped drivers (no data): {', '.join(skipped_drivers)}"
        else:
            warning_note = ""
        
        report_text = report_module.generate_report(
            session_info, cluster_summary, sector_times_dict, feature_df,
            prediction_results, kmeans_styles, hierarchical_styles
        ) + warning_note
        
        features_dict = {}
        for driver in feature_df.index:
            features_dict[driver] = {
                "mean_speed": float(feature_df.loc[driver, "mean_speed"]),
                "max_speed": float(feature_df.loc[driver, "max_speed"]),
                "mean_throttle": float(feature_df.loc[driver, "mean_throttle"]),
                "brake_frequency": float(feature_df.loc[driver, "brake_frequency"]),
                "mean_rpm": float(feature_df.loc[driver, "mean_rpm"]),
                "mean_gear": float(feature_df.loc[driver, "mean_gear"]),
                "aggression_index": float(feature_df.loc[driver, "aggression_index"])
            }
        
        result = {
            "session_info": session_info,
            "drivers": list(feature_df.index),
            "features": features_dict,
            "clusters": {
                "kmeans": dict(zip(feature_df.index, kmeans_styles)),
                "hierarchical": dict(zip(feature_df.index, hierarchical_styles))
            },
            "sector_times": {
                driver: {"s1": s1, "s2": s2, "s3": s3}
                for driver, (s1, s2, s3) in sector_times_dict.items()
            },
            "lap_time_prediction": prediction_results,
            "plots": plots,
            "report_text": report_text
        }
        
        job_store.set_result(job_id, result)
        
    except Exception as e:
        import traceback
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        job_store.set_error(job_id, error_msg)
        print(f"Job {job_id} failed: {error_msg}")


def start_analysis(year: int, gp: str, session: str, drivers: list) -> str:
    """Start an analysis job and return job_id."""
    job_id = job_store.create_job()
    executor.submit(run_analysis, job_id, year, gp, session, drivers)
    return job_id