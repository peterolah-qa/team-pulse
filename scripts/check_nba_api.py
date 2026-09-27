"""Overí, že nba_api funguje z tohto počítača: stiahne sezónu 2024-25."""

import time

from nba_api.stats.endpoints import leaguegamefinder

start = time.time()
r = leaguegamefinder.LeagueGameFinder(
    season_nullable="2024-25",
    league_id_nullable="00",
    season_type_nullable="Regular Season",
    timeout=60,
)
df = r.get_data_frames()[0]
elapsed = time.time() - start

print(f"Riadkov: {len(df)}  (čakáme 2460 = 1230 zápasov × 2 teamy)")
print(f"Zápasov: {df['GAME_ID'].nunique()}")
print(f"Čas: {elapsed:.1f} s")
print(df[["GAME_DATE", "MATCHUP", "PTS", "WL"]].head(4).to_string(index=False))
