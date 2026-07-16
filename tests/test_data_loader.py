import pytest
import pandas as pd
from data_loader import load_session, get_drivers, get_driver_telemetry, get_sector_times, get_weather


class TestDataLoader:
    def test_load_session(self):
        session = load_session(2023, "Bahrain", "R")
        assert session is not None
        assert hasattr(session, "results")

    def test_get_drivers(self):
        session = load_session(2023, "Bahrain", "R")
        drivers = get_drivers(session)
        assert len(drivers) > 0
        assert all(isinstance(d, str) for d in drivers)

    def test_get_driver_telemetry(self):
        session = load_session(2023, "Bahrain", "R")
        telemetry = get_driver_telemetry(session, "VER")
        assert isinstance(telemetry, pd.DataFrame)
        assert "Speed" in telemetry.columns
        assert "Throttle" in telemetry.columns
        assert len(telemetry) > 0

    def test_get_sector_times(self):
        session = load_session(2023, "Bahrain", "R")
        s1, s2, s3 = get_sector_times(session, "VER")
        assert s1 > 0 and s2 > 0 and s3 > 0

    def test_get_weather(self):
        session = load_session(2023, "Bahrain", "R")
        weather = get_weather(session)
        assert isinstance(weather, dict)
        assert "track_temp" in weather
        assert "air_temp" in weather
        assert "rainfall" in weather
        assert isinstance(weather["track_temp"], (int, float))
        assert isinstance(weather["air_temp"], (int, float))
        assert isinstance(weather["rainfall"], bool)

    def test_get_driver_telemetry_all_laps(self):
        session = load_session(2023, "Bahrain", "R")
        telemetry = get_driver_telemetry(session, "VER", laps="all")
        assert isinstance(telemetry, pd.DataFrame)
        assert not telemetry.empty
        assert "LapNumber" in telemetry.columns
        assert "Speed" in telemetry.columns
        # Should have more rows than a single fastest lap
        fast = get_driver_telemetry(session, "VER")
        assert len(telemetry) > len(fast)

    def test_get_driver_telemetry_invalid_driver(self):
        from data_loader import DriverNotFound
        session = load_session(2023, "Bahrain", "R")
        with pytest.raises(DriverNotFound):
            get_driver_telemetry(session, "ZZZ")
