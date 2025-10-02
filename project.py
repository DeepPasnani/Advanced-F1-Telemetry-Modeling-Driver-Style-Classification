# -*- coding: utf-8 -*-
# ============================================================
# 1. SETUP - Install required libraries and enable FastF1 cache
# ============================================================

import fastf1
from fastf1 import plotting
from fastf1.core import Laps
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestRegressor
import streamlit as st
import warnings
warnings.filterwarnings('ignore')

# Enable cache for faster data loading
fastf1.Cache.enable_cache('./cache')

# Set plotting style
sns.set_style("darkgrid")
plotting.setup_mpl()

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_session(year, event, session_type):
    """Load F1 session data with error handling"""
    try:
        s = fastf1.get_session(year, event, session_type)
        s.load()
        return s, None
    except Exception as e:
        return None, str(e)

def extract_features(lap):
    """
    Extract comprehensive telemetry features from a lap
    
    Features extracted:
    - Speed metrics (mean, std)
    - Throttle usage (mean, std)
    - Brake application (mean, std)
    - Steering input (mean, std)
    - Gear usage and RPM
    - DRS percentage
    - Acceleration patterns
    - Aggression index (throttle/brake ratio)
    """
    try:
        tel = lap.get_car_data().add_distance()

        # Time calculations
        tel['Time_s'] = (tel['Time'] - tel['Time'].iloc[0]).dt.total_seconds()

        # Speed and acceleration
        tel['DeltaSpeed'] = tel['Speed'].diff().fillna(0)
        tel['DeltaTime'] = tel['Time_s'].diff().fillna(0.001)
        tel['Acceleration'] = tel['DeltaSpeed'] / tel['DeltaTime']
        tel['Acceleration'] = tel['Acceleration'].replace([np.inf, -np.inf], 0).fillna(0)

        # Calculate aggression index safely
        throttle_mean = tel['Throttle'].mean()
        brake_mean = tel['Brake'].mean()
        aggression_index = throttle_mean / (brake_mean + 1e-6) if brake_mean > 0 else throttle_mean

        # Extract features with proper null handling
        features = {
            'Speed_mean': tel['Speed'].mean(),
            'Speed_std': tel['Speed'].std(),
            'Throttle_mean': tel['Throttle'].mean(),
            'Throttle_std': tel['Throttle'].std(),
            'Brake_mean': tel['Brake'].mean(),
            'Brake_std': tel['Brake'].std(),
            'Steer_mean': abs(tel['Steer']).mean(),
            'Steer_std': tel['Steer'].std(),
            'Gear_mean': tel['nGear'].mean(),
            'RPM_mean': tel['RPM'].mean(),
            'DRS_pct': tel['DRS'].mean(),
            'Acceleration_mean': tel['Acceleration'].mean(),
            'AggressionIndex': aggression_index,
            'LapTime': lap['LapTime'].total_seconds()
        }

        # Fill any NaN values
        for key, value in features.items():
            if pd.isna(value):
                features[key] = 0

        return features, tel

    except Exception as e:
        return None, None

# ============================================================
# STREAMLIT APP
# ============================================================

