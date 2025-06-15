# add at top
from .hardware_profiles import get_live_profile

# ...
def estimate_energy(                     #  ←-- new signature
        code_stats: dict,
        docker_stats: dict,
        profile_hint: str,
        api_list: list[str] | None = None,
        client_heavy: bool = False,
) -> dict[int, float]:
    """
    Return kWh / *day* at 10 · 100 · 1 000 · 10 000 users

    We now:
    • add +15 % if client_heavy (SPAs, WASM, …)
    • add +8 % per external API in *api_list*
    """
    base = code_stats["loc"] / 10_000 * 0.2  # (trivial heuristic)

    multiplier = 1.0
    if client_heavy:
        multiplier += 0.15
    if api_list:
        multiplier += 0.08 * len(api_list)

    return {u: round(base * (u ** 0.75) * multiplier, 2) for u in (10, 100, 1000, 10000)}
