"""
Live-hardware profile helper.

We pull the current Steam Hardware Survey JSON (public, no-auth) once a week
and cache the parsed figures in /tmp so repeated analyses are instant.  You
can extend `SOURCE_HANDLERS` with cloud-vendor endpoints later.
"""
from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Literal, TypedDict

import requests  # add to requirements.txt

CACHE_PATH = Path("/tmp/sypec_hw_cache.json")
CACHE_TTL = timedelta(days=7)  # refresh weekly


class HWProfile(TypedDict):
    cpu: str
    gpu: str
    ram_gb: float
    kwh_per_hour: float


def _fetch_steam_survey() -> dict:
    url = (
        "https://store.steampowered.com/hwsurvey/v1?device=pc"
        "&month=latest&format=json"
    )
    logging.debug("Fetching Steam HW survey …")
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _parse_steam(data: dict) -> HWProfile:
    """Take raw Steam JSON → rough ‘average gamer PC’ profile."""
    try:
        # CPU example: “6-core,  3.3 GHz” prevalence
        cpu_row = max(
            data["cpus"]["cpugraph"]["data"],
            key=lambda row: float(row["pct"])
        )
        gpu_row = max(
            data["gpus"]["gpugraph"]["data"],
            key=lambda row: float(row["pct"])
        )
        ram_row = max(
            data["ram"]["ramgraph"]["data"],
            key=lambda row: float(row["pct"])
        )
        # crude mapping: 1 GB RAM ≈ 0.003 kWh/h idle desktop
        ram_gb = float(ram_row["name"].split()[0])
    except Exception as exc:  # noqa: BLE001
        logging.warning("Steam survey parse failed: %s", exc)
        return {
            "cpu": "unknown",
            "gpu": "unknown",
            "ram_gb": 8.0,
            "kwh_per_hour": 0.1,
        }
    return {
        "cpu": cpu_row["name"],
        "gpu": gpu_row["name"],
        "ram_gb": ram_gb,
        "kwh_per_hour": round(0.05 + ram_gb * 0.003, 3),
    }


SOURCE_HANDLERS = {
    "steam_pc": (_fetch_steam_survey, _parse_steam),
}


def _load_cache() -> dict[str, HWProfile]:
    if CACHE_PATH.exists() and (
            datetime.fromtimestamp(CACHE_PATH.stat().st_mtime) > datetime.now() - CACHE_TTL
    ):
        try:
            return json.loads(CACHE_PATH.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_PATH.write_text(json.dumps(cache))
    except OSError:
        pass


def get_live_profile(profile_name: Literal["desktop", "cloud", "mobile"] = "desktop") -> HWProfile:
    """
    Return a HWProfile dict, refreshing remote data if the cache is stale.

    profile_name:
        - desktop  -> Steam PC profile
        - cloud    -> hard-coded best-guess (update later)
        - mobile   -> hard-coded best-guess (update later)
    """
    cache = _load_cache()

    # ---------------- desktop via Steam ----------------
    if profile_name == "desktop":
        if "steam_pc" not in cache:
            fetch, parse = SOURCE_HANDLERS["steam_pc"]
            cache["steam_pc"] = parse(fetch())
            _save_cache(cache)
        return cache["steam_pc"]

    # ---------------- cloud & mobile placeholders ----------------
    if profile_name == "cloud":
        return {
            "cpu": "AMD EPYC 7763",
            "gpu": "NVIDIA A100",
            "ram_gb": 256,
            "kwh_per_hour": 0.4,
        }
    if profile_name == "mobile":
        return {
            "cpu": "Apple A17 Pro",
            "gpu": "integrated",
            "ram_gb": 8,
            "kwh_per_hour": 0.035,
        }
    raise ValueError(f"Unknown profile '{profile_name}'")
