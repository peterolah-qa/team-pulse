"""NHL zranenia z ESPN: preklad klubov a stavov (bez siete, skutočná odpoveď ESPN vo fixture)."""

import json
from pathlib import Path

from team_pulse.nhl import injuries as inj

RAW = json.loads((Path(__file__).parent / "fixtures" / "espn_nhl_injuries.json").read_text(encoding="utf-8"))


def entry(abbr, name, type_name, pos="C", injury="Lower Body", ret=None):
    return {
        "date": "2026-10-12T19:08Z", "type": {"name": type_name},
        "details": {"type": injury, "returnDate": ret},
        "athlete": {"displayName": name, "team": {"abbreviation": abbr}, "position": {"abbreviation": pos}},
    }  # fmt: skip


def test_contract_real_espn_response():
    out = inj.parse(RAW)
    assert list(out) == ["ANA", "BUF", "CGY"]
    assert sum(len(p) for p in out.values()) == 8
    gauthier = next(p for p in out["ANA"] if p["player"] == "Cutter Gauthier")
    assert gauthier == {
        "player": "Cutter Gauthier", "pos": "LW", "status": "DTD", "injury": "Upper Body",
        "return_date": "2026-10-13", "updated": "2026-10-12T19:08Z",
    }  # fmt: skip
    assert {p["status"] for ps in out.values() for p in ps} <= {"OUT", "IR", "DTD"}


def test_espn_abbreviations_map_to_nhl():
    data = {
        "injuries": [
            {
                "injuries": [
                    entry(a, f"P {a}", "INJURY_STATUS_OUT") for a in ("LA", "NJ", "SJ", "TB", "UTAH", "DET")
                ]
            }
        ]
    }
    assert list(inj.parse(data)) == ["DET", "LAK", "NJD", "SJS", "TBL", "UTA"]


def test_sorted_out_first_then_by_name_and_unknown_status_kept():
    data = {
        "injuries": [
            {
                "injuries": [
                    entry("DET", "Zed", "INJURY_STATUS_DAYTODAY"),
                    entry("DET", "Bob", "INJURY_STATUS_IR"),
                    entry("DET", "Amy", "INJURY_STATUS_NEW_THING"),
                    entry("DET", "Cid", "INJURY_STATUS_OUT"),
                    entry("DET", "Abe", "INJURY_STATUS_OUT"),
                ]
            }
        ]
    }
    assert [(p["player"], p["status"]) for p in inj.parse(data)["DET"]] == [
        ("Abe", "OUT"), ("Cid", "OUT"), ("Bob", "IR"), ("Zed", "DTD"), ("Amy", "?"),
    ]  # fmt: skip


def test_skips_entries_without_team_or_name():
    data = {
        "injuries": [
            {"injuries": [entry("", "X", "INJURY_STATUS_OUT"), entry("DET", "", "INJURY_STATUS_OUT")]}
        ]
    }
    assert inj.parse(data) == {}
    assert inj.parse({}) == {}
