"""
Main pipeline for F1 Telemetry Analysis.

This module runs the complete pipeline:
1. Setup - Enable FastF1 cache
2. Data Collection - Load race session, fetch driver fastest laps
3. Feature Engineering - Extract telemetry features
4. Clustering - KMeans and Hierarchical clustering
5. Lap Time Prediction - RandomForestRegressor
6. Visualization - Generate all plots
7. Report - Generate comprehensive report

Defaults:
- Year: 2023
- Grand Prix: Monza
- Session: Race (R)
- Drivers: VER, HAM, LEC, NOR, ALO
"""

import os
import warnings
import pandas as pd

os.makedirs("output", exist_ok=True)
os.makedirs("cache", exist_ok=True)

warnings.filterwarnings("ignore")

import data_loader
import feature_engineering
import clustering
import prediction
import visualization
import report


DEFAULT_YEAR = 2023
DEFAULT_GP = "Monza"
DEFAULT_SESSION = "R"
DEFAULT_DRIVERS = ["VER", "HAM", "LEC", "NOR", "ALO"]


def run_pipeline(
    year: int = DEFAULT_YEAR,
    gp: str = DEFAULT_GP,
    session_type: str = DEFAULT_SESSION,
    driver_codes: list = None
) -> None:
    """
    Run the complete F1 telemetry analysis pipeline.

    Args:
        year: Year of the session
        gp: Grand Prix name
        session_type: Session type (FP1, FP2, FP3, Q, R, etc.)
        driver_codes: List of driver codes to analyze
    """
    if driver_codes is None:
        driver_codes = DEFAULT_DRIVERS.copy()

    print("\n" + "=" * 70)
    print("   F1 TELEMETRY ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"Session: {year} {gp} {session_type}")
    print(f"Drivers: {', '.join(driver_codes)}")
    print("=" * 70)

    print("\n" + "-" * 70)
    print("STEP 1: SETUP - Enabling FastF1 Cache")
    print("-" * 70)
    data_loader.enable_cache(cache_dir="./cache")
    print("FastF1 cache enabled successfully")

    print("\n" + "-" * 70)
    print("STEP 2: DATA COLLECTION - Loading Session")
    print("-" * 70)
    try:
        session = data_loader.load_session(year, gp, session_type)
        print(f"Loaded session: {session.event['Name']} - {session.session_name}")
    except Exception as e:
        print(f"ERROR: Failed to load session: {e}")
        print("Trying to continue with available data...")
        session = None

    session_info = {
        "year": year,
        "gp": gp,
        "session_type": session_type,
        "date": f"{year} {gp} {session_type}"
    }

    if session is not None:
        session_info["date"] = session.event.get("OfficialEventName", f"{year} {gp}")

    driver_telemetry = {}
    sector_times_dict = {}
    fastest_laps = {}
    skipped_drivers = []

    print("\n" + "-" * 70)
    print("STEP 3: FEATURE ENGINEERING - Extracting Telemetry")
    print("-" * 70)

    for driver_code in driver_codes:
        print(f"\nProcessing driver: {driver_code}")
        
        try:
            fastest_lap = data_loader.get_driver_fastest_lap(session, driver_code)
            
            if fastest_lap is None:
                print(f"  WARNING: No lap data for {driver_code}")
                skipped_drivers.append(driver_code)
                continue
            
            telemetry = data_loader.get_lap_telemetry(fastest_lap)
            
            if telemetry.empty:
                print(f"  WARNING: No telemetry data for {driver_code}")
                skipped_drivers.append(driver_code)
                continue
            
            driver_telemetry[driver_code] = telemetry
            
            s1, s2, s3 = feature_engineering.get_sector_times(fastest_lap)
            sector_times_dict[driver_code] = (s1, s2, s3)
            
            lap_time = feature_engineering.get_lap_duration(fastest_lap)
            fastest_laps[driver_code] = lap_time
            
            print(f"  Lap time: {lap_time:.3f}s")
            print(f"  S1: {s1:.3f}s, S2: {s2:.3f}s, S3: {s3:.3f}s")
            
        except Exception as e:
            print(f"  ERROR processing {driver_code}: {e}")
            skipped_drivers.append(driver_code)
            continue

    if skipped_drivers:
        print(f"\nSkipped drivers (no data): {', '.join(skipped_drivers)}")

    if not driver_telemetry:
        print("\nERROR: No valid driver data collected. Exiting.")
        return

    print(f"\nSuccessfully processed {len(driver_telemetry)} drivers")

    print("\n" + "-" * 70)
    print("Building Feature Matrix")
    print("-" * 70)

    feature_df = feature_engineering.build_feature_matrix(driver_telemetry)

    if feature_df.empty:
        print("ERROR: Failed to build feature matrix")
        return

    print(f"Feature matrix shape: {feature_df.shape}")
    print(f"Features: {list(feature_df.columns)}")

    print("\n" + "-" * 70)
    print("STEP 4: CLUSTERING - KMeans and Hierarchical")
    print("-" * 70)

    kmeans_labels = clustering.cluster_drivers(feature_df, method="kmeans")
    kmeans_styles = clustering.assign_style_labels(feature_df, kmeans_labels)

    hierarchical_labels = clustering.cluster_drivers(feature_df, method="agglomerative")
    hierarchical_styles = clustering.assign_style_labels(feature_df, hierarchical_labels)

    print("\nKMeans Clustering Results:")
    for i, driver in enumerate(feature_df.index):
        print(f"  {driver}: {kmeans_styles[i]}")

    print("\nHierarchical Clustering Results:")
    for i, driver in enumerate(feature_df.index):
        print(f"  {driver}: {hierarchical_styles[i]}")

    cluster_summary = clustering.get_cluster_summary(feature_df, kmeans_styles)

    print("\n" + "-" * 70)
    print("STEP 5: LAP TIME PREDICTION")
    print("-" * 70)

    if session is not None:
        valid_drivers = list(driver_telemetry.keys())
        lap_data = feature_engineering.get_all_laps_features(session, valid_drivers)
        
        if not lap_data.empty and len(lap_data) > 2:
            print(f"Training on {len(lap_data)} laps from {len(valid_drivers)} drivers")
            
            X = lap_data[["mean_speed", "mean_throttle", "brake_frequency", "mean_rpm", "mean_gear"]]
            y = lap_data["lap_duration"]
            
            model, r2, mae = prediction.train_lap_time_model(X, y)
            
            print(f"Model R² Score: {r2:.4f}")
            print(f"Mean Absolute Error: {mae:.3f}s")
            
            prediction_results = {
                "r2": r2,
                "mae": mae,
                "predicted_times": {},
                "actual_times": {}
            }
            
            for driver in feature_df.index:
                try:
                    pred_time = prediction.predict_driver_lap_time(model, feature_df.loc[driver])
                    prediction_results["predicted_times"][driver] = pred_time
                    
                    if driver in fastest_laps:
                        prediction_results["actual_times"][driver] = fastest_laps[driver]
                except Exception as e:
                    print(f"Error predicting for {driver}: {e}")
        else:
            print("Insufficient lap data for prediction model")
            prediction_results = {"r2": 0.0, "mae": 0.0, "predicted_times": {}, "actual_times": {}}
            model = None
    else:
        print("No session data available for prediction")
        prediction_results = {"r2": 0.0, "mae": 0.0, "predicted_times": {}, "actual_times": {}}
        model = None
        lap_data = pd.DataFrame()

    print("\n" + "-" * 70)
    print("STEP 6: VISUALIZATION")
    print("-" * 70)

    visualization.generate_all_visualizations(
        driver_telemetry,
        sector_times_dict,
        feature_df,
        kmeans_styles
    )

    print("\n" + "-" * 70)
    print("STEP 7: REPORT GENERATION")
    print("-" * 70)

    report.generate_and_save_report(
        session_info,
        cluster_summary,
        sector_times_dict,
        feature_df,
        prediction_results,
        kmeans_styles,
        hierarchical_styles
    )

    print("\n" + "=" * 70)
    print("   PIPELINE COMPLETE")
    print("=" * 70)
    print(f"\nOutput files saved to: {os.path.abspath('output')}/")
    print("- speed_trace.png")
    print("- throttle_brake.png")
    print("- sector_comparison.png")
    print("- radar_chart.png")
    print("- cluster_scatter.png")
    print("- report.txt")


if __name__ == "__main__":
    run_pipeline()