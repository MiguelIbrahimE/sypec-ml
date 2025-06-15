# add at top
from .hardware_profiles import get_live_profile

def estimate_energy(
        code_stats: dict,
        docker_stats: dict,
        usage_levels=(10, 100, 1000, 10000),
        profile_hint: str | None = None,
) -> dict[int, float]:
    """
    Very rough model:
    • HW baseline kWh/h from live hardware profile
    • CPU-intensity proxy = (loc / 10_000)  +  docker RAM (GB) × 0.02
    • Linear scale with active users (should be replaced by load-test data)
    """
    profile = get_live_profile(profile_hint or "desktop")
    base = profile["kwh_per_hour"]
    ram_gb = docker_stats.get("estimated_ram_mb", 256) / 1024
    loc = code_stats.get("loc", 1)

    load_factor = (loc / 10_000) + (ram_gb * 0.02)
    energy = {}
    for u in usage_levels:
        energy[u] = round(base * load_factor * (u ** 0.7), 2)  # sub-linear scale
    return energy
