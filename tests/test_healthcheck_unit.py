from unittest.mock import patch, MagicMock
from src.smoke_api import api_halsokoll

def test_api_halsokoll_ok():
    # Fejkat svar från Open-Meteo
    fake_json = {
        "hourly": {
            "time": ["2025-08-27T10:00"],
            "temperature_2m": [20.1],
            "precipitation_probability": [5],
        }
    }

    with patch("src.healthcheck.requests.get") as mock_get:
        m = MagicMock()
        m.status_code = 200
        m.json.return_value = fake_json
        mock_get.return_value = m

        res = api_halsokoll()

    assert res["ok"] is True
    assert res["status"] == "OK"
    assert res["missing"] == [] or res["missing"] == ["precipitation"]  # beroende på config