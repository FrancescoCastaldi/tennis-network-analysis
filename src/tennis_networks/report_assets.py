"""LaTeX tables and figures of the report, built only from results/ and data/processed/.

Run (after analysis, hypotheses, reproduce, source_check and sensitivity):
    python -m tennis_networks.report_assets

Outputs:
    report/tables/*.tex      the tabular only: captions and labels live in report/main.tex
    report/figures/*.pdf     vector figures (plus .png for a quick look)
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

from tennis_networks.config import PROCESSED, REPORT, TABLES
from tennis_networks.loaders import load_network
from tennis_networks.loaders import load_undirected as undirected
from tennis_networks.sensitivity import same_verdict
from tennis_networks.structure import core_periphery
from tennis_networks.triads import triad_census_spectrum

OUT_TAB = REPORT / "tables"
OUT_FIG = REPORT / "figures"

ERAS = ["td_atp_2000_2006", "td_atp_2007_2012", "td_atp_2013_2018", "td_atp_2019_2025"]
SURFACES = ["td_atp_clay", "td_atp_grass", "td_atp_hard"]
TOURS = ["td_atp_2007_2025", "td_wta_2007_2025"]
NETS = ERAS + SURFACES + TOURS
SHORT = {
    "td_atp_2000_2006": "2000-06",
    "td_atp_2007_2012": "2007-12",
    "td_atp_2013_2018": "2013-18",
    "td_atp_2019_2025": "2019-25",
    "td_atp_clay": "Clay",
    "td_atp_grass": "Grass",
    "td_atp_hard": "Hard",
    "td_atp_2007_2025": "ATP 07-25",
    "td_wta_2007_2025": "WTA 07-25",
}
PLAIN = SHORT

# Reference categorical palette (slots 1-4), with distinct markers for black-and-white printing.
COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
MARKERS = ["o", "s", "^", "D"]
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def num(x, digits=3):
    if pd.isna(x):
        return "n/a"
    if float(x).is_integer() and digits == 0:
        return f"{int(x):,}"
    text = f"{x:,.{digits}f}"
    return "$-$" + text[1:] if text.startswith("-") else text


def holm_ready(*frames):
    """True when every frame has a Holm column filled wherever the raw p-value exists.

    A table mixes rows from several result files, so adjusted values are shown only when all
    of them carry the correction; otherwise the whole table shows the raw values under a raw
    heading, never raw values under an adjusted one.
    """
    return all(
        "p_value_holm" in frame.columns and frame.loc[frame["p_value"].notna(), "p_value_holm"].notna().all()
        for frame in frames
        if frame is not None
    )


def p_value(row, adjusted):
    """Holm-adjusted p-value of a result row when `adjusted`, the raw one otherwise."""
    return row["p_value_holm"] if adjusted else row["p_value"]


def p_heading(adjusted):
    return r"$p_{\mathrm{Holm}}$" if adjusted else r"$p$"


def write(name, body):
    OUT_TAB.mkdir(parents=True, exist_ok=True)
    (OUT_TAB / name).write_text(body.strip() + "\n", encoding="utf-8")


# Tables


def table_networks():
    summary = pd.read_csv(TABLES / "td_networks_summary.csv").set_index("network")
    mich = []
    for i, (label, kind) in enumerate(
        [
            ("Wins", "directed, weighted by wins"),
            ("Points", "both directions, weighted by ATP points"),
            ("Matches", "undirected, unweighted"),
            ("Extended", "undirected, unweighted, lower tiers"),
        ],
        start=1,
    ):
        f = {1: "michieli_1_wins", 2: "michieli_2_points", 3: "michieli_3_undirected", 4: "michieli_4_extended"}[i]
        e = pd.read_csv(PROCESSED / f"{f}.csv")
        nodes = len(set(e["source"]) | set(e["target"]))
        matches = num(e["weight"].sum(), 0) if i == 1 else "n/a"
        period = "1968-2018" if i == 4 else "1968-2017"
        mich.append(f"M{i} {label} & {period} & {kind} & {nodes:,} & {len(e):,} & {matches} \\\\")
    td_rows = []
    for n in NETS:
        r = summary.loc[n]
        a, b = (int(x) for x in n.split("_")[-2:]) if n not in SURFACES else (2000, 2025)
        period = f"{a}-{b}"
        label = f"{n.split('_')[1].upper()} " + (SHORT[n] if n in SURFACES else period)
        td_rows.append(
            f"{label} & {period} & directed, weighted by wins & {int(r['players']):,} & "
            f"{int(r['edges']):,} & {int(r['matches']):,} \\\\"
        )
    body = "\n".join(
        [
            r"\begin{tabular}{@{}llp{4.2cm}rrr@{}}",
            r"\toprule",
            r"Network & Period & Type & Nodes & Edges & Matches \\",
            r"\midrule",
            r"\multicolumn{6}{@{}l}{\emph{Michieli (2018), aggregated, no dates}} \\",
            *mich,
            r"\midrule",
            r"\multicolumn{6}{@{}l}{\emph{tennis-data.co.uk, main draw, walkovers excluded}} \\",
            *td_rows,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    write("tab_networks.tex", body)


def table_reproduction():
    d = pd.read_csv(TABLES / "michieli_reproduction.csv")
    rows = []
    for r in d.itertuples(index=False):
        integers = float(r.paper).is_integer() and float(r.ours).is_integer()
        digits = 0 if integers else (4 if abs(r.paper) < 0.05 else 2)
        rows.append(f"{r.network} & {r.measure} & {num(r.paper, digits)} & {num(r.ours, digits)} \\\\")
    write(
        "tab_reproduction.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}llrr@{}}",
                r"\toprule",
                r"Network & Measure & Paper & This study \\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def table_global():
    g = pd.read_csv(TABLES / "global_measures.csv").set_index("network").loc[NETS]
    und = {n: undirected(n) for n in NETS}
    kcore = {n: max(nx.core_number(h).values()) for n, h in und.items()}
    spec = [
        ("Players $n$", g["nodes"], 0),
        ("Edges $m$", g["edges"], 0),
        ("Density", g["density"], 4),
        ("Mean out-degree", g["mean_degree"], 1),
        ("Reciprocity", g["reciprocity"], 3),
        ("Largest SCC (share)", g["giant_fraction"], 3),
        ("Avg.\\ distance (SCC)", g["avg_path_giant"], 2),
        ("Diameter (SCC)", g["diameter_giant"], 0),
        ("Max $k$-core", pd.Series(kcore), 0),
        ("Louvain communities", g["communities"], 0),
        ("Modularity $Q$", g["modularity"], 3),
        ("Top-10 PageRank share", g["top10_pagerank_share"], 3),
        ("Gini of in-strength", g["gini_in_strength"], 3),
        ("Spearman PageRank, rank", g["spearman_pagerank_atp_rank"], 3),
    ]
    head = " & ".join(SHORT[n] for n in NETS)
    rows = [f"{label} & " + " & ".join(num(v[n], d) for n in NETS) + r" \\" for label, v, d in spec]
    write(
        "tab_global.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}l" + "r" * len(NETS) + "@{}}",
                r"\toprule",
                r" & \multicolumn{4}{c}{ATP eras} & \multicolumn{3}{c}{ATP surfaces} & \multicolumn{2}{c}{Tours} \\",
                r"\cmidrule(lr){2-5}\cmidrule(lr){6-8}\cmidrule(l){9-10}",
                f"Measure & {head} \\\\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def table_null():
    d = pd.read_csv(TABLES / "null_undirected.csv")
    tested = set(d["network"])
    stats = [
        ("degree_assortativity", "$r$ (assortativity)"),
        ("avg_clustering", "$C$ (clustering)"),
        ("transitivity", "$T$ (transitivity)"),
    ]
    rows = []
    for n in [n for n in NETS if n in tested]:
        cells = []
        for s, _ in stats:
            r = d[(d["network"] == n) & (d["statistic"] == s)].iloc[0]
            cells += [num(r["observed"], 3), num(r["null_mean"], 3), num(r["z"], 1)]
        rows.append(f"{PLAIN[n]} & " + " & ".join(cells) + r" \\")
    samples = int(d["samples"].iloc[0])
    head = " & ".join(rf"\multicolumn{{3}}{{c}}{{{lab}}}" for _, lab in stats)
    write(
        "tab_null.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}l" + "rrr" * 3 + "@{}}",
                r"\toprule",
                f" & {head} \\\\",
                r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(l){8-10}",
                "Network & " + " & ".join(["obs.", "null", "$z$"] * 3) + r" \\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )
    return samples


def table_tests():
    d = pd.read_csv(TABLES / "hypothesis_tests.csv")
    h5 = pd.read_csv(TABLES / "triads_h5.csv") if (TABLES / "triads_h5.csv").exists() else None
    adjusted = holm_ready(d, h5)
    stat = {"top10_pagerank_share": "top-10 PageRank share", "degree_centralization": "degree centralization"}
    rows = []
    for h in ("H1", "H2", "H3", "H4"):
        if h == "H2":
            h2 = d[d["hypothesis"] == "H2"]
            rows.append(
                f"H2 & degree assortativity & 8 nets vs null & "
                f"{num(h2['value_a'].min(), 3)} to {num(h2['value_a'].max(), 3)} & "
                f"{num(h2['value_b'].min(), 3)} to {num(h2['value_b'].max(), 3)} & "
                f"$>0$ in all & 0 & $\\le${num(h2['p_value_holm' if adjusted else 'p_value'].max(), 3)} \\\\"
            )
            continue
        for r in d[d["hypothesis"] == h].itertuples(index=False):
            comp = {"H1": "2007-18 vs 2019-25 (seasons)", "H4": "WTA vs ATP (paired seasons)"}.get(
                h, r.comparison.replace("ATP ", "")
            )
            expected = num(r.perm_mean_diff, 3) if not pd.isna(r.perm_mean_diff) else "0"
            rows.append(
                f"{h} & {stat[r.statistic]} & {comp} & {num(r.value_a, 3)} & {num(r.value_b, 3)} & "
                f"{num(r.diff, 3)} & {expected} & {num(p_value(r._asdict(), adjusted), 3)} \\\\"
            )
    if h5 is not None:
        for r in h5.itertuples(index=False):
            label = "H5" if r.hypothesis == "H5" else "H5 (tours)"
            comp = "2007-12 vs other eras" if r.hypothesis == "H5" else "WTA vs ATP (paired seasons)"
            rows.append(
                f"{label} & cyclic triad ratio & {comp} & {num(r.value_a, 3)} & {num(r.value_b, 3)} & "
                f"{num(r.diff, 3)} & 0 & {num(p_value(r._asdict(), adjusted), 3)} \\\\"
            )
    write(
        "tab_tests.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}ll>{\raggedright\arraybackslash}p{3.0cm}rrrrr@{}}",
                r"\toprule",
                (
                    rf"H & Statistic & Comparison & Group A & Group B & Diff & $E_0[\mathrm{{Diff}}]$ & "
                    rf"{p_heading(adjusted)} \\"
                ),
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def table_hypothesis_summary():
    """Summarise H1-H8 with Holm-adjusted primary-test p-values."""
    raw = []
    hypotheses = pd.read_csv(TABLES / "hypothesis_tests.csv")
    for r in hypotheses.itertuples(index=False):
        raw.append((r.hypothesis, float(r.p_value)))
    triads = pd.read_csv(TABLES / "triads_h5.csv")
    for r in triads.itertuples(index=False):
        raw.append(("H5", float(r.p_value)))
    levels = pd.read_csv(TABLES / "levels_tests.csv")
    for r in levels.itertuples(index=False):
        if r.hypothesis == "H6" and r.statistic != "beta log PageRank":
            continue
        raw.append((r.hypothesis, float(r.p_value)))

    ordered = sorted(enumerate(raw), key=lambda item: item[1][1])
    adjusted = [0.0] * len(raw)
    running = 0.0
    for rank, (index, (_, p_value)) in enumerate(ordered, start=1):
        running = max(running, min(1.0, p_value * (len(raw) - rank + 1)))
        adjusted[index] = running

    labels = {
        "H1": "top-10 prestige and centralization, eras",
        "H2": "degree assortativity vs configuration null",
        "H3": "grass vs clay/hard concentration",
        "H4": "WTA vs ATP concentration",
        "H5": "cyclic triads, Big Three era",
        "H6": "PageRank predicts official ranking",
        "H7": "cross-surface dominance carry-over",
        "H8": "surface-profile scheduling homophily",
    }
    rows = []
    for hypothesis in labels:
        values = [p for h, p in raw if h == hypothesis]
        corrected = [adjusted[i] for i, (h, _) in enumerate(raw) if h == hypothesis]
        supported = max(corrected) <= 0.05
        raw_text = num(min(values), 3) if min(values) == max(values) else f"{num(min(values), 3)}-{num(max(values), 3)}"
        holm_text = (
            num(min(corrected), 3)
            if min(corrected) == max(corrected)
            else f"{num(min(corrected), 3)}-{num(max(corrected), 3)}"
        )
        verdict = "supported" if supported else "not supported after Holm correction"
        rows.append(f"{hypothesis} & {labels[hypothesis]} & {raw_text} & {holm_text} & {verdict} \\\\")
    write(
        "tab_hypotheses.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}llp{1.6cm}p{1.6cm}l@{}}",
                r"\toprule",
                r"H & Primary test & Raw $p$ & Holm $p$ & Conclusion \\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def table_structure():
    s = pd.read_csv(TABLES / "structure_summary.csv").set_index("network").loc[NETS]
    head = " & ".join(SHORT[n] for n in NETS)

    def section(title, items):
        out = [rf"\multicolumn{{{len(NETS) + 1}}}{{@{{}}l}}{{\emph{{{title}}}}} \\"]
        for label, col, d in items:
            out.append(f"{label} & " + " & ".join(num(s.loc[n, col], d) for n in NETS) + r" \\")
        return out

    rows = []
    rows += section(
        "HITS centrality (Spearman rank correlation)",
        [
            (r"Authority vs PageRank ($\rho$)", "authority_pagerank_spearman", 3),
            (r"Authority vs official rank ($\rho$)", "authority_rank_spearman", 3),
            (r"Hub vs official rank ($\rho$)", "hub_rank_spearman", 3),
        ],
    )
    rows.append(r"\midrule")
    rows += section(
        "Borgatti-Everett discrete core-periphery model",
        [
            (r"Core size $k$", "core_size", 0),
            (r"Core share", "core_share", 3),
            (r"Fit correlation $\phi$", "core_fit", 3),
            (r"Continuous model fit $\rho$", "continuous_core_fit", 3),
            (r"Core density $d_{cc}$", "density_core", 3),
            (r"Core-periphery density $d_{cp}$", "density_core_periphery", 3),
            (r"Periphery density $d_{pp}$", "density_periphery", 4),
            (r"Core vs $k$-core Jaccard", "core_kcore_jaccard", 3),
            (r"Core median rank", "core_median_rank", 1),
            (r"Core top-100 share", "core_share_top100", 3),
        ],
    )
    rows.append(r"\midrule")
    rows += section(
        "Structural equivalence (cosine similarity on opponents)",
        [
            (r"Regular players ($\ge 30$ opponents)", "equivalence_players", 0),
            (r"Mean cosine similarity", "equivalence_mean_similarity", 3),
            (r"Rank-gap correlation $r$", "equivalence_rankgap_r", 3),
            (r"Rank-gap QAP $p$", "equivalence_rankgap_p", 3),
        ],
    )
    rows.append(r"\midrule")
    rows += section(
        "Small-world topology (Maslov-Sneppen null model)",
        [
            (r"Small-world index $\sigma$", "sw_sigma", 2),
        ],
    )

    rc_file = TABLES / "rich_club_summary.csv"
    if rc_file.exists():
        rc = pd.read_csv(rc_file).set_index("network")
        for col in rc.columns:
            s[col] = rc[col]
        rows.append(r"\midrule")
        rows += section(
            r"Rich-club elite closure (configuration null model)",
            [
                (r"Peak threshold degree $k^*$", "peak_k", 0),
                (r"Elite club size $N_{>k^*}$", "elite_nodes", 0),
                (r"Peak $z$-score", "z_peak", 1),
                (r"95\% of null maxima of $z$ (max test)", "z_max_null_95", 1),
            ],
        )

    write(
        "tab_structure.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}l" + "r" * len(NETS) + "@{}}",
                r"\toprule",
                r" & \multicolumn{4}{c}{ATP eras} & \multicolumn{3}{c}{ATP surfaces} & \multicolumn{2}{c}{Tours} \\",
                r"\cmidrule(lr){2-5}\cmidrule(lr){6-8}\cmidrule(l){9-10}",
                f"Property & {head} \\\\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def table_levels():
    rows = []
    h5 = pd.read_csv(TABLES / "triads_h5.csv") if (TABLES / "triads_h5.csv").exists() else None
    lt = pd.read_csv(TABLES / "levels_tests.csv") if (TABLES / "levels_tests.csv").exists() else None
    adjusted = holm_ready(h5, lt)
    if h5 is not None:
        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Network level: "
            r"Triad hierarchy (cyclic ratio $030C/030T$, random baseline $= 1/3$)}} \\"
        )
        for r in h5.itertuples(index=False):
            label = "H5" if r.hypothesis == "H5" else "H5 (tours)"
            comp = "ATP 2007-12 vs other eras" if r.hypothesis == "H5" else "WTA vs ATP (paired seasons)"
            note = f"{num(r.value_a, 3)} vs {num(r.value_b, 3)}"
            diff_str, p_str = num(r.diff, 3), num(p_value(r._asdict(), adjusted), 3)
            rows.append(f"{label} & Network & {comp} & cyclic triad ratio & {diff_str} & {p_str} & {note} \\\\")
        rows.append(r"\midrule")

    if lt is not None:
        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Monadic level: "
            r"Permutation regression of $\log(\text{ranking})$ on PageRank and wins}} \\"
        )
        mon = lt[lt["level"] == "monadic"]
        eras_labels = {
            "td_atp_2000_2006": "ATP 2000-06",
            "td_atp_2007_2012": "ATP 2007-12",
            "td_atp_2013_2018": "ATP 2013-18",
            "td_atp_2019_2025": "ATP 2019-25",
        }
        for era_id, era_name in eras_labels.items():
            sub = mon[mon["comparison"].str.contains(era_id)]
            if sub.empty:
                continue
            pr_row = sub[sub["statistic"] == "beta log PageRank"].iloc[0]
            w_row = sub[sub["statistic"] == "beta log wins"].iloc[0]
            n_val = pr_row["n"]
            r2_val = pr_row["note"].replace("R2", "$R^2$")
            pr_val, pr_p = num(pr_row["value"], 3), num(p_value(pr_row, adjusted), 3)
            rows.append(
                f"H6 & Monadic & {era_name} ($n={n_val}$) & $\\beta$ log PageRank & {pr_val} & {pr_p} & {r2_val} \\\\"
            )
            w_val, w_p = num(w_row["value"], 3), num(p_value(w_row, adjusted), 3)
            rows.append(f"   &         &                      & $\\beta$ log wins     & {w_val} & {w_p} & \\\\")
        rows.append(r"\midrule")

        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Dyadic level: "
            r"Head-to-head dominance across surfaces (QAP permutation test)}} \\"
        )
        dya = lt[lt["level"] == "dyadic"]
        for r in dya.itertuples(index=False):
            comp = "Clay vs Hard balance" if "Clay" in r.comparison else "Grass vs Hard balance"
            p_val = num(p_value(r._asdict(), adjusted), 3)
            rows.append(
                f"H7 & Dyadic & {comp} & QAP correlation $r$ & {num(r.value, 3)} & {p_val} & $n={r.n}$; null $r=0$ \\\\"
            )
        rows.append(r"\midrule")

        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Mixed level: "
            r"Surface profile and match encounters (QAP permutation test)}} \\"
        )
        mix = lt[lt["level"] == "mixed"]
        for r in mix.itertuples(index=False):
            comp = "Same surface profile" if "profile" in r.comparison else "Specialisation gap"
            metric = "matches vs shared profile" if "profile" in r.comparison else "matches vs profile distance"
            note = "$n=328$; 3 classes" if "profile" in r.comparison else "$n=328$; Euclidean"
            p_val = num(p_value(r._asdict(), adjusted), 3)
            rows.append(f"H8 & Mixed & {comp} & {metric} & {num(r.value, 3)} & {p_val} & {note} \\\\")

    body = "\n".join(
        [
            r"\begin{tabular}{@{}ll>{\raggedright\arraybackslash}p{2.6cm}>{\raggedright\arraybackslash}p{3.2cm}rrr@{}}",
            r"\toprule",
            rf"H & Level & Comparison & Metric & Effect & {p_heading(adjusted)} & Details \\",
            r"\midrule",
            *rows,
            r"\bottomrule",
            r"\end{tabular}",
        ]
    )
    write("tab_levels.tex", body)


def table_top10():
    cols = ERAS + ["td_wta_2007_2025"]
    lists = {}
    for n in cols:
        nodes = pd.read_csv(TABLES / f"{n}_nodes.csv").set_index("node")
        ranks = pd.read_csv(PROCESSED / f"{n}_ranks.csv", index_col="player")["rank"]
        top = nodes["pagerank"].sort_values(ascending=False).head(10).index
        lists[n] = [f"{p} ({int(ranks[p]) if p in ranks.index else 'n/a'})" for p in top]
    head = " & ".join(SHORT[n] if n in TOURS else "ATP " + SHORT[n] for n in cols)
    rows = [f"{i + 1} & " + " & ".join(lists[n][i] for n in cols) + r" \\" for i in range(10)]
    write(
        "tab_top10.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}r" + "l" * len(cols) + "@{}}",
                r"\toprule",
                f" & {head} \\\\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def table_topology():
    """Power-law fit, compactness and ranking-band homophily of the nine comparative networks."""
    fits = pd.read_csv(TABLES / "powerlaw_fits.csv").set_index("network").loc[NETS]
    comp = pd.read_csv(TABLES / "compactness.csv").set_index("network").loc[NETS]
    hom = pd.read_csv(TABLES / "homophily_bands.csv").set_index("network").loc[NETS]
    mix = pd.read_csv(TABLES / "homophily_mixing.csv")
    top = mix[(mix.band_a == "top10") & (mix.band_b == "top10")].set_index("network").loc[NETS]

    def line(label, series, d):
        return f"{label} & " + " & ".join(num(series.loc[n], d) for n in NETS) + r" \\"

    def section(title):
        return rf"\multicolumn{{{len(NETS) + 1}}}{{@{{}}l}}{{\emph{{{title}}}}} \\"

    verdict = fits["verdict"].map(lambda v: "yes" if v == "plausible" else "no")
    rows = [
        section("Degree distribution (distinct opponents, power-law fit)"),
        line(r"Exponent $\hat{\alpha}$", fits["alpha"], 2),
        line(r"Lower bound $\hat{k}_{\min}$", fits["xmin"], 0),
        line(r"Players in the tail (share)", fits["tail_share"], 2),
        line(r"Power law vs lognormal ($R$)", fits["R_vs_lognormal"], 1),
        line(r"Power law vs truncated power law ($R$)", fits["R_vs_truncated_power_law"], 1),
        "Power law plausible? & " + " & ".join(verdict.loc[n] for n in NETS) + r" \\",
        r"\midrule",
        section("Compactness (undirected, largest component)"),
        line(r"Average distance $L$", comp["avg_distance"], 2),
        line(r"Diameter", comp["diameter"], 0),
        line(r"Global efficiency", comp["global_efficiency"], 3),
        line(r"$L$ over random-graph reference", comp["distance_ratio"], 2),
        r"\midrule",
        section("Homophily by ranking band (top 10, 11-100, others)"),
        line(r"Same-band share of matches", hom["same_band_share"], 3),
        line(r"Top 10 meet top 10: observed / expected", top["ratio_all"], 1),
        line(r"Same, controlling for number of opponents", top["ratio_deg"], 2),
        line(r"Same-band share, $z$ controlling for activity", hom["same_band_z_deg"], 2),
    ]
    head = " & ".join(SHORT[n] for n in NETS)
    write(
        "tab_topology.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}l" + "r" * len(NETS) + "@{}}",
                r"\toprule",
                r" & \multicolumn{4}{c}{ATP eras} & \multicolumn{3}{c}{ATP surfaces} & \multicolumn{2}{c}{Tours} \\",
                r"\cmidrule(lr){2-5}\cmidrule(lr){6-8}\cmidrule(l){9-10}",
                f"Property & {head} \\\\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


# Phenomenon (A), measure (B), interpretation in tennis (C): the rule of the course, one row per measure.
ABC_ROWS = [
    (
        "Who wins, and who holds prestige",
        "In- and out-degree, PageRank, HITS authority and hub scores",
        "In-degree counts distinct opponents defeated; out-degree counts distinct opponents lost to. "
        "PageRank weights wins by opponent prestige; "
        "an authority beats players who also score highly, while a hub beats authorities.",
    ),
    (
        "How concentrated prestige and wins are",
        "Share of PageRank held by the top 10, Gini coefficient of in-strength",
        "A high top-10 share concentrates prestige. A high Gini means wins are unevenly distributed.",
    ),
    (
        "Core players and the wider field",
        "$k$-core decomposition, Borgatti-Everett core-periphery model",
        "A $k$-core keeps players with at least $k$ ties inside the set. The fitted model compares "
        "within-core and between-group densities; neither requires every core pair to have played.",
    ),
    (
        "How connected the tour is",
        "Components, average distance, diameter, global efficiency, ratio to a random reference",
        "Components count separate groups; distances count steps between players. Short paths and "
        "high efficiency indicate a more connected field.",
    ),
    (
        "Dependence on top players",
        "Largest component after removing players at random and in decreasing PageRank order",
        "A faster loss of connectivity after removing high-PageRank players shows greater reliance on leading players.",
    ),
    (
        "Closed rivalries and win hierarchy",
        "Clustering, transitivity, triad census",
        "Clustering measures closed opponent ties locally; transitivity measures closed triples "
        "overall. Triads distinguish transitive results from cycles of wins.",
    ),
    (
        "Whether opponent counts have a heavy tail",
        "Power-law fit of the degree distribution and likelihood-ratio tests against lognormal, "
        "exponential and truncated power law",
        "A power-law tail would mean a few players face many more opponents. Tournament draws and "
        "season length set a practical upper bound, so alternatives are compared as well.",
    ),
    (
        "Do highly ranked or active players meet each other",
        "Degree and ranking-band assortativity, band mixing against permutation nulls",
        "Positive assortativity means similar-degree players meet. Band-mixing ratios compare "
        "observed matches with shuffled ranks, including a shuffle that controls opponent counts.",
    ),
    (
        "Whether players occupy similar positions",
        "Cosine similarity of opponent vectors, QAP correlation with the ranking gap",
        "Cosine similarity compares opponent profiles. QAP tests whether profile similarity "
        "tracks the gap in official ranking.",
    ),
    (
        "Structure beyond opponent counts",
        "Configuration model, $z$-scores and permutation $p$-values, small-world index $\\sigma$",
        "Degree-preserving nulls keep each player's opponent count. Differences from them show "
        "patterns not explained by those counts alone.",
    ),
    (
        "Groups and career cohorts",
        "Louvain communities and modularity",
        "Modularity measures how strongly matches fall within detected groups. Here, groups can "
        "reflect players whose careers overlapped in time.",
    ),
]


def table_abc():
    col = r">{\raggedright\arraybackslash}p{%s\linewidth}"
    rows = []
    for a, b, c in ABC_ROWS:
        rows += [rf"{a} & {b} & {c} \\", r"\addlinespace[3pt]"]
    write(
        "tab_abc.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}" + col % "0.22" + col % "0.28" + col % "0.43" + "@{}}",
                r"\toprule",
                r"Phenomenon (A) & Measure (B) & Interpretation in tennis (C) \\",
                r"\midrule",
                *rows[:-1],
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


# Figures


def table_sensitivity():
    """H1, H3 and H4 under each cleaning variant: difference and two-sided p-value, and whether the verdict holds."""
    d = pd.read_csv(TABLES / "sensitivity_tests.csv")
    variants = pd.read_csv(TABLES / "sensitivity_variants.csv")["variant"].tolist()
    stat = {"top10_pagerank_share": "top-10 share", "degree_centralization": "centralization"}
    comp = {
        "ATP 2007-2018 vs 2019-2025 (season means)": "2007-18 vs 2019-25",
        "WTA vs ATP, paired season differences 2007-2025": "WTA vs ATP",
    }
    rows = []
    for key, g in d.groupby(["hypothesis", "statistic", "comparison"], sort=False):
        h, s, c = key
        cells = " & ".join(
            f"{num(g[g['variant'] == v]['diff'].iloc[0], 3)} ({num(g[g['variant'] == v]['p_value'].iloc[0], 3)})"
            for v in variants
        )
        verdict = "yes" if same_verdict(g["p_value"]) else "no"
        rows.append(f"{h} & {stat[s]}, {comp.get(c, c.replace('ATP ', ''))} & {cells} & {verdict} \\\\")
    write(
        "tab_sensitivity.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}ll" + "r" * len(variants) + r"c@{}}",
                r"\toprule",
                r"H & Test & Baseline & No retire. & Walkovers & Carpet=hard & Same verdict \\",
                r"\midrule",
                *rows,
                r"\bottomrule",
                r"\end{tabular}",
            ]
        ),
    )


def style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9.5,
            "axes.labelsize": 10,
            "axes.titlesize": 10.5,
            "legend.fontsize": 8.5,
            "xtick.labelsize": 8.5,
            "ytick.labelsize": 8.5,
            "axes.edgecolor": MUTED,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.color": GRID,
            "grid.linewidth": 0.6,
            "lines.linewidth": 1.6,
            "lines.markersize": 4.5,
            "legend.frameon": False,
            "savefig.bbox": "tight",
        }
    )


def save(fig, name):
    OUT_FIG.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_FIG / f"{name}.pdf")
    fig.savefig(OUT_FIG / f"{name}.png", dpi=200)
    plt.close(fig)


GROUPS = [("(a) ATP eras", ERAS), ("(b) ATP surfaces, 2000-2025", SURFACES), ("(c) ATP vs WTA, 2007-2025", TOURS)]


def figure_yearly():
    y = pd.read_csv(TABLES / "yearly_statistics.csv").set_index("season")
    tri = pd.read_csv(TABLES / "triads_by_season.csv").set_index("season")
    fig, axes = plt.subplots(1, 3, figsize=(5.9, 2.5), layout="constrained")
    stats = ("top10_pagerank_share", "degree_centralization")
    labels = ("(a) top-10 PageRank share", "(b) degree centralization")
    for ax, stat, label in zip(axes[:2], stats, labels, strict=True):
        ax.axvspan(2006.5, 2018.5, color=GRID, alpha=0.6, linewidth=0)
        for i, tour in enumerate(("ATP", "WTA")):
            s_ = y[f"{tour}_{stat}"].dropna()
            ax.plot(s_.index, s_.values, color=COLORS[i], marker=MARKERS[i], markersize=3.5, linewidth=1.4, label=tour)
        ax.set_title(label, loc="left", fontsize=8.5)
        ax.set_xlabel("season")
        ax.legend(loc="upper right", fontsize=7)
    ax = axes[2]
    ax.axvspan(2006.5, 2018.5, color=GRID, alpha=0.6, linewidth=0)
    for i, tour in enumerate(("ATP", "WTA")):
        s_ = tri[f"{tour}_cyclic_ratio"].dropna()
        ax.plot(s_.index, s_.values, color=COLORS[i], marker=MARKERS[i], markersize=3.5, linewidth=1.4, label=tour)
    ax.set_title("(c) cyclic / transitive triads", loc="left", fontsize=8.5)
    ax.set_xlabel("season")
    ax.legend(loc="lower left", fontsize=7)
    save(fig, "fig_yearly")


def _draw_sources(ax_wins, ax_pairs):
    """Panels (a) and (b) of the source validation: whole-career wins and loser-winner pairs."""
    players = pd.read_csv(TABLES / "td_michieli_players.csv")
    pairs = pd.read_csv(TABLES / "td_michieli_pairs.csv")

    x, y = players["wins_michieli"], players["wins_tennis_data"]
    top = max(x.max(), y.max()) * 1.05
    ax_wins.plot([0, top], [0, top], color=MUTED, linewidth=0.9, linestyle="--", zorder=1)
    ax_wins.scatter(x, y, s=12, color=COLORS[0], alpha=0.6, edgecolors="none", zorder=2)
    r = np.corrcoef(x, y)[0, 1]
    ax_wins.text(0.04, 0.96, f"$n$ = {len(players)}, $r$ = {r:.2f}", transform=ax_wins.transAxes, va="top", color=MUTED)
    ax_wins.set_xlim(0, top)
    ax_wins.set_ylim(0, top)
    ax_wins.set_xlabel("wins in Michieli network 1")
    ax_wins.set_ylabel("wins in tennis-data.co.uk")
    ax_wins.set_title("(a) players who debut after 2002", loc="left", fontsize=10)

    shares = pairs.set_index("outcome")["share"]
    colors = {
        "identical": COLORS[2],
        "Michieli higher": COLORS[0],
        "tennis-data higher": COLORS[3],
        "absent in Michieli": COLORS[1],
    }
    left = 0.0
    for outcome, share in shares.items():
        ax_pairs.barh(0, share, left=left, color=colors[outcome], edgecolor="white", linewidth=0.6, height=0.5)
        left += share
    ax_pairs.set_xlim(0, 1)
    ax_pairs.set_ylim(-0.9, 0.5)
    ax_pairs.set_yticks([])
    ax_pairs.set_xlabel("share of loser-winner pairs")
    ax_pairs.grid(False)
    ax_pairs.spines["left"].set_visible(False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[o]) for o in shares.index]
    labels = [f"{o} ({100 * s:.1f}%)" for o, s in shares.items()]
    ax_pairs.legend(handles, labels, loc="lower left", ncol=2, fontsize=7.5, columnspacing=0.8, handlelength=1)
    ax_pairs.set_title("(b) pairs between those players", loc="left", fontsize=10)


def figure_network_core():
    fig, (ax_net, ax_triad) = plt.subplots(1, 2, figsize=(6.5, 3.5), gridspec_kw={"width_ratios": [1.18, 1.0]})

    # (a) Network core (Top 12 players of 2007-2012)
    spec_2007 = {"id": "td_atp_2007_2012", "file": "td_atp_2007_2012.csv", "directed": True}
    g = load_network(spec_2007)
    nodes_df = pd.read_csv(TABLES / "td_atp_2007_2012_nodes.csv").set_index("node")
    top_players = list(nodes_df["pagerank"].sort_values(ascending=False).head(12).index)
    sub = g.subgraph(top_players).copy()

    big4 = {"Nadal R.", "Djokovic N.", "Federer R.", "Murray A."}
    node_colors = ["#1f77b4" if p in big4 else "#e66101" for p in top_players]
    node_sizes = [240 + 3200 * nodes_df.loc[p, "pagerank"] for p in top_players]

    pos = nx.circular_layout(top_players)

    # Draw directed edges with encounter weights
    for u, v, d in sub.edges(data=True):
        w = d.get("weight", 1)
        ax_net.annotate(
            "",
            xy=pos[v],
            xytext=pos[u],
            arrowprops=dict(
                arrowstyle="->",
                color="#666666",
                lw=0.5 + 0.16 * min(w, 10),
                alpha=0.6,
                shrinkA=10,
                shrinkB=10,
                connectionstyle="arc3,rad=0.08",
            ),
        )

    ax_net.scatter(
        [pos[p][0] for p in top_players],
        [pos[p][1] for p in top_players],
        s=node_sizes,
        c=node_colors,
        zorder=5,
        edgecolors="#0b0b0b",
        linewidths=0.9,
    )

    short_names = {
        "Nadal R.": "Nadal",
        "Djokovic N.": "Djokovic",
        "Federer R.": "Federer",
        "Murray A.": "Murray",
        "Ferrer D.": "Ferrer",
        "Davydenko N.": "Davydenko",
        "Roddick A.": "Roddick",
        "Tsonga J.W.": "Tsonga",
        "Berdych T.": "Berdych",
        "Del Potro J.M.": "Del Potro",
        "Verdasco F.": "Verdasco",
        "Soderling R.": "Soderling",
    }
    for p in top_players:
        x, y = pos[p]
        ha = "center"
        if x > 0.3:
            ha = "left"
        elif x < -0.3:
            ha = "right"
        va = "center"
        if y > 0.5:
            va = "bottom"
        elif y < -0.5:
            va = "top"
        ax_net.text(
            1.23 * x,
            1.23 * y,
            short_names.get(p, p),
            fontsize=7.5,
            ha=ha,
            va=va,
            weight="bold" if p in big4 else "normal",
            color="#0b0b0b",
        )

    # Legend for Big Four vs Contenders
    ax_net.scatter([], [], c="#1f77b4", s=60, edgecolors="#0b0b0b", lw=0.7, label="Big Four")
    ax_net.scatter([], [], c="#e66101", s=60, edgecolors="#0b0b0b", lw=0.7, label="Contenders")
    ax_net.legend(loc="lower left", fontsize=7.5, frameon=False, bbox_to_anchor=(-0.05, -0.05))

    ax_net.set_xlim(-1.65, 1.65)
    ax_net.set_ylim(-1.65, 1.65)
    ax_net.axis("off")
    ax_net.set_title("(a) 2007-2012 elite core tournament (N = 12)", loc="left", fontsize=9.5)

    # (b) Triad census spectrum
    spec_file = TABLES / "triads_spectrum_2007_2012.csv"
    if spec_file.exists():
        df_spec = pd.read_csv(spec_file)
    else:
        df_spec = triad_census_spectrum(g, samples=15, seed=20261115)
        spec_file.parent.mkdir(parents=True, exist_ok=True)
        df_spec.to_csv(spec_file, index=False, encoding="utf-8")

    triad_types = list(df_spec["triad"])
    zs = df_spec["z"].fillna(0.0).to_numpy()
    y_pos = np.arange(len(triad_types))
    colors = ["#1f77b4" if z >= 0 else "#e66101" for z in zs]

    ax_triad.barh(y_pos, zs, color=colors, height=0.68, edgecolor="none", zorder=3)
    ax_triad.axvline(0, color="#0b0b0b", linewidth=0.8, zorder=4)
    ax_triad.axvline(1.96, color="#52514e", linestyle="--", linewidth=0.6, zorder=2)
    ax_triad.axvline(-1.96, color="#52514e", linestyle="--", linewidth=0.6, zorder=2)
    ax_triad.set_yticks(y_pos)
    ax_triad.set_yticklabels(triad_types, fontsize=7.5)
    ax_triad.set_xlabel("z-score vs configuration null", fontsize=8.5)
    ax_triad.set_title("(b) 16-class triad z-score spectrum", loc="left", fontsize=9.5)
    ax_triad.tick_params(axis="both", which="major", labelsize=7.5)
    ax_triad.grid(True, linestyle=":", alpha=0.6, color="#e4e3df", zorder=0)

    fig.tight_layout()
    save(fig, "fig_network_core_2007_2012")


def figure_core_homophily():
    """2007-2012: block density of the adjacency by degree with the core, and ranking-band mixing ratios."""
    name = "td_atp_2007_2012"
    und = undirected(name)
    _, stats = core_periphery(und)
    order = sorted(und.nodes(), key=lambda v: (-und.degree(v), str(v)))
    n, k = len(order), stats["core_size"]
    adj = nx.to_numpy_array(und, nodelist=order) > 0
    size = int(np.ceil(n / 60))  # players per block, so that the pattern is visible at print size
    blocks = int(np.ceil(n / size))
    padded = np.zeros((blocks * size, blocks * size))
    padded[:n, :n] = adj
    density = padded.reshape(blocks, size, blocks, size).mean(axis=(1, 3))

    mix = pd.read_csv(TABLES / "homophily_mixing.csv")
    mix = mix[mix.network == name]
    bands = ["top10", "11-100", "others"]
    labels = ["Top 10", "11-100", "Others"]

    def matrix(col):
        m = np.full((3, 3), np.nan)
        for _, r in mix.iterrows():
            i, j = bands.index(r.band_a), bands.index(r.band_b)
            m[i, j] = m[j, i] = r[col]
        return m

    fig, axes = plt.subplots(1, 3, figsize=(6.5, 3.1), gridspec_kw={"width_ratios": [1.3, 1, 1]}, layout="constrained")
    ax = axes[0]
    ax.imshow(density, cmap="Greys", vmin=0, vmax=np.quantile(density, 0.98), interpolation="nearest")
    edge = k / size - 0.5
    ax.add_patch(plt.Rectangle((-0.5, -0.5), edge + 0.5, edge + 0.5, fill=False, edgecolor=COLORS[1], linewidth=1.6))
    ax.set_title(f"(a) Core of {k} players ({stats['core_share']:.0%})", loc="left", fontsize=9.5)
    ax.set_xlabel("players by decreasing degree", fontsize=8.5)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

    for ax, col, title in ((axes[1], "ratio_all", "(b) all players"), (axes[2], "ratio_deg", "(c) same degree")):
        m = matrix(col)
        im = ax.imshow(np.log2(m), cmap="RdBu_r", vmin=-4, vmax=4)
        ax.set_xticks(range(3), labels, rotation=45, ha="right", fontsize=8)
        ax.set_yticks(range(3), labels if col == "ratio_all" else [""] * 3, fontsize=8)
        for i in range(3):
            for j in range(3):
                strong = abs(np.log2(m[i, j])) > 2.5
                ax.text(j, i, f"{m[i, j]:.1f}", ha="center", va="center", fontsize=8, color="white" if strong else INK)
        ax.set_title(title, loc="left", fontsize=9.5)
        ax.grid(False)
    cbar = fig.colorbar(im, ax=axes[1:], shrink=0.75, pad=0.02)
    cbar.ax.tick_params(labelsize=8)
    cbar.set_label(r"$\log_2$ (observed / expected)", fontsize=8.5)
    save(fig, "fig_core_homophily")


def _draw_reproduction(ax):
    """Relative difference between our value and the paper's, per reference measure of Michieli (2018)."""
    rep = pd.read_csv(TABLES / "michieli_reproduction.csv")
    rep["paper"] = pd.to_numeric(rep["paper"], errors="coerce")
    rep["ours"] = pd.to_numeric(rep["ours"], errors="coerce")
    rep = rep[rep["paper"].notna() & rep["ours"].notna() & (rep["paper"] != 0)].copy()
    rep["pct"] = 100 * (rep["ours"] - rep["paper"]) / rep["paper"].abs()
    ypos = np.arange(len(rep))[::-1]
    ax.axvline(0, color=MUTED, linewidth=0.9)
    for y, (_, r) in zip(ypos, rep.iterrows(), strict=True):
        close = abs(r["pct"]) <= 5
        ax.scatter(r["pct"], y, s=24, color=COLORS[2] if close else COLORS[1], edgecolor="none", zorder=3)
    ax.set_xscale("symlog", linthresh=1)
    ax.set_xlim(-2, 1000)
    ax.set_xticks([-1, 0, 1, 10, 100, 1000], ["-1", "0", "1", "10", "100", "1000"])
    ax.minorticks_off()
    ax.set_yticks(ypos, [f"{r['network'].split()[0]} {r['measure'][:24]}" for _, r in rep.iterrows()], fontsize=6.8)
    ax.set_xlabel("difference from the paper, % (symlog)")
    ax.grid(axis="y", visible=False)
    ax.set_title("(c) reproduction of the reference study", loc="left", fontsize=10)


