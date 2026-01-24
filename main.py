import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# DATA LOADER FUNCTIONS
# ============================================================

BASE_URL = "https://api.openf1.org/v1"

def fetch_data(endpoint, params=None):
    """Generic function to fetch data from OpenF1 API"""
    try:
        response = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching {endpoint}: {e}")
        return pd.DataFrame()

def fetch_sessions(meeting_key):
    """Fetch sessions for a specific meeting"""
    sessions = fetch_data("sessions", {"meeting_key": meeting_key})
    if not sessions.empty:
        sessions["label"] = (
            sessions["session_name"] + 
            " (" + sessions["date_start"].str[:10] + ")"
        )
    return sessions

def fetch_laps(session_key):
    """Fetch lap data for a session"""
    return fetch_data("laps", {"session_key": session_key})

def fetch_stints(session_key):
    """Fetch stint data for a session"""
    return fetch_data("stints", {"session_key": session_key})

def fetch_pit_stop(session_key):
    """Fetch pit stop data for a session"""
    return fetch_data("pit", {"session_key": session_key})

def fetch_drivers(session_key):
    """Fetch driver information for a session"""
    return fetch_data("drivers", {"session_key": session_key})

def fetch_car_data(session_key, driver_number):
    """Fetch detailed car telemetry for a driver"""
    return fetch_data("car_data", {
        "session_key": session_key,
        "driver_number": driver_number
    })

def fetch_position_data(session_key):
    """Fetch position data for the session"""
    return fetch_data("position", {"session_key": session_key})

# ============================================================
# DATA PROCESSOR FUNCTIONS
# ============================================================

def process_lap_data(lap_df):
    """Process and clean lap time data"""
    if lap_df.empty:
        return lap_df
    
    # Remove invalid laps
    lap_df = lap_df[lap_df["lap_duration"].notna()].copy()
    lap_df = lap_df[lap_df["lap_duration"] > 0]
    
    # Convert to seconds if needed
    if not lap_df.empty and lap_df["lap_duration"].max() > 1000:
        lap_df["lap_duration"] = lap_df["lap_duration"] / 1000
    
    return lap_df

def process_stints(stints_df):
    """Process stint/tire strategy data"""
    if stints_df.empty:
        return stints_df
    
    stints_df = stints_df.copy()
    
    # Calculate stint length
    if "lap_start" in stints_df.columns and "lap_end" in stints_df.columns:
        stints_df["stint_length"] = stints_df["lap_end"] - stints_df["lap_start"] + 1
    
    return stints_df

def process_pit_stops(pit_df):
    """Process pit stop data"""
    if pit_df.empty:
        return pit_df
    
    pit_df = pit_df.copy()
    
    # Filter valid pit stops
    if "pit_duration" in pit_df.columns:
        pit_df = pit_df[pit_df["pit_duration"].notna()]
        pit_df = pit_df[pit_df["pit_duration"] > 0]
    
    return pit_df

def build_driver_color_map(driver_df):
    """Build a color map for drivers based on team colors"""
    color_map = {}
    
    # F1 2024 team colors
    team_colors = {
        "Red Bull Racing": "#3671C6",
        "Ferrari": "#E8002D",
        "Mercedes": "#27F4D2",
        "McLaren": "#FF8000",
        "Aston Martin": "#229971",
        "Alpine": "#FF87BC",
        "Williams": "#64C4FF",
        "RB": "#6692FF",
        "Kick Sauber": "#52E252",
        "Haas F1 Team": "#B6BABD",
        "Sauber": "#52E252",
        "AlphaTauri": "#6692FF"
    }
    
    for _, driver in driver_df.iterrows():
        team = driver.get("team_name", "Unknown")
        driver_num = str(driver.get("driver_number", ""))
        color_map[driver_num] = team_colors.get(team, "#808080")
    
    return color_map

# ============================================================
# VISUALIZATION FUNCTIONS
# ============================================================

