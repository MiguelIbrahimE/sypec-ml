# backend/src/static_analyzer/energy_model.py
def estimate_energy(code_stats: dict, docker_stats: dict) -> dict:
    base_energy = 0.01 * code_stats.get("total_loc", 1000) / 1000
    ram_factor = docker_stats.get("estimated_ram_mb", 256) / 512

    energy_by_users = {
        10: round(base_energy * 10 * ram_factor, 2),
        100: round(base_energy * 100 * ram_factor, 2),
        1000: round(base_energy * 1000 * ram_factor, 2),
        10000: round(base_energy * 10000 * ram_factor, 2),
    }
    return energy_by_users