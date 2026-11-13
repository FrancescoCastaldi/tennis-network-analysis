import re

import numpy as np
import pandas as pd
import pytest

from tennis_networks import report_assets as ra


@pytest.fixture(autouse=True)
def out_dirs(tmp_path, monkeypatch):
    """Write the generated tables and figures to a temporary folder, not to report/."""
    monkeypatch.setattr(ra, "OUT_TAB", tmp_path / "tables")
    monkeypatch.setattr(ra, "OUT_FIG", tmp_path / "figures")
    return tmp_path


def test_table_structure_generates_file(out_dirs):
    ra.table_structure()
    path = out_dirs / "tables" / "tab_structure.tex"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert r"\begin{tabular}" in content
    assert r"\end{tabular}" in content
    assert "HITS centrality" in content
    assert "Borgatti-Everett discrete core-periphery model" in content
    assert "Structural equivalence" in content
    assert "Small-world topology" in content
    assert "Rich-club elite closure" in content
    # Check that all 9 networks are present in the header
    for net_short in ["2000-06", "2007-12", "2013-18", "2019-25", "Clay", "Grass", "Hard", "ATP 07-25", "WTA 07-25"]:
        assert net_short in content
    # Ensure no NaN values leak into the LaTeX output
    assert re.search(r"\bnan\b", content, re.IGNORECASE) is None


def test_table_levels_generates_file(out_dirs):
    ra.table_levels()
    path = out_dirs / "tables" / "tab_levels.tex"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert r"\begin{tabular}" in content
    assert r"\end{tabular}" in content
    assert "H5" in content
    assert "H6" in content
    assert "H7" in content
    assert "H8" in content
    # Verify all four levels from course slide L04 are labeled
    assert "Network level" in content
    assert "Monadic level" in content
    assert "Dyadic level" in content
    assert "Mixed level" in content
    assert "$R^2$" in content
    assert re.search(r"\bnan\b", content, re.IGNORECASE) is None


def test_table_tests_includes_h1_to_h5(out_dirs):
    ra.table_tests()
    path = out_dirs / "tables" / "tab_tests.tex"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "H1" in content
    assert "H2" in content
    assert "H3" in content
    assert "H4" in content
    assert "H5" in content
    assert r">{\raggedright\arraybackslash}" in content
    assert re.search(r"\bnan\b", content, re.IGNORECASE) is None


def test_holm_values_are_shown_only_when_every_frame_carries_them():
    raw = pd.DataFrame({"p_value": [0.01, 0.04]})
    adjusted = pd.DataFrame({"p_value": [0.01, 0.04], "p_value_holm": [0.02, 0.04]})
    partial = pd.DataFrame({"p_value": [0.01, 0.04], "p_value_holm": [0.02, np.nan]})
    missing_raw = pd.DataFrame({"p_value": [np.nan, 0.04], "p_value_holm": [np.nan, 0.04]})
    assert ra.holm_ready(adjusted, missing_raw, None)
    assert not ra.holm_ready(raw)
    assert not ra.holm_ready(partial)
    assert not ra.holm_ready(adjusted, raw)
    row = {"p_value": 0.01, "p_value_holm": 0.02}
    assert ra.p_value(row, True) == 0.02
    assert ra.p_value(row, False) == 0.01
    assert ra.p_heading(False) == r"$p$"
    assert "Holm" in ra.p_heading(True)


def test_tables_call_values_adjusted_only_if_the_stored_results_are_adjusted(out_dirs):
    """Stored result files from before the Holm correction must not end up under an adjusted heading."""
    ra.table_tests()
    ra.table_levels()
    names = ("hypothesis_tests", "triads_h5", "levels_tests")
    frames = [pd.read_csv(ra.TABLES / f"{name}.csv") for name in names]
    for table, used in (("tab_tests.tex", frames[:2]), ("tab_levels.tex", frames[1:])):
        content = (out_dirs / "tables" / table).read_text(encoding="utf-8")
        assert ("Holm" in content) == ra.holm_ready(*used)


def test_figure_network_core_generates_pdf_and_png(out_dirs):
    ra.style()
    ra.figure_network_core()
    fig_pdf = out_dirs / "figures" / "fig_network_core_2007_2012.pdf"
    fig_png = out_dirs / "figures" / "fig_network_core_2007_2012.png"
    assert fig_pdf.exists() and fig_pdf.stat().st_size > 10000
    assert fig_png.exists() and fig_png.stat().st_size > 20000


def test_table_topology_generates_file(out_dirs):
    ra.table_topology()
    content = (out_dirs / "tables" / "tab_topology.tex").read_text(encoding="utf-8")
    assert r"\begin{tabular}" in content and r"\end{tabular}" in content
    for block in ("Degree distribution", "Compactness", "Homophily by ranking band"):
        assert block in content
    for net_short in ["2000-06", "2007-12", "Clay", "Grass", "WTA 07-25"]:
        assert net_short in content
    assert re.search(r"\bnan\b", content, re.IGNORECASE) is None


def test_table_abc_has_one_row_per_measure_and_three_columns(out_dirs):
    ra.table_abc()
    content = (out_dirs / "tables" / "tab_abc.tex").read_text(encoding="utf-8")
    assert "Phenomenon (A) & Measure (B) & Interpretation in tennis (C)" in content
    rows = [line for line in content.splitlines() if line.endswith(r"\\") and line.count(" & ") == 2]
    assert len(rows) == len(ra.ABC_ROWS) + 1  # header plus one row per phenomenon


def test_figure_core_homophily_generates_pdf_and_png(out_dirs):
    ra.style()
    ra.figure_core_homophily()
    assert (out_dirs / "figures" / "fig_core_homophily.pdf").stat().st_size > 5000
    assert (out_dirs / "figures" / "fig_core_homophily.png").stat().st_size > 10000


def test_table_abc_describes_hub_losses_to_authorities(out_dirs):
    ra.table_abc()
    content = (out_dirs / "tables" / "tab_abc.tex").read_text(encoding="utf-8")
    assert "while a hub beats authorities" not in content
    assert "hub loses" in content.lower()


def test_table_levels_uses_csv_sample_size_for_h8(out_dirs):
    ra.table_levels()
    content = (out_dirs / "tables" / "tab_levels.tex").read_text(encoding="utf-8")
    lt = pd.read_csv(ra.TABLES / "levels_tests.csv")
    h8_n = int(lt.loc[lt["hypothesis"] == "H8", "n"].iloc[0])
    assert "$n=328$" not in content
    assert f"$n={h8_n}$" in content


def test_figure_structure_rich_club_xlim_covers_all_networks(monkeypatch):
    captured = {}

    def capture_save(fig, name):
        captured["xlim"] = fig.axes[3].get_xlim()
        ra.plt.close(fig)

    monkeypatch.setattr(ra, "save", capture_save)
    ra.style()
    ra.figure_structure()
    rc = pd.read_csv(ra.TABLES / "rich_club_summary.csv").set_index("network").loc[ra.NETS]
    assert captured["xlim"][1] > float(rc["rho_rich_peak"].max())
