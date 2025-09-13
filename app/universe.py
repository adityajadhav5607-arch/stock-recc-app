# universe.py
import csv
from collections import defaultdict
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data" / "universe.csv"

GOALS = defaultdict(lambda: {"core": [], "note": ""})

NOTES = {
  "information_technology": "Software, semis, and IT services; higher growth & volatility.",
  "health_care": "Pharma, biotech, devices; defensive with innovation pockets.",
  "financials": "Banks, insurers, asset managers; rate-sensitive.",
  "consumer_discretionary": "Retail, autos, travel; cyclicals.",
  "consumer_staples": "Food, beverages, household; defensive cash flows.",
  "energy": "Integrated, E&P, midstream, services; commodity-driven.",
  "industrials": "Machinery, rails, defense, logistics; broad cyclicals.",
  "materials": "Chemicals, metals/mining, packaging; commodity exposure.",
  "utilities": "Regulated electric/gas/water; income + rate sensitivity.",
  "real_estate": "REITs across property types; income-oriented.",
  "communication_services": "Search, social, streaming, telecom; ads & subscriptions.",
}

with DATA_PATH.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        goal = row["goal"].strip()
        tags = [t.strip() for t in row["tags"].split(",") if t.strip()]
        GOALS[goal]["core"].append({
            "symbol": row["symbol"].strip(),
            "name": row["name"].strip(),
            "type": row["type"].strip(),  # "ETF" or "Stock"
            "tags": tags,
        })
        if not GOALS[goal]["note"]:
            GOALS[goal]["note"] = NOTES.get(goal, "")

SUPPORTED_GOALS = list(GOALS.keys())
