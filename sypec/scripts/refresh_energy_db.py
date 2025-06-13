"""
Optional cron script that updates carbon-intensity coefficients.
Download from electricityMap or Ember APIs, write to data/energy_intensity.json.
"""
import requests
from pathlib import Path
import json

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "energy_intensity.json"

def main():
    resp = requests.get("https://api.electricitymap.org/v3/carbon-intensity/latest")
    resp.raise_for_status()
    DATA_FILE.write_text(json.dumps(resp.json(), indent=2))
    print(f"Updated {DATA_FILE}")

if __name__ == "__main__":
    main()
