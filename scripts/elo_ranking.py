"""Prepočíta Elo na stiahnutých zápasoch a vypíše rebríček na konci poslednej sezóny."""

import pandas as pd

from team_pulse.elo import EloParams, run

games = pd.read_parquet("data/raw/games.parquet")
teams = set(games["home"]) | set(games["away"])
p = EloParams()
res = run(games, p, initial={t: p.mean for t in teams})

last = res["season"].max()
final: dict[str, float] = {}
for r in res[res["season"] == last].itertuples():
    final[r.home], final[r.away] = r.elo_home_post, r.elo_away_post

rank = pd.Series(final).sort_values(ascending=False).round(0)
print(f"Elo na konci sezóny {last - 1}-{str(last)[-2:]} (vrátane playoff):\n")
print("TOP 5\n" + rank.head(5).to_string())
print("\nPOSLEDNÝCH 5\n" + rank.tail(5).to_string())
