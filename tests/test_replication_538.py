"""Replikačný test: naše Elo musí sedieť s archívom FiveThirtyEight.

Archív sa necommituje; stiahni ho do data/ref/nba_elo.csv (pozri README).
Bez archívu sa test preskočí.
"""

import pytest

from team_pulse.replicate_538 import REF, compare

pytestmark = pytest.mark.skipif(not REF.exists(), reason="chýba archív data/ref/nba_elo.csv")


def test_matches_538_archive_since_2000():
    r = compare(from_season=2000)
    assert r["games"] > 30_000
    assert r["elo_mae"] < 0.05  # priemerná odchýlka pod 0,05 Elo
    assert r["share_within_1"] > 0.99  # 99 % zápasov do 1 Elo bodu
    assert r["prob_max"] < 0.01  # pravdepodobnosť nikde neodbehne o viac ako 1 p. b.
