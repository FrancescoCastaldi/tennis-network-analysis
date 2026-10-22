import pandas as pd
import pytest

from tennis_networks.source_check import pair_agreement, player_wins


def atp_matches():
    rows = [
        # winner, loser, date
        ("Aaa A.", "Bbb B.", "2004-03-01"),
        ("Aaa A.", "Bbb B.", "2005-03-01"),
        ("Ccc C.", "Aaa A.", "2006-03-01"),
        ("Ddd D.", "Aaa A.", "2007-03-01"),
        ("Ddd D.", "Aaa A.", "2008-03-01"),
        ("Eee E.", "Ccc C.", "2009-03-01"),
        # Old has a match before 2003: their pairs have a Michieli weight from earlier years and are left out.
        ("Old O.", "Zzz Z.", "2001-03-01"),
        ("Old O.", "Bbb B.", "2008-03-01"),
    ]
    df = pd.DataFrame(rows, columns=["winner", "loser", "date"])
    df["date"] = pd.to_datetime(df["date"])
    return df


def michieli_wins():
    # Same wins, except: Aaa beat Bbb 3 times (Michieli higher), Ddd beat Aaa once (tennis-data higher),
    # and Eee beat Ccc is missing.
    return pd.DataFrame(
        {
            "source": ["Bbb B.", "Aaa A.", "Aaa A."],
            "target": ["Aaa A.", "Ccc C.", "Ddd D."],
            "weight": [3, 1, 1],
        }
    )


def test_pair_agreement_classifies_pairs_between_whole_career_players():
    out = pair_agreement(atp_matches(), michieli_wins()).set_index("outcome")
    assert out["pairs"].to_dict() == {
        "identical": 1,
        "Michieli higher": 1,
        "tennis-data higher": 1,
        "absent in Michieli": 1,
    }
    assert out["share"].sum() == pytest.approx(1.0)


def test_player_wins_keeps_players_with_a_whole_career_in_the_window():
    out = player_wins(atp_matches(), michieli_wins()).set_index("player")
    # Aaa debuts in 2004 and wins in both sources; Eee has no win in Michieli and is left out.
    assert out.loc["aaa a.", "wins_tennis_data"] == 2
    assert out.loc["aaa a.", "wins_michieli"] == 3
    assert "eee e." not in out.index
