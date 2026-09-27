"""Preklad skratiek teamov z ESPN na naše (NBA) skratky."""

from __future__ import annotations

from team_pulse.arenas import table

# ESPN používa pri niektorých teamoch iné skratky než NBA
ESPN_ALIASES = {
    "NY": "NYK",
    "SA": "SAS",
    "GS": "GSW",
    "NO": "NOP",
    "UTAH": "UTA",
    "WSH": "WAS",
    "PHO": "PHX",
    "BRK": "BKN",
}


def our_teams() -> set[str]:
    return set(table()["team"])


def from_espn(abbr: str) -> str:
    """ESPN skratka → naša. Neznáma skratka vyhodí chybu (contract test ju zachytí)."""
    team = ESPN_ALIASES.get(abbr, abbr)
    if team not in our_teams():
        raise KeyError(f"neznáma ESPN skratka teamu: {abbr}")
    return team