def _draw_sensitivity(ax):
    """p-values of H1, H3 and H4 (top-10 share) under each cleaning choice."""
    sens = pd.read_csv(TABLES / "sensitivity_tests.csv")
    sens = sens[sens["statistic"] == "top10_pagerank_share"].copy()
    tests = [
        ("H1", sens[sens["hypothesis"] == "H1"]),
        ("H3 grass vs clay", sens[(sens["hypothesis"] == "H3") & sens["comparison"].str.contains("Clay")]),
        ("H4 WTA vs ATP", sens[sens["hypothesis"] == "H4"]),
    ]
    variants = ["baseline", "no_retirements", "walkovers_kept", "carpet_as_hard"]
    labels = {
        "baseline": "baseline",
        "no_retirements": "no retirements",
        "walkovers_kept": "walkovers kept",
        "carpet_as_hard": "carpet as hard",
    }
    ypos = 0.0
    yticks, ylabels = [], []
    for name, frame in tests:
        for v in variants:
            row = frame[frame["variant"] == v]
            if row.empty:
                continue
            p = float(row["p_value"].iloc[0])
            ax.scatter(
                p, ypos, s=26, color=COLORS[0] if p < 0.05 else "white", edgecolor=COLORS[0], linewidth=1.1, zorder=3
            )
            yticks.append(ypos)
            ylabels.append(f"{name}, {labels[v]}")
            ypos -= 1
        ypos -= 0.6
    ax.axvline(0.05, color=MUTED, linestyle="--", linewidth=0.9)
    ax.set_yticks(yticks, ylabels, fontsize=7.2)
    ax.set_xscale("log")
    ax.set_xlim(0.003, 0.3)
    ax.set_xlabel("two-sided permutation $p$-value (log scale)")
    ax.grid(axis="y", visible=False)
    ax.set_title("(d) sensitivity to cleaning choices", loc="left", fontsize=10)


