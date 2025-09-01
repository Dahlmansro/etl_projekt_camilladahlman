import os
import time
import logging
from datetime import datetime
import requests
import pandas as pd
from sqlalchemy import create_engine, text
import yaml
from dotenv import load_dotenv

# Modul-logger
logger = logging.getLogger(__name__)

# Loggning
def setup_logging(log_file: str) -> None:
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler()
        ],
    )

# Konfiguration
def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

# API-hämtning
def fetch_weather(base_url: str, params: dict, timeout: int, retries: int, backoff: int) -> dict:
    session = requests.Session()
    headers = {"User-Agent": f"ETL-Flow/1.0 (+https://example.local)"}
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(base_url, params=params, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_err = e
            logger.warning(f"Försök {attempt}/{retries} misslyckades: {e}")
            if attempt < retries:
                time.sleep(backoff * attempt)

    logger.error("API failed")
    raise RuntimeError(f"API-anrop misslyckades efter {retries} försök: {last_err}")

# Transformering
def transform(json_data: dict, filter_old_times: bool = True) -> pd.DataFrame:
    hourly = json_data.get("hourly", {})
    times = hourly.get("time", [])
    n = len(times)

    def col(name: str):
        vals = hourly.get(name)
        if vals is None or len(vals) != n:
            logger.warning(f"Kolumn {name} saknas eller har fel längd – fyller med NaN")
            return [None] * n
        return vals

    df = pd.DataFrame({
        "tid": pd.to_datetime(times, errors="coerce"),
        "temperatur_c": pd.to_numeric(col("temperature_2m"), errors="coerce"),
        "relativ_fuktighet": pd.to_numeric(col("relative_humidity_2m"), errors="coerce"),
        "nederbord_mm": pd.to_numeric(col("precipitation"), errors="coerce"),
        "vindhastighet_ms": pd.to_numeric(col("wind_speed_10m"), errors="coerce"),
    })

    # Varningar för NaN
    nan_counts = df.isna().sum()
    for col_name, count in nan_counts.items():
        if count > 0:
            logger.warning(f"{count} ogiltiga värden i kolumn '{col_name}' ersattes med NaN")

    # Rader utan tid
    before = len(df)
    df = df.dropna(subset=["tid"])
    dropped = before - len(df)
    if dropped > 0:
        logger.warning(f"{dropped} rader togs bort pga saknad eller ogiltig tid")

    # Timestamp
    now_stockholm = pd.Timestamp.now(tz="Europe/Stockholm").tz_localize(None)
    df = df.copy()
    df["laddad_tid"] = now_stockholm

    if filter_old_times:
        cut = now_stockholm.floor("h")
        pre = len(df)
        df = df[df["tid"] >= cut]
        logger.info(f"Filtrerade bort {pre - len(df)} passerade timmar (cut={cut})")

    return df

# Skapar databas 
def ensure_table(engine, table_name: str):
    ddl = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        tid TEXT PRIMARY KEY,
        temperatur_c REAL,
        relativ_fuktighet REAL,
        nederbord_mm REAL,
        vindhastighet_ms REAL,
        laddad_tid TEXT NOT NULL
    );
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))

def clear_table(engine, table_name: str):
    from sqlalchemy import text
    with engine.begin() as conn:
        conn.execute(text(f"DELETE FROM {table_name}"))

