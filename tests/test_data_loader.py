import pytest
import pandas as pd
from data_loader import load_session, get_drivers, get_driver_telemetry, get_sector_times


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

    def test_get_driver_telemetry_invalid_driver(self):
        from data_loader import DriverNotFound
        session = load_session(2023, "Bahrain", "R")
        with pytest.raises(DriverNotFound):
            get_driver_telemetry(session, "ZZZ")
