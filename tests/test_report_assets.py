import re

from tennis_networks import report_assets as ra
from tennis_networks.config import REPORT


def test_table_structure_generates_file():
    ra.table_structure()
    path = REPORT / "tables" / "tab_structure.tex"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert r"\begin{tabular}" in content
    assert r"\end{tabular}" in content
    assert "HITS centrality" in content
    assert "Borgatti-Everett discrete core-periphery model" in content
    assert "Structural equivalence" in content
    assert "Small-world topology" in content
    # Check that all 9 networks are present in the header
    for net_short in ["2000-06", "2007-12", "2013-18", "2019-25", "Clay", "Grass", "Hard", "ATP 07-25", "WTA 07-25"]:
        assert net_short in content
    # Ensure no NaN values leak into the LaTeX output
    assert re.search(r"\bnan\b", content, re.IGNORECASE) is None


def test_table_levels_generates_file():
    ra.table_levels()
    path = REPORT / "tables" / "tab_levels.tex"
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


def test_table_tests_includes_h1_to_h5():
    ra.table_tests()
    path = REPORT / "tables" / "tab_tests.tex"
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "H1" in content
    assert "H2" in content
    assert "H3" in content
    assert "H4" in content
    assert "H5" in content
    assert r">{\raggedright\arraybackslash}" in content
    assert re.search(r"\bnan\b", content, re.IGNORECASE) is None


def test_figure_network_core_generates_pdf_and_png():
    ra.style()
    ra.figure_network_core()
    fig_pdf = REPORT / "figures" / "fig_network_core_2007_2012.pdf"
    fig_png = REPORT / "figures" / "fig_network_core_2007_2012.png"
    assert fig_pdf.exists() and fig_pdf.stat().st_size > 10000
    assert fig_png.exists() and fig_png.stat().st_size > 20000
