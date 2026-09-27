"""Pulse: stav teamu pred zápasom v 4 úrovniach, dôvody a istota.

Elo dnes = Elo (vrstva A) + príspevky ostatných vrstiev v Elo bodoch
Pulse    = 50 + (Elo dnes − 1505) / 6        orezané na 0..100 (±300 Elo = celý rozsah)
Úroveň   = Silný ≥ 70 · Stabilný 50–69 · Oslabený 30–49 · Kritický < 30
Pokles   = ak je team dnes o ≥ 60 Elo slabší než normálne → o úroveň nižšie
Dôvody   = najviac 3 príspevky s dopadom nad 10 Elo
"""

from __future__ import annotations

LEAGUE_MEAN = 1505.0
PULSE_SCALE = 6  # pôvodne 4: najlepšie teamy (Elo 1 750+) mali všetky Pulse 100
TIERS = ["Silný", "Stabilný", "Oslabený", "Kritický"]
TIER_FLOORS = [70, 50, 30]  # hranice Pulse pre Silný, Stabilný, Oslabený
DROP_ELO = 60
MIN_REASON_ELO = 10
MAX_REASONS = 3


def pulse_from_elo(elo: float) -> float:
    return max(0.0, min(100.0, 50 + (elo - LEAGUE_MEAN) / PULSE_SCALE))


def tier_index(pulse: float) -> int:
    for i, floor in enumerate(TIER_FLOORS):
        if pulse >= floor:
            return i
    return len(TIER_FLOORS)


def team_state(base_elo: float, contributions: dict[str, float]) -> dict:
    """base_elo = Elo z výsledkov; contributions = dôvod → Elo body (záporné = oslabuje)."""
    today = base_elo + sum(contributions.values())
    pulse = pulse_from_elo(today)
    normal = tier_index(pulse_from_elo(base_elo))
    tier = tier_index(pulse)
    dropped = base_elo - today >= DROP_ELO
    if dropped:
        tier = min(max(tier, normal + 1), len(TIERS) - 1)
    reasons = sorted(
        ((k, v) for k, v in contributions.items() if abs(v) > MIN_REASON_ELO), key=lambda kv: -abs(kv[1])
    )[:MAX_REASONS]
    return {
        "elo": round(base_elo, 1),
        "elo_today": round(today, 1),
        "pulse": round(pulse, 1),
        "tier": TIERS[tier],
        "normal_tier": TIERS[normal],
        "dropped": dropped,
        "reasons": [(k, round(v)) for k, v in reasons],
    }


def confidence(tier_if_all_play: str, tier_if_none_play: str, swing_elo: float, data_age_hours: float) -> str:
    """Istota hodnotenia podľa otáznych hráčov a čerstvosti dát."""
    if tier_if_all_play != tier_if_none_play or swing_elo > 40 or data_age_hours > 6:
        return "nízka"
    if swing_elo > 15 or data_age_hours > 1:
        return "stredná"
    return "vysoká"
