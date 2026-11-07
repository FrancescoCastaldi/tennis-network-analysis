"""The numbers quoted in report/main.tex must match the committed results in results/tables/.

Each check recomputes a value from a results file and compares it with the rounded
value written in the report. A change to the results or to the text that breaks
the agreement fails here, before it reaches the PDF.
"""

from __future__ import annotations

import pandas as pd
import pytest

from tennis_networks.config import TABLES

REPORT = (TABLES.parent.parent / "report" / "main.tex").read_text(encoding="utf-8")

NINE = [
    "td_atp_2000_2006", "td_atp_2007_2012", "td_atp_2013_2018", "td_atp_2019_2025",
    "td_atp_clay", "td_atp_grass", "td_atp_hard", "td_atp_2007_2025", "td_wta_2007_2025",
]


def _csv(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / name, encoding="utf-8-sig")


def _range(values, digits: int) -> tuple[str, str]:
    lo, hi = min(values), max(values)
    return f"{lo:.{digits}f}", f"{hi:.{digits}f}"


def test_densities_and_giant_components():
    g = _csv("global_measures.csv").set_index("network").loc[NINE]
    lo, hi = _range(g["density"], 3)
    assert f"from {lo} to {hi}" in REPORT
    lo, hi = _range(g["giant_fraction"] * 100, 1)
    assert f"{lo}\\% to {hi}\\%" in REPORT


def test_path_lengths_and_diameters():
    g = _csv("global_measures.csv").set_index("network").loc[NINE]
    lo, hi = _range(g["avg_path_giant"], 1)
    assert f"between {lo} and {hi} steps" in REPORT
    assert g["diameter_giant"].max() <= 9 and "never above 9" in REPORT


def test_reciprocity_and_modularity():
    g = _csv("global_measures.csv").set_index("network")
    assert f"{g.loc['td_atp_hard', 'reciprocity']:.2f}" == "0.28" and "0.28 on hard courts" in REPORT
    assert f"{g.loc['td_atp_clay', 'reciprocity']:.2f}" == "0.21" and "0.21 on clay" in REPORT
    assert f"{g.loc['td_atp_grass', 'reciprocity']:.3f}" == "0.086" and "Grass courts are the exception at 0.086" in REPORT
    surfaces = g.loc[["td_atp_clay", "td_atp_grass", "td_atp_hard"], "modularity"]
    assert f"{surfaces.mean():.2f}" == "0.38" and "0.38 on the surfaces" in REPORT


def test_gini_and_centralization_ranges():
    g = _csv("global_measures.csv").set_index("network").loc[NINE]
    lo, hi = _range(g["gini_in_strength"], 2)
    assert f"from {lo} to {hi}" in REPORT
    lo, hi = _range(g["degree_centralization"], 2)
    assert f"from {lo} to {hi}" in REPORT


def test_small_world_index():
    s = _csv("structure_summary.csv").set_index("network")
    eras = s.loc[["td_atp_2000_2006", "td_atp_2007_2012", "td_atp_2013_2018", "td_atp_2019_2025"], "sw_sigma"]
    assert all(v < 1 for v in eras)
    lo, hi = _range(eras, 2)
    assert f"is {lo} to {hi} in the four ATP eras" in REPORT
    rest = s.loc[["td_atp_clay", "td_atp_grass", "td_atp_hard", "td_atp_2007_2025", "td_wta_2007_2025"], "sw_sigma"]
    lo, hi = _range(rest, 2)
    assert f"{lo} to {hi} for the surfaces" in REPORT


def test_core_and_hits():
    s = _csv("structure_summary.csv").set_index("network").loc[NINE]
    lo, hi = _range(s["core_share"] * 100, 0)
    assert f"{lo}\\% to {hi}\\%" in REPORT
    lo, hi = _range(s["core_share_top100"] * 100, 0)
    assert f"{lo}\\% and {hi}\\%" in REPORT
    lo, hi = _range(s["core_kcore_jaccard"], 2)
    assert f"from {lo} to {hi}" in REPORT
    lo, hi = _range(s["authority_pagerank_spearman"], 2)
    assert f"between {lo} and {hi}" in REPORT
    hub = _csv("structure_summary.csv").set_index("network").loc[NINE, "hub_rank_spearman"]
    assert f"{hub.min():.2f}".startswith("-0.8") and "$-0.61$" in REPORT


