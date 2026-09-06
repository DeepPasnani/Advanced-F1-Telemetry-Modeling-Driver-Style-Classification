"""
Data loader module for F1 telemetry data using FastF1.
"""

import os
import fastf1
import pandas as pd
from fastf1.core import Session


CACHE_DIR = os.environ.get("FASTF1_CACHE_DIR", "cache")


class SessionNotFound(Exception):
    pass


class DriverNotFound(Exception):
    pass


class NoValidLapError(Exception):
    """Raised when a driver has no lap that qualifies as a "fastest lap" —
    e.g. they retired before completing a timed lap, or every lap they set
    was deleted/inaccurate. This is a legitimate race outcome, not a bug."""
    pass


def resolve_session(year: int, grand_prix: str, session_type: str = "R") -> Session:
    """Cheaply resolve a session's identity (~10-20ms) without fetching its
    laps/telemetry/weather data. Used to validate a load request fails fast
    on a bad year/grand-prix/session combo, without paying the cost of a
    full data download just to check that."""
    fastf1.Cache.enable_cache(CACHE_DIR)
    return fastf1.get_session(year, grand_prix, session_type)


def load_session(year: int, grand_prix: str, session_type: str = "R") -> Session:
    """Load an F1 session, returns a loaded Session object.

    Even with a fully warm cache this is CPU-bound work (building lap
    tables across every driver) and takes real time — a couple of seconds
    for a long race, much more on a cold cache. Callers that don't need
    the data immediately should prefer resolve_session() and defer this.
    """
    session = resolve_session(year, grand_prix, session_type)
    # Race control messages aren't used anywhere in this app — skip
    # fetching/parsing them to shave a bit off every load.
    session.load(messages=False)
    return session


def get_event_schedule(year: int) -> list:
    """Return Grand Prix event names for a season, excluding pre-season testing."""
    fastf1.Cache.enable_cache(CACHE_DIR)
    schedule = fastf1.get_event_schedule(year)
    events = schedule[schedule["EventFormat"] != "testing"]
    return events.sort_values("RoundNumber")["EventName"].tolist()


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
        DataFrame with Distance, Speed, Throttle, Brake, DRS, RPM, Gear, nGear,
        SessionTime. If laps="all", also includes LapNumber column.
    """
    laps_data = session.laps.pick_drivers(driver_code)
    if laps_data.empty:
        raise DriverNotFound(f"Driver '{driver_code}' not found in session")

    # SessionTime is required to pace the live-telemetry WebSocket replay;
    # Distance requires an explicit add_distance() call — FastF1's raw
    # get_car_data() does not include it.
    cols = ["Distance", "Speed", "Throttle", "Brake", "DRS", "RPM", "Gear", "nGear", "SessionTime"]

    if laps == "all":
        telemetry_list = []
        for _, lap in laps_data.iterrows():
            lap_telemetry = lap.get_car_data().add_distance()
            keep = [c for c in cols if c in lap_telemetry.columns]
            lap_telemetry = lap_telemetry[keep].copy()
            lap_telemetry["LapNumber"] = lap["LapNumber"]
            telemetry_list.append(lap_telemetry)
        return pd.concat(telemetry_list, ignore_index=True)
    else:
        fastest = laps_data.pick_fastest()
        if fastest is None:
            raise NoValidLapError(f"Driver '{driver_code}' has no valid fastest lap in this session")
        telemetry = fastest.get_car_data().add_distance()
        return telemetry[[c for c in cols if c in telemetry.columns]]


def get_sector_times(session: Session, driver_code: str) -> tuple:
    """Return (s1, s2, s3) sector times in seconds for a driver's fastest lap.

    A missing individual sector time (rather than a missing lap entirely)
    comes back as None for that sector.
    """
    laps = session.laps.pick_drivers(driver_code)
    if laps.empty:
        raise DriverNotFound(f"Driver '{driver_code}' not found in session")
    fastest = laps.pick_fastest()
    if fastest is None:
        raise NoValidLapError(f"Driver '{driver_code}' has no valid fastest lap in this session")

    def _seconds(sector_time):
        return None if pd.isna(sector_time) else sector_time.total_seconds()

    return (
        _seconds(fastest["Sector1Time"]),
        _seconds(fastest["Sector2Time"]),
        _seconds(fastest["Sector3Time"]),
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
