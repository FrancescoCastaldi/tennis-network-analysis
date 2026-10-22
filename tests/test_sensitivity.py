import pandas as pd

from tennis_networks.sensitivity import build_variants, same_verdict


def raw_matches():
    rows = [
        ("Completed", "Hard"),
        ("Completed", "Carpet"),
        ("Retired", "Clay"),
        ("rrtired", "Grass"),
        ("Walkover", "Clay"),
    ]
    df = pd.DataFrame(rows, columns=["comment", "surface"])
    df["winner"] = [f"W{i}" for i in range(len(df))]
    df["loser"] = [f"L{i}" for i in range(len(df))]
    return df


def test_each_variant_changes_one_choice_of_the_baseline():
    variants = build_variants(raw_matches())
    assert len(variants["baseline"]) == 4  # the walkover is dropped
    assert len(variants["no_retirements"]) == 2  # both spellings of a retirement are dropped
    assert len(variants["walkovers_kept"]) == 5
    assert (variants["baseline"]["surface"] == "Carpet").sum() == 1
    assert (variants["carpet_as_hard"]["surface"] == "Carpet").sum() == 0
    assert (variants["carpet_as_hard"]["surface"] == "Hard").sum() == 2


def test_same_verdict_needs_every_p_value_on_one_side_of_alpha():
    assert same_verdict([0.01, 0.04])
    assert same_verdict([0.06, 0.4])
    assert not same_verdict([0.04, 0.06])
