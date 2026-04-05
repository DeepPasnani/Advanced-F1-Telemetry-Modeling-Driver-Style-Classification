"""
Data loading module using FastF1 for F1 telemetry data.

This module provides functions to:
- Enable FastF1 cache
- Load race sessions
- Get driver fastest laps
- Retrieve telemetry data

TODO: Real-time telemetry streaming via WebSocket (Future Work)
"""

import fastf1
import fastf1.plotting
import pandas as pd
from typing import Optional, Dict, Any


def enable_cache(cache_dir: str = "./cache") -> None:
    """
    Enable FastF1 cache for storing downloaded data.

    Args:
        cache_dir: Directory path for cache storage
    """
    fastf1.Cache.enable_cache(cache_dir)


def load_session(year: int, gp: str, session_type: str) -> fastf1.core.Session:
    """
    Load a FastF1 session for the specified year, grand prix, and session type.

    Args:
        year: Year of the session (e.g., 2023)
        gp: Grand Prix name (e.g., 'Monza')
        session_type: Session type - 'FP1', 'FP2', 'FP3', 'Q', 'R', 'SQ', 'Sprint'

    Returns:
        FastF1 Session object
    """
    session = fastf1.get_session(year, gp, session_type)
    session.load()
    return session


def get_driver_fastest_lap(session: fastf1.core.Session, driver_code: str) -> Optional[fastf1.core.Lap]:
    """
    Get the fastest lap for a specific driver in the session.

    Args:
        session: FastF1 Session object
        driver_code: Driver code (e.g., 'VER', 'HAM', 'LEC')

    Returns:
        Fastest Lap object or None if not available
    """
    try:
        driver_laps = session.laps[session.laps["Driver"] == driver_code]
        if driver_laps.empty:
            return None
        fastest_lap = driver_laps.pick_fastest()
        return fastest_lap
    except Exception as e:
        print(f"Error getting fastest lap for {driver_code}: {e}")
        return None


def get_lap_telemetry(lap: fastf1.core.Lap) -> pd.DataFrame:
    """
    Get telemetry data for a specific lap.

    Args:
        lap: FastF1 Lap object

    Returns:
        DataFrame with telemetry columns: Distance, Speed, Throttle, Brake, RPM, nGear, Time
    """
    try:
        telemetry = lap.get_car_data()
        if telemetry.empty:
            return pd.DataFrame()
        
        telemetry = telemetry.reset_index(drop=True)
        
        if "Time" not in telemetry.columns and "date" in telemetry.columns:
            telemetry["Time"] = (telemetry["date"] - telemetry["date"].iloc[0]).dt.total_seconds()
        
        return telemetry
    except Exception as e:
        print(f"Error getting telemetry: {e}")
        return pd.DataFrame()


def get_driver_info(session: fastf1.core.Session) -> pd.DataFrame:
    """
    Get driver information for the session.

    Args:
        session: FastF1 Session object

    Returns:
        DataFrame with driver information
    """
    try:
        return session.results
    except Exception as e:
        print(f"Error getting driver info: {e}")
        return pd.DataFrame()


def get_session_info(session: fastf1.core.Session) -> Dict[str, Any]:
    """
    Get session information.

    Args:
        session: FastF1 Session object

    Returns:
        Dictionary with session info
    """
    return {
        "year": session.event.year,
        "gp": session.event["Name"],
        "session_type": session.session_name,
        "date": session.event["OfficialEventName"]
    }