def plot_lap_times(lap_df, driver_color_map):
    """Create lap time visualization"""
    fig = go.Figure()
    
    if lap_df.empty:
        return fig
    
    for driver_num in lap_df["driver_number"].unique():
        driver_data = lap_df[lap_df["driver_number"] == driver_num].sort_values("lap_number")
        driver_name = driver_data["name_acronym"].iloc[0] if "name_acronym" in driver_data.columns else str(driver_num)
        
        fig.add_trace(go.Scatter(
            x=driver_data["lap_number"],
            y=driver_data["lap_duration"],
            mode="lines+markers",
            name=driver_name,
            line=dict(color=driver_color_map.get(str(driver_num), "#808080"), width=2),
            marker=dict(size=6),
            hovertemplate=f"<b>{driver_name}</b><br>" +
                         "Lap: %{x}<br>" +
                         "Time: %{y:.3f}s<br>" +
                         "<extra></extra>"
        ))
    
    fig.update_layout(
        title="Lap Times Throughout Session",
        xaxis_title="Lap Number",
        yaxis_title="Lap Time (seconds)",
        hovermode="closest",
        height=500,
        template="plotly_dark",
        legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
    )
    
    return fig

def plot_tire_strategy(stints_df, driver_color_map):
    """Create tire strategy visualization"""
    fig = go.Figure()
    
    if stints_df.empty:
        return fig
    
    tire_colors = {
        "SOFT": "#FF0000",
        "MEDIUM": "#FFF200",
        "HARD": "#FFFFFF",
        "INTERMEDIATE": "#00FF00",
        "WET": "#0000FF"
    }
    
    # Group by driver
    drivers = stints_df["name_acronym"].unique() if "name_acronym" in stints_df.columns else stints_df["driver_number"].unique()
    
    for idx, driver in enumerate(drivers):
        driver_stints = stints_df[
            (stints_df["name_acronym"] == driver) if "name_acronym" in stints_df.columns 
            else (stints_df["driver_number"] == driver)
        ].sort_values("stint_number")
        
        for _, stint in driver_stints.iterrows():
            compound = stint.get("compound", "UNKNOWN").upper()
            lap_start = stint.get("lap_start", 0)
            lap_end = stint.get("lap_end", 0)
            stint_length = lap_end - lap_start + 1
            
            fig.add_trace(go.Bar(
                x=[stint_length],
                y=[driver],
                orientation="h",
                name=compound,
                marker=dict(
                    color=tire_colors.get(compound, "#808080"),
                    line=dict(color="black", width=1)
                ),
                text=compound,
                textposition="inside",
                hovertemplate=f"<b>{driver}</b><br>" +
                             f"Compound: {compound}<br>" +
                             f"Laps: {lap_start} - {lap_end}<br>" +
                             f"Length: {stint_length} laps<br>" +
                             "<extra></extra>",
                showlegend=False,
                base=lap_start
            ))
    
    fig.update_layout(
        title="Tire Strategy",
        xaxis_title="Lap Number",
        yaxis_title="Driver",
        barmode="overlay",
        height=max(400, len(drivers) * 40),
        template="plotly_dark",
        yaxis=dict(autorange="reversed")
    )
    
    return fig

def plot_pit_stop(pit_df, driver_color_map):
    """Create pit stop duration visualization"""
    fig = go.Figure()
    
    if pit_df.empty:
        return fig
    
    # Group by driver and calculate average
    pit_summary = pit_df.groupby(["driver_number", "name_acronym"])["pit_duration"].agg(['mean', 'count']).reset_index()
    pit_summary = pit_summary.sort_values("mean")
    
    colors = [driver_color_map.get(str(num), "#808080") for num in pit_summary["driver_number"]]
    
    fig.add_trace(go.Bar(
        x=pit_summary["name_acronym"],
        y=pit_summary["mean"],
        marker=dict(color=colors, line=dict(color="black", width=1)),
        text=[f"{val:.2f}s" for val in pit_summary["mean"]],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>" +
                     "Avg Duration: %{y:.2f}s<br>" +
                     "<extra></extra>"
    ))
    
    fig.update_layout(
        title="Average Pit Stop Durations",
        xaxis_title="Driver",
        yaxis_title="Duration (seconds)",
        height=500,
        template="plotly_dark",
        showlegend=False
    )
    
    return fig