def main():
    st.set_page_config(page_title="F1 Telemetry Analysis", page_icon="🏎️", layout="wide")
    
    st.title("🏎️ Advanced F1 Telemetry Modeling & Driver Style Classification")
    st.markdown("---")
    
    # Sidebar for inputs
    st.sidebar.header("⚙️ Session Settings")
    
    year = st.sidebar.number_input("Year", min_value=2018, max_value=2024, value=2023, step=1)
    
    # Common race events
    events = ['Bahrain', 'Saudi Arabia', 'Australia', 'Azerbaijan', 'Miami', 'Monaco', 
              'Spain', 'Canada', 'Austria', 'Great Britain', 'Hungary', 'Belgium', 
              'Netherlands', 'Italy', 'Singapore', 'Japan', 'Qatar', 'United States', 
              'Mexico', 'Brazil', 'Las Vegas', 'Abu Dhabi', 'Monza']
    event = st.sidebar.selectbox("Grand Prix", events, index=events.index('Monza'))
    
    session_type = st.sidebar.selectbox("Session Type", ['Q', 'R', 'FP1', 'FP2', 'FP3', 'Sprint'], index=0)
    
    num_drivers = st.sidebar.slider("Number of Drivers", min_value=3, max_value=10, value=5, step=1)
    
    analyze_button = st.sidebar.button("🚀 Analyze Session", type="primary")
    
    # Main content area
    if analyze_button:
        with st.spinner(f"Loading {year} {event} {session_type} session..."):
            # Load session
            user_session, error = get_user_session(year, event, session_type)
            
            if error:
                st.error(f"❌ Error loading session: {error}")
                return
            
            st.success(f"✅ Loaded {year} {event} {session_type} session")
        
        # Get top drivers
        with st.spinner("Selecting top drivers..."):
            valid_laps = user_session.laps.pick_quicklaps().dropna(subset=['LapTime'])
            top_drivers = valid_laps.groupby('Driver')['LapTime'].min().nsmallest(num_drivers).index.tolist()
            
            # Get fastest lap for each driver
            laps = {}
            for driver in top_drivers:
                driver_laps = user_session.laps.pick_drivers([driver]).pick_quicklaps()
                if not driver_laps.empty:
                    fastest_lap = driver_laps.pick_fastest()
                    laps[driver] = fastest_lap
            
            st.success(f"✅ Top {num_drivers} drivers: {', '.join(top_drivers)}")
            print("Drivers Found")
        
        # Extract features
        with st.spinner("Extracting telemetry features..."):
            driver_features = {}
            driver_telemetry = {}
            
            progress_bar = st.progress(0)
            for idx, driver in enumerate(top_drivers):
                if driver in laps:
                    features, tel = extract_features(laps[driver])
                    if features is not None:
                        driver_features[driver] = features
                        driver_telemetry[driver] = tel
                progress_bar.progress((idx + 1) / len(top_drivers))
            
            features_df = pd.DataFrame(driver_features).T
            st.success(f"✅ Features extracted for {len(features_df)} drivers")
            print("Features Extracted")
        
        # Clustering
        st.markdown("---")
        st.header("🎯 Driver Style Clustering")
        
        if len(features_df) > 0:
            cluster_features = ['Speed_mean', 'Throttle_mean', 'Brake_mean', 'Steer_mean',
                               'Gear_mean', 'RPM_mean', 'DRS_pct', 'Acceleration_mean', 'AggressionIndex']
            
            scaler = StandardScaler()
            X = scaler.fit_transform(features_df[cluster_features])
            
            n_clusters = min(3, len(features_df))
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X)
            features_df['Cluster'] = clusters
            print("Clustering done")
            
            cluster_names = {0: 'Smooth Cornering', 1: 'Aggressive', 2: 'Late Brakers'}
            features_df['Style'] = features_df['Cluster'].map(cluster_names)
            
            # Display clustering results
            col1, col2, col3 = st.columns(3)
            for idx, (driver, style) in enumerate(zip(features_df.index, features_df['Style'])):
                cols = [col1, col2, col3]
                with cols[idx % 3]:
                    st.metric(driver, style)
                    print(f"Driver: {driver}, Style: {style}")
        
        # Lap Time Prediction
        st.markdown("---")
        st.header("📊 Lap Time Prediction Model")
        
        if len(features_df) > 2:
            regress_features = ['Speed_mean', 'Throttle_mean', 'Brake_mean', 'Steer_mean',
                               'Gear_mean', 'RPM_mean', 'DRS_pct', 'Acceleration_mean', 'AggressionIndex']
            
            X_reg = features_df[regress_features]
            y_reg = features_df['LapTime']
            
            rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10)
            rf.fit(X_reg, y_reg)
            
            lap_time_pred = rf.predict(X_reg)
            features_df['LapTime_pred'] = lap_time_pred
            
            mae = np.mean(np.abs(y_reg - lap_time_pred))
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Model Mean Absolute Error", f"{mae:.3f}s")
            
            # Feature importance
            feature_importance = pd.DataFrame({
                'Feature': regress_features,
                'Importance': rf.feature_importances_
            }).sort_values('Importance', ascending=False)
            
            with col2:
                st.subheader("Top Feature Importance")
                st.dataframe(feature_importance.head(5), use_container_width=True, hide_index=True)
        
        # Visualizations
        st.markdown("---")
        st.header("📈 Telemetry Visualization")
        
        if len(driver_telemetry) > 0:
            # Telemetry comparison
            fig, axs = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
            fig.suptitle('Driver Telemetry Comparison', fontsize=16, fontweight='bold')
            
            colors = plt.cm.Set1(np.linspace(0, 1, len(top_drivers)))
            
            for i, driver in enumerate(top_drivers):
                if driver in driver_telemetry:
                    tel = driver_telemetry[driver]
                    color = colors[i]
                    
                    axs[0].plot(tel['Distance'], tel['Speed'], label=driver, color=color, alpha=0.8, linewidth=2)
                    axs[1].plot(tel['Distance'], tel['Throttle'], label=driver, color=color, alpha=0.8, linewidth=2)
                    axs[2].plot(tel['Distance'], tel['Brake'], label=driver, color=color, alpha=0.8, linewidth=2)
            
            axs[0].set_ylabel('Speed [km/h]', fontsize=12, fontweight='bold')
            axs[0].set_title('Speed Profile', fontsize=12)
            axs[0].grid(True, alpha=0.3)
            axs[0].legend(loc='upper right')
            
            axs[1].set_ylabel('Throttle [%]', fontsize=12, fontweight='bold')
            axs[1].set_title('Throttle Application', fontsize=12)
            axs[1].grid(True, alpha=0.3)
            
            axs[2].set_ylabel('Brake [%]', fontsize=12, fontweight='bold')
            axs[2].set_title('Brake Zones', fontsize=12)
            axs[2].set_xlabel('Distance [m]', fontsize=12, fontweight='bold')
            axs[2].grid(True, alpha=0.3)
            
            plt.tight_layout()
            st.pyplot(fig)
            
            # Radar chart
            if len(features_df) > 0:
                categories = regress_features
                N = len(categories)
                angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
                angles += angles[:1]
                
                fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
                
                radar_data = features_df[regress_features].copy()
                for col in radar_data.columns:
                    col_range = radar_data[col].max() - radar_data[col].min()
                    if col_range > 0:
                        radar_data[col] = (radar_data[col] - radar_data[col].min()) / col_range
                    else:
                        radar_data[col] = 0
                print("Radar data prepared")
                
                for i, driver in enumerate(radar_data.index):
                    values = radar_data.loc[driver].tolist()
                    values += values[:1]
                    ax.plot(angles, values, 'o-', linewidth=2, label=driver, alpha=0.8, color=colors[i])
                    ax.fill(angles, values, alpha=0.15, color=colors[i])
                
                ax.set_xticks(angles[:-1])
                ax.set_xticklabels(categories, size=10)
                ax.set_ylim(0, 1)
                ax.set_title('Driver Style Profile (Normalized)', size=16, pad=30, fontweight='bold')
                ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
                ax.grid(True)
                
                plt.tight_layout()
                st.pyplot(fig)
        
        # Performance Report
        st.markdown("---")
        st.header("📋 Driver Performance Report")
        
        for driver in top_drivers:
            if driver in features_df.index:
                with st.expander(f"🏎️ {driver}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Lap Time", f"{features_df.loc[driver, 'LapTime']:.3f}s")
                        if 'LapTime_pred' in features_df.columns:
                            pred_time = features_df.loc[driver, 'LapTime_pred']
                            st.metric("Predicted Time", f"{pred_time:.3f}s")
                    
                    with col2:
                        if 'Style' in features_df.columns:
                            st.metric("Driving Style", features_df.loc[driver, 'Style'])
                        st.metric("Avg Speed", f"{features_df.loc[driver, 'Speed_mean']:.1f} km/h")
                    
                    with col3:
                        st.metric("Throttle Usage", f"{features_df.loc[driver, 'Throttle_mean']:.1f}%")
                        st.metric("Brake Usage", f"{features_df.loc[driver, 'Brake_mean']:.1f}%")
                    
                    st.markdown("**Additional Metrics:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"🎯 Steering: {features_df.loc[driver, 'Steer_mean']:.2f}°")
                    with col2:
                        st.write(f"⚡ Aggression Index: {features_df.loc[driver, 'AggressionIndex']:.2f}")
                    with col3:
                        st.write(f"🚀 DRS Usage: {features_df.loc[driver, 'DRS_pct']*100:.1f}%")
        
        # Session Summary
        st.markdown("---")
        st.header("📊 Session Summary")
        
        if len(features_df) > 0:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                fastest_driver = features_df['LapTime'].idxmin()
                fastest_time = features_df['LapTime'].min()
                st.metric("Fastest Lap", f"{fastest_time:.3f}s", f"{fastest_driver}")
            
            with col2:
                slowest_driver = features_df['LapTime'].idxmax()
                slowest_time = features_df['LapTime'].max()
                st.metric("Slowest Lap", f"{slowest_time:.3f}s", f"{slowest_driver}")
            
            with col3:
                avg_time = features_df['LapTime'].mean()
                st.metric("Average Lap Time", f"{avg_time:.3f}s")
            
            with col4:
                time_spread = features_df['LapTime'].max() - features_df['LapTime'].min()
                st.metric("Time Spread", f"{time_spread:.3f}s")
        
        # Sector Analysis
        st.markdown("---")
        st.header("🏁 Sector Analysis")
        
        try:
            sector_data = user_session.laps.pick_drivers(top_drivers)[['Driver', 'Sector1Time', 'Sector2Time', 'Sector3Time']].dropna()
            if not sector_data.empty:
                sector_summary = sector_data.groupby('Driver').mean()
                
                st.subheader("Average Sector Times")
                st.dataframe(sector_summary, use_container_width=True)
                
                st.subheader("Sector Performance")
                for driver in top_drivers:
                    if driver in sector_summary.index:
                        sectors = sector_summary.loc[driver]
                        best_sector = sectors.idxmin()
                        st.write(f"**{driver}**: Strongest in {best_sector}")
            else:
                st.info("Sector data not available for this session")
        except Exception as e:
            st.warning(f"Sector analysis unavailable: {str(e)}")
        
        # Download data
        st.markdown("---")
        st.header("💾 Download Data")
        
        csv = features_df.to_csv(index=True)
        st.download_button(
            label="📥 Download Analysis Results (CSV)",
            data=csv,
            file_name=f"f1_analysis_{year}_{event}_{session_type}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("👈 Configure session settings in the sidebar and click 'Analyze Session' to begin")
        
        st.markdown("""
        ### 🏎️ Features:
        - **Compare multiple drivers** using telemetry metrics
        - **Segment laps into sectors** for detailed analysis
        - **Cluster driving styles** (Late Brakers, Smooth Cornering, Aggressive)
        - **Predict lap times** using regression models
        - **Visualize speed, throttle, brake zones**, and driver profiles
        - **Generate reports** linking style to car setup and tire usage
        
        ### 📊 Applications:
        - Identifying braking and cornering patterns across drivers
        - Measuring lap time gains and losses by driving strategy
        - Predicting tire wear impact from driver style
        - Supporting engineers in race strategy decisions
        """)

if __name__ == "__main__":
    main()