def write_sqlite(df: pd.DataFrame, sqlite_path: str, table_name: str):
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    engine = create_engine(f"sqlite:///{sqlite_path}", future=True)
    ensure_table(engine, table_name)

    if df.empty:
        logger.info("Inget att skriva – DataFrame är tom.")
        return

    # Töm tabellen så den alltid bara innehåller senaste 4 timmar (för att inte samala massa data just nu)
    clear_table(engine, table_name)

    inserted, updated = 0, 0
    with engine.begin() as conn:
        for _, r in df.iterrows():
            result = conn.execute(
                text(f"""
                    INSERT INTO {table_name} (tid, temperatur_c, relativ_fuktighet, nederbord_mm, vindhastighet_ms, laddad_tid)
                    VALUES (:tid, :temperatur_c, :relativ_fuktighet, :nederbord_mm, :vindhastighet_ms, :laddad_tid)
                    ON CONFLICT(tid) DO UPDATE SET
                        temperatur_c=excluded.temperatur_c,
                        relativ_fuktighet=excluded.relativ_fuktighet,
                        nederbord_mm=excluded.nederbord_mm,
                        vindhastighet_ms=excluded.vindhastighet_ms,
                        laddad_tid=excluded.laddad_tid
                """),
                {
                    "tid": r["tid"].isoformat(),
                    "temperatur_c": r["temperatur_c"],
                    "relativ_fuktighet": r["relativ_fuktighet"],
                    "nederbord_mm": r["nederbord_mm"],
                    "vindhastighet_ms": r["vindhastighet_ms"],
                    # --- ÄNDRAT: spara som ISO-sträng i DB ---
                    "laddad_tid": r["laddad_tid"].isoformat(),
                }
            )
            inserted += 1
    logger.info(f"Skrev {len(df)} rader till {sqlite_path}:{table_name}")

# Huvudprogram
def main():
    start_time = time.time()
    try:
        load_dotenv()
        cfg = load_config("config.yaml")
        setup_logging(cfg["run"]["log_file"])

        logger.info("=== Startar ETL-körning (Open-Meteo → SQLite) ===")
        logger.debug("Konfiguration laddad.")

        # API
        logger.info("Startar API-hämtning...")
        json_data = fetch_weather(
            base_url=cfg["api"]["base_url"],
            params=cfg["api"]["params"],
            timeout=cfg["run"]["timeout_seconds"],
            retries=cfg["run"]["max_retries"],
            backoff=cfg["run"]["backoff_seconds"],
        )
        approx_bytes = len(str(json_data).encode("utf-8"))
        logger.info("API-hämtning klar, ~%d bytes rådata mottagna.", approx_bytes)

        # Transform
        logger.info("Startar transformering...")
        df = transform(json_data)
        logger.info("Transformering klar, %d rader i DataFrame.", len(df))

        # Metadata före filtrering
        if df.empty:
            logger.warning("DataFrame är tom efter transformering – inget att skriva.")
        else:
            try:
                logger.info("DataFrame metadata: %d rader, %d kolumner.", df.shape[0], df.shape[1])
                logger.info("Tidsintervall i data: %s till %s.", df["tid"].min(), df["tid"].max())
            except Exception as meta_err:
                logger.debug("Kunde inte beräkna tidsintervall/metadata: %s", meta_err)

        # Behåll endast senaste 4 timmar
        if not df.empty:
            try:
                now = pd.Timestamp.now().tz_localize(None)
            except Exception:
                now = pd.Timestamp.now()  

            past = df[df["tid"] <= now].sort_values("tid")
            if len(past) >= 4:
                df = past.tail(4)
                logger.info("Filtrerat till senaste 4 historiska timmar: %s → %s.",
                            df["tid"].iloc[0], df["tid"].iloc[-1])
            else:
                future = df[df["tid"] > now].sort_values("tid")
                df = pd.concat([past, future.head(4 - len(past))]).sort_values("tid")
                logger.info("Hade bara %d historiska timmar; fyllde upp med %d kommande. Intervall: %s → %s.",
                            len(past), max(0, 4 - len(past)), df["tid"].iloc[0], df["tid"].iloc[-1])

        # Skrivning till SQLite 
        logger.info("Startar skrivning till SQLite (%s:%s)...",
                    cfg["storage"]["sqlite_path"], cfg["storage"]["table_name"])
        write_sqlite(df, cfg["storage"]["sqlite_path"], cfg["storage"]["table_name"])
        logger.info("Databasuppdatering klar.")

        elapsed = time.time() - start_time
        logger.info("=== ETL-körning klar på %.2f sekunder ===", elapsed)

    except Exception as e:
        logger.exception("ETL-körning avbröts av fel: %s", e)
        raise

# Körskydd
if __name__ == "__main__":
    main()