def plot_position_changes(position_df, driver_color_map):
    """Plot position changes throughout the session"""
    fig = go.Figure()
    
    if position_df.empty:
        return fig
    
    for driver_num in position_df["driver_number"].unique():
        driver_data = position_df[position_df["driver_number"] == driver_num].sort_values("date")
        
        if "name_acronym" in driver_data.columns:
            driver_name = driver_data["name_acronym"].iloc[0]
        else:
            driver_name = str(driver_num)
        
        fig.add_trace(go.Scatter(
            x=driver_data["date"],
            y=driver_data["position"],
            mode="lines",
            name=driver_name,
            line=dict(color=driver_color_map.get(str(driver_num), "#808080"), width=2)
        ))
    
    fig.update_layout(
        title="Position Changes Throughout Session",
        xaxis_title="Time",
        yaxis_title="Position",
        yaxis=dict(autorange="reversed"),
        height=500,
        template="plotly_dark",
        hovermode="x unified"
    )
    
    return fig

# ============================================================
# STREAMLIT APP
# ============================================================

def main():
    st.set_page_config(page_title="F1 Strategy Dashboard", page_icon="🏎️", layout="wide")
    
    st.title("🏎️ Formula 1 Strategy Dashboard")
    st.markdown("_Powered by OpenF1.org API_")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("⚙️ Session Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Year selection
        available_years = [2023, 2024, 2025]
        selected_year = st.selectbox("Select Year", available_years, index=len(available_years) - 1)
        
        # Fetch meetings
        with st.spinner("Loading race calendar..."):
            all_meetings = fetch_data("meetings", {"year": selected_year})
        
        if all_meetings.empty:
            st.error("❌ No meetings found for this year.")
            st.stop()
        
        # Country selection
        available_countries = sorted(all_meetings["country_name"].dropna().unique())
        selected_country = st.selectbox("Select Country", available_countries)
        
        # Filter meetings
        filtered_meetings = all_meetings[all_meetings["country_name"] == selected_country].copy()
        filtered_meetings["label"] = filtered_meetings["meeting_name"] + " - " + filtered_meetings["location"]
        filtered_meetings = filtered_meetings.sort_values(by="meeting_key", ascending=False)
    
    with col2:
        # Grand Prix selection
        selected_meeting = st.selectbox("Select Grand Prix", filtered_meetings["label"])
        selected_meeting_key = filtered_meetings.loc[
            filtered_meetings["label"] == selected_meeting, "meeting_key"
        ].values[0]
        
        # Session selection
        with st.spinner("Loading sessions..."):
            sessions = fetch_sessions(selected_meeting_key)
        
        if sessions.empty:
            st.error("❌ No sessions found for this meeting.")
            st.stop()
        
        selected_session = st.selectbox("Select Session", sessions["label"])
        sessions["session_type"] = sessions["label"].str.extract(r"^(.*?)\s\(")
        selected_session_type = sessions.loc[sessions["label"] == selected_session, "session_type"].values[0]
        selected_session_key = sessions.loc[sessions["label"] == selected_session, "session_key"].values[0]
    
    # Session overview
    st.markdown(f"### 🏁 Session Overview: `{selected_session}`")
    with st.expander("📋 Session Details", expanded=False):
        st.write(f"**Meeting Key:** {selected_meeting_key}")
        st.write(f"**Session Key:** {selected_session_key}")
        st.write(f"**Session Type:** {selected_session_type}")
    
    # Fetch driver data
    with st.spinner("Loading driver information..."):
        driver_df = fetch_drivers(selected_session_key)
    
    if driver_df.empty:
        st.error("❌ No driver data available for this session.")
        st.stop()
    
    driver_df["driver_number"] = driver_df["driver_number"].astype(str)
    driver_color_map = build_driver_color_map(driver_df)
    driver_info = driver_df[["driver_number", "name_acronym"]]
    
    # Lap Times Section
    st.markdown("---")
    with st.expander(f"📈 Lap Time Analysis for {selected_session_type} at {selected_country} {selected_year}", expanded=True):
        with st.spinner("Loading lap data..."):
            lap_df = fetch_laps(selected_session_key)
            processed_df = process_lap_data(lap_df)
        
        if not processed_df.empty:
            processed_df["driver_number"] = processed_df["driver_number"].astype(str)
            processed_df = processed_df.merge(driver_info, on="driver_number", how="left")
            
            fig = plot_lap_times(processed_df, driver_color_map)
            st.plotly_chart(fig, use_container_width=True)
            
            # Statistics
            col1, col2, col3, col4 = st.columns(4)
            fastest = processed_df.loc[processed_df["lap_duration"].idxmin()]
            with col1:
                st.metric("Fastest Lap", f"{fastest['lap_duration']:.3f}s")
            with col2:
                st.metric("Driver", fastest.get("name_acronym", fastest["driver_number"]))
            with col3:
                st.metric("Lap Number", int(fastest["lap_number"]))
            with col4:
                avg_time = processed_df["lap_duration"].mean()
                st.metric("Average Lap", f"{avg_time:.3f}s")
        else:
            st.warning("⚠️ No lap time data found.")
    
    # Tire Strategy Section
    st.markdown("---")
    with st.expander(f"🛞 Tire Strategy for {selected_session_type} at {selected_country} {selected_year}", expanded=True):
        with st.spinner("Loading tire strategy..."):
            stints = fetch_stints(selected_session_key)
            stints_df = process_stints(stints)
        
        if not stints_df.empty:
            stints_df["driver_number"] = stints_df["driver_number"].astype(str)
            stints_df = stints_df.merge(driver_info, on="driver_number", how="left")
            
            fig = plot_tire_strategy(stints_df, driver_color_map)
            st.plotly_chart(fig, use_container_width=True)
            
            # Tire compound summary
            compound_summary = stints_df.groupby("compound").size().reset_index(name="count")
            st.subheader("Tire Compound Usage")
            col1, col2, col3 = st.columns(3)
            for idx, row in compound_summary.iterrows():
                cols = [col1, col2, col3]
                with cols[idx % 3]:
                    st.metric(row["compound"], f"{row['count']} stints")
        else:
            st.warning("⚠️ No tire strategy data found.")
    
    # Pit Stops Section
    st.markdown("---")
    with st.expander(f"⏱️ Pit Stop Analysis for {selected_session_type} at {selected_country} {selected_year}", expanded=True):
        with st.spinner("Loading pit stop data..."):
            pit_stop = fetch_pit_stop(selected_session_key)
            pit_stop_df = process_pit_stops(pit_stop)
        
        if not pit_stop_df.empty:
            pit_stop_df["driver_number"] = pit_stop_df["driver_number"].astype(str)
            pit_stop_df = pit_stop_df.merge(driver_info, on="driver_number", how="left")
            
            fig = plot_pit_stop(pit_stop_df, driver_color_map)
            st.plotly_chart(fig, use_container_width=True)
            
            # Pit stop statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                fastest_pit = pit_stop_df["pit_duration"].min()
                st.metric("Fastest Pit Stop", f"{fastest_pit:.2f}s")
            with col2:
                avg_pit = pit_stop_df["pit_duration"].mean()
                st.metric("Average Pit Stop", f"{avg_pit:.2f}s")
            with col3:
                total_pits = len(pit_stop_df)
                st.metric("Total Pit Stops", total_pits)
        else:
            st.warning("⚠️ No pit stop data found.")
    
    # Position Changes Section (Race only)
    if selected_session_type and "Race" in selected_session_type:
        st.markdown("---")
        with st.expander("📊 Position Changes", expanded=False):
            with st.spinner("Loading position data..."):
                position_df = fetch_position_data(selected_session_key)
            
            if not position_df.empty:
                position_df["driver_number"] = position_df["driver_number"].astype(str)
                position_df = position_df.merge(driver_info, on="driver_number", how="left")
                
                fig = plot_position_changes(position_df, driver_color_map)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("⚠️ No position data found.")
    
    # Footer
    st.markdown("---")
    st.markdown("### 📥 Export Data")
    if not processed_df.empty:
        csv = processed_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Lap Data (CSV)",
            data=csv,
            file_name=f"f1_lap_data_{selected_year}_{selected_country}_{selected_session_type}.csv",
            mime="text/csv"
        )
    
    st.markdown("---")
    st.caption("Data provided by OpenF1.org | Dashboard built with Streamlit")

if __name__ == "__main__":
    main()