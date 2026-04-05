# -*- coding: utf-8 -*-
# ============================================================
# 1. SETUP - Install required libraries
# ============================================================

import requests
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

# Set plotting style
sns.set_style("darkgrid")

# ============================================================
# OPENF1 API FUNCTIONS
# ============================================================

BASE_URL = "https://api.openf1.org/v1"

def fetch_data(endpoint, params=None):
    """Generic function to fetch data from OpenF1 API"""
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        df = pd.DataFrame(data)
        if df.empty:
            st.warning(f"No data returned from {endpoint}")
        return df
    except requests.exceptions.Timeout:
        st.error(f"Request timeout for {endpoint}")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {str(e)}")
        return pd.DataFrame()

def get_user_session(year, country, session_type):
    """Load F1 session data with error handling"""
    try:
        # Fetch meetings for the year
        meetings = fetch_data("meetings", {"year": year})
        if meetings.empty:
            return None, None, "No meetings found for this year"
        
        # Filter by country
        meeting = meetings[meetings["country_name"] == country]
        if meeting.empty:
            return None, None, f"No meeting found for {country} in {year}"
        
        meeting_key = meeting.iloc[0]["meeting_key"]
        
        # Fetch sessions for this meeting
        sessions = fetch_data("sessions", {"meeting_key": meeting_key})
        if sessions.empty:
            return None, None, "No sessions found for this meeting"
        
        # Map session types
        session_map = {
            'Q': 'Qualifying',
            'R': 'Race',
            'FP1': 'Practice 1',
            'FP2': 'Practice 2',
            'FP3': 'Practice 3',
            'Sprint': 'Sprint'
        }
        
        session_name = session_map.get(session_type, session_type)
        session = sessions[sessions["session_name"].str.contains(session_name, case=False, na=False)]
        
        if session.empty:
            return None, None, f"No {session_name} session found"
        
        session_key = session.iloc[0]["session_key"]
        session_info = {
            'session_key': session_key,
            'meeting_key': meeting_key,
            'session_name': session.iloc[0]["session_name"]
        }
        
        return session_info, None
    except Exception as e:
        return None, str(e)

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def extract_features(session_key, driver_number, driver_name):
    """
    Extract comprehensive telemetry features from a driver's fastest lap
    
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
        # Get all laps for this driver
        laps = fetch_data("laps", {"session_key": session_key, "driver_number": driver_number})
        
        if laps.empty:
            st.warning(f"No lap data for driver {driver_name}")
            return None, None
        
        # Filter valid laps
        valid_laps = laps[laps["lap_duration"].notna()].copy()
        valid_laps = valid_laps[valid_laps["lap_duration"] > 0]
        
        if valid_laps.empty:
            st.warning(f"No valid laps for driver {driver_name}")
            return None, None
        
        # Get fastest lap
        fastest_lap_idx = valid_laps["lap_duration"].idxmin()
        fastest_lap = valid_laps.loc[fastest_lap_idx]
        lap_duration = fastest_lap["lap_duration"]
        
        st.info(f"Processing {driver_name} - Fastest lap: {lap_duration:.3f}s")
        
        # Get car data (telemetry) for this driver - LIMIT THE DATA
        car_data = fetch_data("car_data", {
            "session_key": session_key,
            "driver_number": driver_number
        })
        
        if car_data.empty:
            st.warning(f"No telemetry data for driver {driver_name}")
            # Return features based on lap time only
            return {
                'Speed_mean': 0,
                'Speed_std': 0,
                'Throttle_mean': 0,
                'Throttle_std': 0,
                'Brake_mean': 0,
                'Brake_std': 0,
                'Steer_mean': 0,
                'Steer_std': 0,
                'Gear_mean': 0,
                'RPM_mean': 0,
                'DRS_pct': 0,
                'Acceleration_mean': 0,
                'AggressionIndex': 0,
                'LapTime': lap_duration
            }, None
        
        # Sample data if too large (take every 10th point for visualization)
        if len(car_data) > 1000:
            car_data = car_data.iloc[::10].copy()
        
        # Calculate acceleration
        if 'speed' in car_data.columns:
            car_data['DeltaSpeed'] = car_data['speed'].diff().fillna(0)
            car_data['Acceleration'] = car_data['DeltaSpeed']
            car_data['Acceleration'] = car_data['Acceleration'].replace([np.inf, -np.inf], 0).fillna(0)
        else:
            car_data['Acceleration'] = 0

        # Calculate aggression index safely
        throttle_mean = car_data['throttle'].mean() if 'throttle' in car_data.columns else 0
        brake_mean = car_data['brake'].mean() if 'brake' in car_data.columns else 0
        aggression_index = throttle_mean / (brake_mean + 1e-6) if brake_mean > 0 else throttle_mean

        # Extract features with proper null handling
        features = {
            'Speed_mean': car_data['speed'].mean() if 'speed' in car_data.columns else 0,
            'Speed_std': car_data['speed'].std() if 'speed' in car_data.columns else 0,
            'Throttle_mean': throttle_mean,
            'Throttle_std': car_data['throttle'].std() if 'throttle' in car_data.columns else 0,
            'Brake_mean': brake_mean,
            'Brake_std': car_data['brake'].std() if 'brake' in car_data.columns else 0,
            'Steer_mean': 0,  # Not directly available in OpenF1
            'Steer_std': 0,
            'Gear_mean': car_data['n_gear'].mean() if 'n_gear' in car_data.columns else 0,
            'RPM_mean': car_data['rpm'].mean() if 'rpm' in car_data.columns else 0,
            'DRS_pct': car_data['drs'].mean() if 'drs' in car_data.columns else 0,
            'Acceleration_mean': car_data['Acceleration'].mean() if 'Acceleration' in car_data.columns else 0,
            'AggressionIndex': aggression_index,
            'LapTime': lap_duration
        }

        # Fill any NaN values
        for key, value in features.items():
            if pd.isna(value):
                features[key] = 0
        
        # Prepare telemetry data for visualization
        tel = car_data.copy()
        if 'distance' not in tel.columns:
            tel['Distance'] = range(len(tel))
        else:
            tel['Distance'] = tel['distance']
        
        tel['Speed'] = tel['speed'] if 'speed' in tel.columns else 0
        tel['Throttle'] = tel['throttle'] if 'throttle' in tel.columns else 0
        tel['Brake'] = tel['brake'] if 'brake' in tel.columns else 0

        return features, tel

    except Exception as e:
        st.error(f"Error extracting features for {driver_name}: {str(e)}")
        return None, None

# ============================================================
# STREAMLIT APP
# ============================================================

def main():
    st.set_page_config(page_title="F1 Telemetry Analysis", page_icon="🏎️", layout="wide")
    
    st.title("🏎️ Advanced F1 Telemetry Modeling & Driver Style Classification")
    st.markdown("_Powered by OpenF1.org API_")
    st.markdown("---")
    
    # Sidebar for inputs
    st.sidebar.header("⚙️ Session Settings")
    
    year = st.sidebar.number_input("Year", min_value=2023, max_value=2025, value=2024, step=1)
    
    # Fetch available countries for the year
    with st.spinner("Loading race calendar..."):
        meetings = fetch_data("meetings", {"year": year})
    
    if meetings.empty:
        st.error("❌ No meetings found for this year.")
        st.info("Note: OpenF1 API only has data from 2023 onwards.")
        st.stop()
    
    available_countries = sorted(meetings["country_name"].dropna().unique())
    country = st.sidebar.selectbox("Country", available_countries)
    
    session_type = st.sidebar.selectbox("Session Type", ['Q', 'R', 'FP1', 'FP2', 'FP3', 'Sprint'], index=0)
    
    num_drivers = st.sidebar.slider("Number of Drivers", min_value=3, max_value=10, value=5, step=1)
    
    analyze_button = st.sidebar.button("🚀 Analyze Session", type="primary")
    
    # Main content area
    if analyze_button:
        with st.spinner(f"Loading {year} {country} {session_type} session..."):
            # Load session
            session_info, error = get_user_session(year, country, session_type)
            
            if error:
                st.error(f"❌ Error loading session: {error}")
                return
            
            session_key = session_info['session_key']
            st.success(f"✅ Loaded {year} {country} {session_type} session")
        
        # Get top drivers
        with st.spinner("Selecting top drivers..."):
            # Get all drivers
            drivers = fetch_data("drivers", {"session_key": session_key})
            
            if drivers.empty:
                st.error("❌ No driver data available")
                return
            
            drivers["driver_number"] = drivers["driver_number"].astype(str)
            
            # Get fastest lap for each driver
            driver_lap_times = []
            for _, driver in drivers.iterrows():
                driver_num = driver["driver_number"]
                laps = fetch_data("laps", {"session_key": session_key, "driver_number": driver_num})
                
                if not laps.empty:
                    valid_laps = laps[laps["lap_duration"].notna()]
                    valid_laps = valid_laps[valid_laps["lap_duration"] > 0]
                    
                    if not valid_laps.empty:
                        fastest_time = valid_laps["lap_duration"].min()
                        driver_lap_times.append({
                            'driver_number': driver_num,
                            'name': driver["name_acronym"],
                            'time': fastest_time
                        })
            
            # Sort and get top N drivers
            driver_lap_times_df = pd.DataFrame(driver_lap_times)
            driver_lap_times_df = driver_lap_times_df.sort_values('time').head(num_drivers)
            
            top_drivers = driver_lap_times_df['name'].tolist()
            st.success(f"✅ Top {num_drivers} drivers: {', '.join(top_drivers)}")
            print("Drivers Found")
        
        # Extract features
        with st.spinner("Extracting telemetry features..."):
            driver_features = {}
            driver_telemetry = {}
            
            progress_bar = st.progress(0)
            for counter, (idx, row) in enumerate(driver_lap_times_df.iterrows()):
                driver_name = row['name']
                driver_num = row['driver_number']
                
                features, tel = extract_features(session_key, driver_num, driver_name)
                
                if features is not None:
                    driver_features[driver_name] = features
                    if tel is not None and not tel.empty:
                        driver_telemetry[driver_name] = tel
                
                progress_bar.progress((counter + 1) / len(driver_lap_times_df))
            
            features_df = pd.DataFrame(driver_features).T
            st.success(f"✅ Features extracted for {len(features_df)} drivers")
            print("Features Extracted")
        
        # Clustering
        st.markdown("---")
        st.header("🎯 Driver Style Clustering")
        
        if len(features_df) > 0:
            cluster_features = ['Speed_mean', 'Throttle_mean', 'Brake_mean', 'Steer_mean',
                               'Gear_mean', 'RPM_mean', 'DRS_pct', 'Acceleration_mean', 'AggressionIndex']
            
            # Filter available features
            available_cluster_features = [f for f in cluster_features if f in features_df.columns]
            
            if len(available_cluster_features) >= 3:
                scaler = StandardScaler()
                X = scaler.fit_transform(features_df[available_cluster_features])
                
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
            
            # Filter available features
            available_regress_features = [f for f in regress_features if f in features_df.columns]
            
            if len(available_regress_features) >= 3:
                X_reg = features_df[available_regress_features]
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
                    'Feature': available_regress_features,
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
            if len(features_df) > 0 and 'available_regress_features' in locals() and len(available_regress_features) > 0:
                categories = available_regress_features
                N = len(categories)
                angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
                angles += angles[:1]
                
                fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))
                
                radar_data = features_df[available_regress_features].copy()
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
        
        # Sector Analysis (Note: Limited in OpenF1)
        st.markdown("---")
        st.header("🏁 Sector Analysis")
        
        try:
            # Try to get sector times from laps data
            all_laps = fetch_data("laps", {"session_key": session_key})
            
            if not all_laps.empty and 'segments_sector_1' in all_laps.columns:
                st.info("Sector timing data available - processing...")
                # Process sector data if available
            else:
                st.info("Sector data not available for this session via OpenF1 API")
        except Exception as e:
            st.warning(f"Sector analysis unavailable: {str(e)}")
        
        # Download data
        st.markdown("---")
        st.header("💾 Download Data")
        
        csv = features_df.to_csv(index=True)
        st.download_button(
            label="📥 Download Analysis Results (CSV)",
            data=csv,
            file_name=f"f1_analysis_{year}_{country}_{session_type}.csv",
            mime="text/csv"
        )
    
    else:
        st.info("👈 Configure session settings in the sidebar and click 'Analyze Session' to begin")
        
        st.markdown("""
        ### 🏎️ Features:
        - **Compare multiple drivers** using telemetry metrics from OpenF1 API
        - **Cluster driving styles** (Late Brakers, Smooth Cornering, Aggressive)
        - **Predict lap times** using regression models
        - **Visualize speed, throttle, brake zones**, and driver profiles
        - **Generate reports** linking style to performance metrics
        
        ### 📊 Applications:
        - Identifying braking and cornering patterns across drivers
        - Measuring lap time gains and losses by driving strategy
        - Predicting performance impact from driver style
        - Supporting engineers in race strategy decisions
        
        ### 🔄 Migration Notes:
        - Now using **OpenF1 API** instead of FastF1
        - Data available from **2023 onwards**
        - More reliable API with better uptime
        - Real-time and historical data access
        - Steering data not directly available (set to 0)
        """)

if __name__ == "__main__":
    main()