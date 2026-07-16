"""
Data loader module for F1 telemetry data using FastF1.
"""

import fastf1
import pandas as pd
from fastf1.core import Session


CACHE_DIR = "cache"


class SessionNotFound(Exception):
    pass


class DriverNotFound(Exception):
    pass


def load_session(year: int, grand_prix: str, session_type: str = "R") -> Session:
    """Load an F1 session, returns a loaded Session object."""
    fastf1.Cache.enable_cache(CACHE_DIR)
    session = fastf1.get_session(year, grand_prix, session_type)
    session.load()
    return session


def get_drivers(session: Session) -> list:
    """Return list of driver abbreviations for a session."""
    return session.results["Abbreviation"].tolist()


def get_driver_telemetry(session: Session, driver_code: str, laps: str = "fastest") -> pd.DataFrame:
    """Return telemetry DataFrame for a driver.

    Args:
        session: Loaded FastF1 session.
        driver_code: Three-letter driver abbreviation.
        laps: "fastest" (single fastest lap) or "all" (all completed laps).

    Returns:
        DataFrame with Distance, Speed, Throttle, Brake, DRS, RPM, Gear, nGear.
        If laps="all", also includes LapNumber column.
    """
    laps_data = session.laps.pick_drivers(driver_code)
    if laps_data.empty:
        raise DriverNotFound(f"Driver '{driver_code}' not found in session")

    cols = ["Distance", "Speed", "Throttle", "Brake", "DRS", "RPM", "Gear", "nGear"]

    if laps == "all":
        telemetry_list = []
        for _, lap in laps_data.iterrows():
            lap_telemetry = lap.get_car_data()
            keep = [c for c in cols if c in lap_telemetry.columns]
            lap_telemetry = lap_telemetry[keep].copy()
            lap_telemetry["LapNumber"] = lap["LapNumber"]
            telemetry_list.append(lap_telemetry)
        return pd.concat(telemetry_list, ignore_index=True)
    else:
        fastest = laps_data.pick_fastest()
        telemetry = fastest.get_car_data()
        return telemetry[[c for c in cols if c in telemetry.columns]]


def get_sector_times(session: Session, driver_code: str) -> tuple:
    """Return (s1, s2, s3) sector times in seconds for a driver's fastest lap."""
    laps = session.laps.pick_drivers(driver_code)
    if laps.empty:
        raise DriverNotFound(f"Driver '{driver_code}' not found in session")
    fastest = laps.pick_fastest()
    return (
        fastest["Sector1Time"].total_seconds(),
        fastest["Sector2Time"].total_seconds(),
        fastest["Sector3Time"].total_seconds(),
    )


def get_weather(session: Session) -> dict:
    """Return average weather conditions for a session.

    Returns dict with track_temp, air_temp (float °C) and rainfall (bool).
    """
    weather = session.weather_data
    if weather is None or weather.empty:
        return {"track_temp": 0.0, "air_temp": 0.0, "rainfall": False}
    return {
        "track_temp": float(weather["TrackTemp"].mean()),
        "air_temp": float(weather["AirTemp"].mean()),
        "rainfall": bool(weather["Rainfall"].any()),
    }


def get_result(session: Session, driver_code: str) -> dict:
    """Return result dict (position, status) for a driver."""
    row = session.results[session.results["Abbreviation"] == driver_code]
    if row.empty:
        return {}
    r = row.iloc[0]
    return {"position": int(r["Position"]), "status": r["Status"]}
