# ETL Väder – Automatiserat ETL-flöde från Open-Meteo API

I detta projekt har jag byggt ett **automatiserat ETL-flöde** som hämtar väderdata från [Open-Meteo API](https://open-meteo.com/), 
transformerar det och sparar det i en SQLite-databas. Flödet loggar både normal körning och eventuella fel. 

---

## 🎯 Projektets olika delar
- Bygga ett Pythonbaserat ETL-flöde.  
- Uppdatera en SQL-tabell (SQLite).  
- Hantera exceptions och logga dem i en loggfil.  
- Skriva automatiska tester i ett separat skript.  
- Dokumentera koden enligt standard.  
<<<<<<< HEAD
- Göra projektet körbart både manuellt och via schemaläggning (Windows/Mac).  
=======
- Göra projektet körbart både manuellt och via schemaläggning 
>>>>>>> 6b5eb0a3f52360fbc974d286b74458ec96b20420

---

## 🗂 Projektstruktur

```bash
etl_vader/
│
├── src/                 
│   ├── main.py          # Huvudflödet (exekveras manuellt eller via schemaläggning)
│   ├── smoke_api.py     # Hälsokontroller av API
│
├── tests/               
│   ├── test_main.py
│   └── test_healthcheck_unit.py
│
├── data/                # Databas & rådata
│   └── weather.db       # SQLite-databas med tabellen weather_forecast
│
├── logs/                
│   └── etl.log
│
├── config.yaml          # Projektets konfigurationsfil (API-parametrar, DB, loggning)
├── requirements.txt     # Python-paket för projektet
└── README.md            


````

## ⚙️ Tekniker & bibliotek

* **Python 3.12**
* **SQLite** för lagring
* **PyYAML** för konfiguration
* **Requests** för API-anrop
* **Pandas** för datahantering
* **Logging** för loggfiler (inklusive exceptions)
* **Pytest** för tester

---

## 🚀 Kom igång

### 1. Klona projektet

```bash
git clone <repo-url>
cd etl_vader
```

### 2. Skapa och aktivera virtuell miljö

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows PowerShell
```

### 3. Installera beroenden

```bash
pip install -r requirements.txt
```

### 4. Kör ETL-flödet manuellt

```bash
python src/main.py
```

### 5. Schemalägg körning

* **Windows**: använd **Schemaläggaren**. [Guide här](https://www.youtube.com/watch?v=HAOP0HZeDJg)
* **Mac/Linux**: använd **cron**. [Guide här](https://www.youtube.com/watch?v=mEgSGUe2BvU)

---

## 📡 Hämtad data

ETL-flödet hämtar timvis väderdata från **Open-Meteo API** för vald plats (Lundbyskog, lat 59.067, lon 15.752). 
Följande parametrar ingår i hämtningen:

- **temperature_2m** – Lufttemperatur 2 meter över mark (°C).  
- **relative_humidity_2m** – Relativ luftfuktighet 2 meter över mark (%).  
- **precipitation** – Nederbördsmängd (mm).  
- **wind_speed_10m** – Vindhastighet 10 meter över mark (m/s).  
- **precipitation_probability** – Sannolikhet för nederbörd (%).  

Data lagras timme för timme i tabellen `weather_forecast` i `weather.db`.
Varje körning uppdaterar tabellen med aktuell prognos 7 dagar framåt.

---

## 📊 Output

* **SQLite-databas:** `data/weather.db`

  * Tabell: `weather_forecast`
* **Loggar:** `logs/etl.log`

Exempel på logg:

```
2025-08-28 17:09:30,813 | INFO | Startar transformering...
2025-08-28 17:09:30,849 | INFO | Transformering klar, 168 rader i DataFrame.
2025-08-28 17:09:30,849 | INFO | DataFrame metadata: 168 rader, 5 kolumner.
2025-08-28 17:09:30,849 | INFO | Tidsintervall i data: 2025-08-28 00:00:00 till 2025-09-03 23:00:00.
```

---

## ✅ Tester

Tester finns i mappen **tests/** och körs med **pytest**:

```bash
pytest
```

Exempel:

* `test_healthcheck_unit.py` testar hälsokontroll och att API-svar hanteras.
* `test_main.py` testar ETL-transformering och datainläsning.

---

## 🔮 Vidareutveckling

* Skapa beräkning av frostrisk
* Skicka push till telefonen om risk upptäcks
---

👩‍💻 Projektet utvecklas av *Camilla Dahlman* inom kursen **Data Science (Kunskapskontroll 1)**.

```