def test_rich_club_range():
    rc = _csv("rich_club_summary.csv").set_index("network").loc[NINE]
    lo, hi = _range(rc["rho_rich_peak"], 3)
    assert f"from {lo} to {hi}" in REPORT
    assert rc["p_max"].max() == pytest.approx(1 / 201, abs=1e-4) and "$p = 0.005$" in REPORT


def test_compactness_and_communities():
    c = _csv("compactness.csv").set_index("network").loc[NINE]
    lo, hi = _range(c["distance_ratio"], 2)
    assert f"{lo} to {hi} times" in REPORT
    lo, hi = _range(c["global_efficiency"], 2)
    assert f"between {lo} and {hi}" in REPORT
    g = _csv("global_measures.csv").set_index("network").loc[NINE]
    assert int(g.loc["td_atp_grass", "communities"]) == 3 and int(g.loc["td_wta_2007_2025", "communities"]) == 15
    assert "between 3 communities (grass) and 15 (WTA)" in REPORT


def test_h_verdicts_and_p_values():
    h = _csv("hypothesis_tests.csv")
    def p(hyp, needle=None):
        rows = h[h["hypothesis"] == hyp]
        if needle:
            rows = rows[rows["comparison"].str.contains(needle, regex=False)]
        return float(rows["p_value"].iloc[0])
    assert f"{p('H1'):.3f}" == "0.060" and "$p = 0.060$" in REPORT
    assert f"{p('H3', 'Grass vs Clay'):.3f}" in ("0.015", "0.005")
    assert "$p = 0.015$" in REPORT and "$p = 0.005$" in REPORT
    assert f"{p('H4', 'WTA'):.3f}" == "0.016" and "$p = 0.016$" in REPORT


def test_h5_and_h6_values():
    t = _csv("triads_h5.csv")
    h5 = t[t["hypothesis"] == "H5"].iloc[0]
    assert f"{h5['value_a']:.3f}" == "0.184" and f"{h5['value_b']:.3f}" == "0.211"
    assert "0.184 against 0.211" in REPORT
    lv = _csv("levels_tests.csv")
    r2 = lv[lv["note"].astype(str).str.startswith("R2")]["note"].str.extract(r"= ([0-9.]+)")[0].astype(float)
    lo, hi = _range(r2 * 100, 0)
    assert f"{lo}\\% to {hi}\\%" in REPORT


def test_dyadic_and_mixed_correlations():
    lv = _csv("levels_tests.csv")
    h7 = lv[lv["hypothesis"] == "H7"]["value"].astype(float).round(3).tolist()
    assert "$r = 0.149$" in REPORT and "$r = 0.123$" in REPORT and 0.149 in h7
    h8 = lv[lv["hypothesis"] == "H8"]["value"].astype(float).round(3).tolist()
    assert "$r = 0.056$" in REPORT and "$r = -0.094$" in REPORT and 0.056 in h8


def test_validity_numbers():
    rep = _csv("michieli_reproduction.csv")
    m3 = rep[rep["measure"].str.contains("clustering", case=False)].iloc[0]
    assert f"{m3['ours']:.3f}" == "0.311" and "$C = 0.311$" in REPORT
    v = _csv("td_validity_michieli.csv")
    share = float(v.loc[v.iloc[:, 0].str.contains("loser-winner"), v.columns[-1]].iloc[0])
    assert f"{100 * share:.1f}" == "97.6" and "97.6\\% of loser-winner pairs" in REPORT


def test_sensitivity_p_values():
    s = _csv("sensitivity_tests.csv")
    h1 = s[(s["hypothesis"] == "H1") & (s["statistic"] == "top10_pagerank_share")]
    got = {r.variant: round(float(r.p_value), 3) for r in h1.itertuples()}
    assert got["no_retirements"] == 0.036 and got["walkovers_kept"] == 0.053 and got["baseline"] == 0.06
    assert "$p = 0.036$" in REPORT and "$0.053$" in REPORT