def figure_validity():
    """Validity of the data and of the reproduction: four panels in a 2x2 grid."""
    fig, axes = plt.subplots(2, 2, figsize=(5.9, 5.0), gridspec_kw={"width_ratios": [1, 1.25]})
    _draw_sources(axes[0, 0], axes[0, 1])
    _draw_reproduction(axes[1, 0])
    _draw_sensitivity(axes[1, 1])
    fig.tight_layout()
    save(fig, "fig_validity")


def figure_global_heatmap():
    """Global measures of the nine comparative networks; colour is scaled within each measure."""
    g = pd.read_csv(TABLES / "global_measures.csv").set_index("network").loc[NETS]
    sw = pd.read_csv(TABLES / "structure_summary.csv").set_index("network").loc[NETS]
    short = {**SHORT, "td_atp_2007_2025": "ATP", "td_wta_2007_2025": "WTA"}
    values = pd.DataFrame(index=NETS)
    values["density"] = g["density"]
    values["giant component"] = g["giant_fraction"]
    values["mean distance"] = g["avg_path_giant"]
    values["reciprocity"] = g["reciprocity"]
    values["modularity"] = g["modularity"]
    values["degree assortativity"] = g["degree_assortativity"]
    values["Gini, in-strength"] = g["gini_in_strength"]
    values["degree centralization"] = g["degree_centralization"]
    values["small-world $\\sigma$"] = sw["sw_sigma"]
    values["top-10 PageRank share"] = g["top10_pagerank_share"]
    values["cyclic / transitive triads"] = g["triad_030C"] / g["triad_030T"]
    values["PageRank vs rank, $\\rho$"] = g["spearman_pagerank_atp_rank"]
    digits = {"density": 3, "mean distance": 2, "small-world $\\sigma$": 2}
    fig, ax = plt.subplots(figsize=(5.9, 3.9))
    norm = (values - values.min()) / (values.max() - values.min())
    cmap = LinearSegmentedColormap.from_list("ink", ["#f4f8fd", COLORS[0]])
    ax.imshow(norm.T.values, cmap=cmap, aspect="auto", vmin=0, vmax=1)
    for j, measure in enumerate(values.columns):
        for i in range(len(NETS)):
            v = values.iloc[i, j]
            d = digits.get(measure, 2 if abs(v) >= 0.1 else 3)
            ax.text(
                i,
                j,
                f"{v:.{d}f}".replace("-", "$-$"),
                ha="center",
                va="center",
                fontsize=7.5,
                color="white" if norm.iloc[i, j] > 0.6 else INK,
            )
    ax.set_xticks(range(len(NETS)), [short[n] for n in NETS], fontsize=8)
    ax.set_yticks(range(len(values.columns)), list(values.columns), fontsize=8)
    ax.tick_params(length=0)
    ax.grid(False)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.axvline(3.5, color="white", linewidth=3)
    ax.axvline(6.5, color="white", linewidth=3)
    ax.set_xlabel("eras (left), surfaces (middle), tours (right); colour is scaled within each row")
    fig.tight_layout()
    save(fig, "fig_global_heatmap")


