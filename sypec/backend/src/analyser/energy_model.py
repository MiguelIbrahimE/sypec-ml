"""
Very first-pass kWh estimator.
Assumes linear CPU load vs. active users and 0.6 Wh / (CPU%·s) coefficient.
"""
from __future__ import annotations
from statistics import mean
from typing import Dict, List

COEFFICIENT_WH_PER_CPU_SECOND = 0.6  # <-- tune this later!


def project_energy_use(metrics: Dict[str, float], user_growth: List[int] | None = None) -> dict:
    """
    Return a projection dict ready for plotting.
    `user_growth` defaults to [10, 100, 1_000, 10_000].
    """
    if user_growth is None:
        user_growth = [10, 100, 1_000, 10_000]

    # Naïve link: complexity * 0.2 → avg CPU seconds per user / day
    cpu_per_user_s = metrics["complexity"] * 0.2
    daily_kwh = [
        users * cpu_per_user_s * COEFFICIENT_WH_PER_CPU_SECOND / 1_000 for users in user_growth
    ]
    return {
        "user_growth": user_growth,
        "daily_kwh": daily_kwh,
        "avg_daily_kwh": mean(daily_kwh),
    }
