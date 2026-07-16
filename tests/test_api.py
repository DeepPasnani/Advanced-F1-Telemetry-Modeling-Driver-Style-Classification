import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


class TestAPI:
    def test_list_sessions(self):
        resp = client.get("/sessions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert isinstance(data.get("data"), list)

    def test_load_and_analyze(self):
        # Load a session
        load_resp = client.post("/sessions/load", json={
            "year": 2023,
            "grand_prix": "Bahrain",
            "session_type": "R"
        })
        assert load_resp.status_code == 200
        session_id = load_resp.json()["data"]["session_id"]

        # List drivers
        drivers_resp = client.get(f"/sessions/{session_id}/drivers")
        assert drivers_resp.status_code == 200
        drivers = drivers_resp.json()["data"]
        assert len(drivers) > 0

        # Run analysis on first 3 drivers
        analyze_resp = client.post(f"/sessions/{session_id}/analyze", json={
            "driver_codes": drivers[:3]
        })
        assert analyze_resp.status_code == 200
        analysis_id = analyze_resp.json()["data"]["analysis_id"]

        # Get report
        report_resp = client.get(f"/analysis/{analysis_id}/report")
        assert report_resp.status_code == 200
        assert len(report_resp.json()["data"]["report"]) > 0

    def test_invalid_session(self):
        resp = client.get("/sessions/nonexistent/drivers")
        assert resp.status_code == 404