def figure_hypotheses():
    """All hypothesis tests on one page: network tests against the null, H2 z-scores, and the three levels."""
    tests = pd.read_csv(TABLES / "hypothesis_tests.csv")
    h5 = pd.read_csv(TABLES / "triads_h5.csv")
    levels = pd.read_csv(TABLES / "levels_tests.csv")
    fig = plt.figure(figsize=(5.9, 6.2))
    gs = fig.add_gridspec(3, 1, height_ratios=[10, 9, 11], hspace=0.55)

    ax = fig.add_subplot(gs[0])
    net = tests[tests["hypothesis"].isin(["H1", "H3", "H4"])].copy()
    rows = []
    for r in net.itertuples(index=False):
        comp = {
            "ATP 2007-2018 vs 2019-2025 (season means)": "2007-18 vs 2019-25",
            "ATP Grass vs Clay": "grass vs clay",
            "ATP Grass vs Hard": "grass vs hard",
            "WTA vs ATP, paired season differences 2007-2025": "WTA vs ATP",
        }[r.comparison]
        stat = {"top10_pagerank_share": "top-10 share", "degree_centralization": "centralization"}[r.statistic]
        rows.append((f"{r.hypothesis} {stat}, {comp}", r.diff, r.p_value))
    for r in h5.itertuples(index=False):
        rows.append(
            (f"{r.hypothesis}  cyclic ratio, {'2007-12' if r.hypothesis == 'H5' else 'WTA vs ATP'}", r.diff, r.p_value)
        )
    for i, (_label, diff, p) in enumerate(rows):
        ax.scatter(
            diff, i, s=26, color=COLORS[0] if p < 0.05 else "white", edgecolor=COLORS[0], linewidth=1.1, zorder=3
        )
        ax.text(1.02, i, f"$p$ = {p:.3f}", transform=ax.get_yaxis_transform(), va="center", fontsize=7.5, color=INK)
    ax.axvline(0, color=MUTED, linewidth=0.9)
    ax.set_yticks(range(len(rows)), [r[0] for r in rows], fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("observed difference (filled: $p < 0.05$)")
    ax.grid(axis="y", visible=False)
    ax.set_title("(a) network-level tests H1, H3, H4 and H5", loc="left", fontsize=10)

    ax = fig.add_subplot(gs[1])
    h2 = tests[tests["hypothesis"] == "H2"].copy()
    h2["net"] = h2["comparison"].str.replace(" vs configuration model", "", regex=False).str.replace("td_", "")
    h2 = h2.sort_values("z").reset_index(drop=True)
    for i, r in h2.iterrows():
        ax.scatter(r["z"], i, s=24, color=COLORS[2], edgecolor="none", zorder=3)
    ax.set_yticks(range(len(h2)), [SHORT.get("td_" + n, n) for n in h2["net"]], fontsize=7.5)
    ax.set_xlabel("$z$-score of degree assortativity against 200 configuration nulls")
    ax.grid(axis="y", visible=False)
    ax.set_title("(b) H2, degree assortativity above the null in all nine networks", loc="left", fontsize=10)

    ax = fig.add_subplot(gs[2])
    lev = levels.copy()
    labels = []
    for i, r in enumerate(lev.itertuples(index=False)):
        if r.hypothesis == "H6":
            era = r.comparison.split(":")[0].replace("td_", "")
            lab = f"H6 {r.statistic.replace('beta ', '')}, {era.replace('atp_', '').replace('_', '-')}"
        else:
            lab = {
                "Clay vs on Hard": "H7 hard vs clay",
                "Grass vs on Hard": "H7 hard vs grass",
                "same surface profile": "H8 shared surface profile",
                "clay-hard specialisation": "H8 specialisation distance",
            }[
                next(
                    k
                    for k in ("Clay vs on Hard", "Grass vs on Hard", "same surface profile", "clay-hard specialisation")
                    if k in r.comparison
                )
            ]
        labels.append(lab)
        ax.scatter(
            r.value,
            i,
            s=24,
            color=COLORS[0] if r.p_value < 0.05 else "white",
            edgecolor=COLORS[0],
            linewidth=1.1,
            zorder=3,
        )
        ax.text(
            1.02, i, f"$p$ = {r.p_value:.3f}", transform=ax.get_yaxis_transform(), va="center", fontsize=7.5, color=INK
        )
    ax.axvline(0, color=MUTED, linewidth=0.9)
    ax.set_yticks(range(len(labels)), labels, fontsize=7)
    ax.invert_yaxis()
    ax.set_xlabel("coefficient (H6: $\\beta$ on log PageRank and log wins; H7, H8: QAP $r$)")
    ax.grid(axis="y", visible=False)
    ax.set_title("(c) monadic, dyadic and mixed levels", loc="left", fontsize=10)
    save(fig, "fig_hypotheses")


def figure_topology():
    """Degree distributions (top row) and targeted versus random removal (bottom row), per group."""
    fig, axes = plt.subplots(2, 3, figsize=(5.9, 4.6), sharey="row")
    for col, (title, nets) in enumerate(GROUPS):
        ax_deg, ax_rob = axes[0, col], axes[1, col]
        for i, n in enumerate(nets):
            deg = np.sort(np.array([d for _, d in undirected(n).degree()]))
            ccdf = 1 - np.arange(len(deg)) / len(deg)
            ax_deg.loglog(deg, ccdf, color=COLORS[i], label=PLAIN[n], marker=MARKERS[i], markevery=0.12, markersize=3.5)
            c = pd.read_csv(TABLES / f"{n}_robustness.csv")
            ax_rob.plot(c["fraction"], c["attack"], color=COLORS[i], marker=MARKERS[i], markersize=3, label=PLAIN[n])
            ax_rob.plot(c["fraction"], c["random"], color=COLORS[i], linestyle="--", linewidth=1.0)
        ax_deg.set_title(title, loc="left", fontsize=9)
        ax_deg.set_xlabel("distinct opponents $k$")
        ax_deg.legend(loc="lower left", fontsize=7)
        ax_rob.set_xlabel("share of players removed")
        ax_rob.legend(loc="lower left", fontsize=7)
    axes[0, 0].set_ylabel(r"$P(K \geq k)$")
    axes[1, 0].set_ylabel("largest component")
    axes[1, 2].text(
        0.98,
        0.98,
        "solid: by PageRank\ndashed: random",
        transform=axes[1, 2].transAxes,
        ha="right",
        va="top",
        fontsize=7,
        color=MUTED,
    )
    fig.tight_layout()
    save(fig, "fig_topology")


def figure_structure():
    """Core-periphery, HITS and rich-club values of the nine networks, one row per network."""
    st = pd.read_csv(TABLES / "structure_summary.csv").set_index("network").loc[NETS]
    rc = pd.read_csv(TABLES / "rich_club_summary.csv").set_index("network").loc[NETS]
    ypos = np.arange(len(NETS))[::-1]
    labels = [SHORT[n] for n in NETS]
    fig, axes = plt.subplots(1, 4, figsize=(5.9, 3.4), sharey=True, layout="constrained")
    ax = axes[0]
    ax.scatter(st["authority_pagerank_spearman"], ypos, s=18, color=COLORS[0], label="vs PageRank", zorder=3)
    ax.scatter(
        st["authority_rank_spearman"], ypos, s=18, color=COLORS[1], marker="s", label="vs official rank", zorder=3
    )
    ax.axvline(0, color=MUTED, linewidth=0.8)
    ax.set_xlim(-1, 1.05)
    ax.set_yticks(ypos, labels, fontsize=7.5)
    ax.set_title("(a) HITS", loc="left", fontsize=8.5)
    ax = axes[1]
    ax.scatter(st["core_share"], ypos, s=18, color=COLORS[0], label="core share", zorder=3)
    ax.scatter(st["core_kcore_jaccard"], ypos, s=18, color=COLORS[2], marker="^", label="Jaccard vs k-core", zorder=3)
    ax.set_xlim(0, 1)
    ax.set_title("(b) core", loc="left", fontsize=8.5)
    ax = axes[2]
    ax.scatter(st["density_core"], ypos, s=18, color=COLORS[0], label="core", zorder=3)
    ax.scatter(st["density_periphery"], ypos, s=18, color=COLORS[1], marker="s", label="periphery", zorder=3)
    ax.set_xscale("log")
    ax.set_title("(c) density", loc="left", fontsize=8.5)
    ax = axes[3]
    ax.hlines(ypos, 1.0, rc["rho_rich_peak"], color=COLORS[0], linewidth=1.1, alpha=0.6)
    ax.scatter(rc["rho_rich_peak"], ypos, s=18, color=COLORS[0], zorder=3)
    ax.axvline(1.0, color=MUTED, linestyle="--", linewidth=0.8)
    ax.set_xlim(0.99, 1.25)
    ax.set_title(r"(d) rich club", loc="left", fontsize=8.5)
    for axis in axes:
        axis.grid(axis="y", visible=False)
        axis.tick_params(axis="x", labelsize=7)
    save(fig, "fig_structure")


def figure_study_design():
    """Span, size and surface of the nine comparative networks, from the tennis-data summary."""
    summ = pd.read_csv(TABLES / "td_networks_summary.csv").set_index("network").loc[NETS]
    fig, ax = plt.subplots(figsize=(5.9, 2.7), layout="constrained")
    ypos = np.arange(len(NETS))[::-1]
    for y, n in zip(ypos, NETS, strict=True):
        start = pd.Timestamp(summ.loc[n, "first"]).year + (pd.Timestamp(summ.loc[n, "first"]).day_of_year / 365.25)
        end = pd.Timestamp(summ.loc[n, "last"]).year + (pd.Timestamp(summ.loc[n, "last"]).day_of_year / 365.25)
        color = COLORS[0] if n in ERAS else COLORS[1] if n in SURFACES else COLORS[2]
        ax.barh(y, end - start, left=start, height=0.55, color=color, alpha=0.85)
        ax.text(
            end + 0.3,
            y,
            f"{int(summ.loc[n, 'matches']):,} matches, {int(summ.loc[n, 'players']):,} players",
            va="center",
            fontsize=7,
            color=INK,
        )
    ax.set_yticks(ypos, [SHORT[n] for n in NETS], fontsize=7.5)
    ax.set_xlim(1999, 2050)
    ax.set_xticks([2000, 2007, 2013, 2019, 2025])
    ax.set_xlabel("period covered by the matches")
    ax.grid(axis="y", visible=False)
    save(fig, "fig_study_design")


def figure_prestige():
    """PageRank against median official rank for the leaders of each network, with the top five labelled."""
    fig, axes = plt.subplots(2, 3, figsize=(5.9, 4.0), layout="constrained")
    cols = ERAS + ["td_wta_2007_2025"]
    for ax, n in zip(axes.flat, cols, strict=False):
        nodes = pd.read_csv(TABLES / f"{n}_nodes.csv").set_index("node")
        ranks = pd.read_csv(PROCESSED / f"{n}_ranks.csv", index_col="player")["rank"]
        pr = nodes["pagerank"]
        common = pr.index.intersection(ranks.index)
        x = pr[common]
        yv = ranks[common]
        ax.scatter(x, yv, s=8, color=COLORS[0], alpha=0.45, edgecolors="none")
        placed = []
        for player in x.sort_values(ascending=False).index:
            if len(placed) == 3:
                break
            px, py = np.log10(x[player]), np.log10(yv[player])
            if any(abs(px - qx) < 0.25 and abs(py - qy) < 0.25 for qx, qy in placed):
                continue
            placed.append((px, py))
            ax.annotate(
                player.split(" ")[0],
                (x[player], yv[player]),
                xytext=(3, 2),
                textcoords="offset points",
                fontsize=6.5,
                color=INK,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_title(("ATP " + SHORT[n]) if n in ERAS else SHORT[n], loc="left", fontsize=8.5)
        ax.set_xlabel("PageRank", fontsize=7.5)
        ax.tick_params(labelsize=7)
    axes[0, 0].set_ylabel("official rank (median)", fontsize=7.5)
    axes[1, 0].set_ylabel("official rank (median)", fontsize=7.5)
    axes[1, 2].axis("off")
    axes[1, 2].text(
        0.0,
        0.5,
        "Each point is a player.\nLabels: the highest PageRank scores (up to three).\nRank 1 is the best position.",
        fontsize=7.5,
        color=MUTED,
        va="center",
    )
    save(fig, "fig_prestige")


def main():
    table_networks()
    table_reproduction()
    table_global()
    samples = table_null()
    table_tests()
    table_hypothesis_summary()
    table_top10()
    table_structure()
    table_levels()
    table_sensitivity()
    table_topology()
    table_abc()
    style()
    figure_topology()
    figure_yearly()
    figure_network_core()
    figure_study_design()
    figure_validity()
    figure_prestige()
    figure_global_heatmap()
    figure_core_homophily()
    figure_structure()
    figure_hypotheses()
    print(f"Tables in {OUT_TAB}, figures in {OUT_FIG} (null models: {samples} samples)")


if __name__ == "__main__":
    main()
