import pytest
import pandas as pd
from src import main as etl  

@pytest.fixture
def sample_json_ok():
    return {
        "hourly": {
            "time": ["2025-08-27T10:00", "2025-08-27T11:00", "2025-08-27T12:00"],
            "temperature_2m": [20.1, 21.3, 22.0],
            "relative_humidity_2m": [60, 58, 55],
            "precipitation": [0.0, 0.2, 0.0],
            "wind_speed_10m": [3.4, 4.1, 3.8],
            "precipitation_probability": [5, 10, 0], 
        }
    }


@pytest.fixture
def sample_json_missing_col():
    # Här saknas relative_humidity_2m helt och precipitation har fel längd
    return {
        "hourly": {
            "time": ["2025-08-27T10:00", "2025-08-27T11:00", "2025-08-27T12:00"],
            "temperature_2m": [20.1, 21.3, 22.0],
            # "relative_humidity_2m": [60, 58, 55],  # medvetet borttagen
            "precipitation": [0.0, 0.2, 0.0, 0.1],  # fel längd
            "wind_speed_10m": [3.4, 4.1, 3.8],
            "precipitation_probability": [5, 10, 0],
        }
    }

#Kollar att transformeringen fungerar när all data är korrekt
def test_transform_ok(sample_json_ok):
    df = etl.transform(sample_json_ok, filter_old_times=False)

    # Förväntade kolumner (svenska)
    expected_cols = {"tid", "temperatur_c", "relativ_fuktighet", "nederbord_mm", "vindhastighet_ms"}
    assert expected_cols.issubset(df.columns)

    # precip_prob används inte -> ska inte finnas som kolumn
    assert "precipitation_probability" not in df.columns

    # Raddräkning & typer
    assert len(df) == 3
    assert pd.api.types.is_datetime64_any_dtype(df["tid"])

    # Rimliga värden
    assert df["temperatur_c"].iloc[0] == pytest.approx(20.1)
    assert df["relativ_fuktighet"].iloc[2] == 55
    assert df["nederbord_mm"].sum() == pytest.approx(0.2)

#Kollar att funktionen klarar av saknade eller felaktiga kolumner
def test_transform_missing_or_bad_lengths(sample_json_missing_col, caplog):
    caplog.clear()
    df = etl.transform(sample_json_missing_col, filter_old_times=False)

    # Fortfarande tre rader (baserat på time)
    assert len(df) == 3

    # precipitation hade fel längd -> blir NaN i nederbord_mm
    assert df["nederbord_mm"].isna().sum() == 3

    # relative_humidity_2m saknades -> blir NaN i relativ_fuktighet
    assert df["relativ_fuktighet"].isna().sum() == 3

    # minst en WARNING ska ha loggats
    assert any(r.levelname == "WARNING" for r in caplog.records)

#Kollar att ogiltiga tidsvärden hanteras rätt
def test_transform_drops_bad_time():
    bad = {
        "hourly": {
            "time": ["2025-08-27T10:00", "NOT_A_TIME", "2025-08-27T12:00"],
            "temperature_2m": [20.1, 21.3, 22.0],
            "relative_humidity_2m": [60, 58, 55],
            "precipitation": [0.0, 0.2, 0.0],
            "wind_speed_10m": [3.4, 4.1, 3.8],
            "precipitation_probability": [5, 10, 0],
        }
    }
    df = etl.transform(bad, filter_old_times=False)
    # Ogiltig tid droppas
    assert len(df) == 2
    assert df["tid"].min().isoformat().startswith("2025-08-27T10:00")