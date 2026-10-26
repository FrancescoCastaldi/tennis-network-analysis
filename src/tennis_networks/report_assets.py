"""LaTeX tables and figures of the report, built only from results/ and data/processed/.

Run (after analysis, hypotheses and reproduce):
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

from tennis_networks.config import PROCESSED, REPORT, TABLES
from tennis_networks.loaders import load_network
from tennis_networks.loaders import load_undirected as undirected
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
    nu = pd.DataFrame(
        {
            "avg_clustering": {n: nx.average_clustering(h) for n, h in und.items()},
            "transitivity": {n: nx.transitivity(h) for n, h in und.items()},
            "degree_assortativity": {n: nx.degree_assortativity_coefficient(h) for n, h in und.items()},
        }
    )
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
        ("Avg.\\ clustering $C$", nu["avg_clustering"], 3),
        ("Transitivity $T$", nu["transitivity"], 3),
        ("Degree assortativity $r$", nu["degree_assortativity"], 3),
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
    stats = [("degree_assortativity", "$r$"), ("avg_clustering", "$C$"), ("transitivity", "$T$")]
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
    stat = {"top10_pagerank_share": "top-10 PageRank share", "degree_centralization": "degree centralization"}
    rows = []
    for h in ("H1", "H2", "H3", "H4"):
        if h == "H2":
            h2 = d[d["hypothesis"] == "H2"]
            rows.append(
                f"H2 & degree assortativity & each of the 8 networks vs null & "
                f"{num(h2['value_a'].min(), 3)} to {num(h2['value_a'].max(), 3)} & "
                f"{num(h2['value_b'].min(), 3)} to {num(h2['value_b'].max(), 3)} & "
                f"$>0$ in all & 0 & $\\le${num(h2['p_value'].max(), 3)} \\\\"
            )
            continue
        for r in d[d["hypothesis"] == h].itertuples(index=False):
            comp = {"H1": "2007-18 vs 2019-25 (seasons)", "H4": "WTA vs ATP (paired seasons)"}.get(
                h, r.comparison.replace("ATP ", "")
            )
            expected = num(r.perm_mean_diff, 3) if not pd.isna(r.perm_mean_diff) else "0"
            rows.append(
                f"{h} & {stat[r.statistic]} & {comp} & {num(r.value_a, 3)} & {num(r.value_b, 3)} & "
                f"{num(r.diff, 3)} & {expected} & {num(r.p_value, 3)} \\\\"
            )
    if (TABLES / "triads_h5.csv").exists():
        h5 = pd.read_csv(TABLES / "triads_h5.csv")
        for r in h5.itertuples(index=False):
            label = "H5" if r.hypothesis == "H5" else "H5 (tours)"
            comp = "2007-12 vs other eras" if r.hypothesis == "H5" else "WTA vs ATP (paired seasons)"
            rows.append(
                f"{label} & cyclic triad ratio & {comp} & {num(r.value_a, 3)} & {num(r.value_b, 3)} & "
                f"{num(r.diff, 3)} & 0 & {num(r.p_value, 3)} \\\\"
            )
    write(
        "tab_tests.tex",
        "\n".join(
            [
                r"\begin{tabular}{@{}ll>{\raggedright\arraybackslash}p{3.1cm}rrrrr@{}}",
                r"\toprule",
                r"H & Statistic & Comparison & A & B & A$-$B & $E_0$[A$-$B] & $p$ \\",
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
                (r"Normalised rich-club $\rho_{\text{rich}}$", "rho_rich_peak", 3),
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
    if (TABLES / "triads_h5.csv").exists():
        h5 = pd.read_csv(TABLES / "triads_h5.csv")
        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Network level: "
            r"Triad hierarchy (cyclic ratio $030C/030T$, random baseline $= 1/3$)}} \\"
        )
        for r in h5.itertuples(index=False):
            label = "H5" if r.hypothesis == "H5" else "H5 (tours)"
            comp = "ATP 2007-12 vs other eras" if r.hypothesis == "H5" else "WTA vs ATP (paired seasons)"
            note = f"{num(r.value_a, 3)} vs {num(r.value_b, 3)}"
            diff_str, p_str = num(r.diff, 3), num(r.p_value, 3)
            rows.append(f"{label} & Network & {comp} & cyclic triad ratio & {diff_str} & {p_str} & {note} \\\\")
        rows.append(r"\midrule")

    if (TABLES / "levels_tests.csv").exists():
        lt = pd.read_csv(TABLES / "levels_tests.csv")
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
            pr_val, pr_p = num(pr_row["value"], 3), num(pr_row["p_value"], 3)
            rows.append(
                f"H6 & Monadic & {era_name} ($n={n_val}$) & $\\beta$ log PageRank & {pr_val} & {pr_p} & {r2_val} \\\\"
            )
            w_val, w_p = num(w_row["value"], 3), num(w_row["p_value"], 3)
            rows.append(f"   &         &                      & $\\beta$ log wins     & {w_val} & {w_p} & \\\\")
        rows.append(r"\midrule")

        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Dyadic level: "
            r"QAP correlation of head-to-head dominance balance across surfaces}} \\"
        )
        dya = lt[lt["level"] == "dyadic"]
        for r in dya.itertuples(index=False):
            comp = "Clay vs Hard balance" if "Clay" in r.comparison else "Grass vs Hard balance"
            note = f"$n={r.n}$, $E_0[r]=0.000$"
            rows.append(
                f"H7 & Dyadic & {comp} & QAP Pearson $r$ & {num(r.value, 3)} & {num(r.p_value, 3)} & {note} \\\\"
            )
        rows.append(r"\midrule")

        rows.append(
            r"\multicolumn{7}{@{}l}{\emph{Mixed level: "
            r"QAP correlation of surface specialisation with match encounters}} \\"
        )
        mix = lt[lt["level"] == "mixed"]
        for r in mix.itertuples(index=False):
            comp = "Same surface profile vs meetings" if "profile" in r.comparison else "Specialisation gap vs meetings"
            note = "$n=328$, 3 classes" if "profile" in r.comparison else "$n=328$, Euclidean diff"
            rows.append(
                f"H8 & Mixed & {comp} & QAP Pearson $r$ & {num(r.value, 3)} & {num(r.p_value, 3)} & {note} \\\\"
            )

    body = "\n".join(
        [
            r"\begin{tabular}{@{}llp{3.6cm}lrrr@{}}",
            r"\toprule",
            r"Hyp. & Level & Comparison / Target & Predictor / Stat & Coeff. / $r$ & $p$ & Notes \\",
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
        "Who dominates, and who forms the elite of an era",
        "In- and out-degree, PageRank, HITS authority and hub scores",
        "In-degree counts the opponents a player has beaten; PageRank discounts wins over weak "
        "opponents, so it rewards beating players who also win; an authority beats players who go deep.",
    ),
    (
        "How unequal prestige and wins are",
        "Share of PageRank held by the top 10, Gini coefficient of in-strength",
        "A high share means a few players hold most of the prestige of the tour; a low one means "
        "wins are spread over many players (competitive balance).",
    ),
    (
        "Backbone of the tour: regular professionals against the periphery",
        "$k$-core decomposition, Borgatti-Everett core-periphery model",
        "The core is the inner circle that meets everyone; the periphery is made of qualifiers and "
        "one-off entrants who mostly meet core players.",
    ),
    (
        "Integration against fragmentation",
        "Components, average distance, diameter, global efficiency, ratio to a random reference",
        "Short distances mean that an upset chain connects any two players: the tour is one arena, "
        "not a set of separate circuits.",
    ),
    (
        "Robustness to losing its stars",
        "Largest component after removing players at random and in decreasing PageRank order",
        "A faster drop under targeted removal than under random removal shows how much of the "
        "connectivity of the tour rests on a few high-prestige players.",
    ),
    (
        "Local rivalries and hierarchy",
        "Clustering, transitivity, triad census",
        "Closed triads are players with common opponents; a transitive triad is a clean hierarchy "
        "(A beats B beats C, A beats C) and a cycle is an upset loop.",
    ),
    (
        "Whether the tour has mega-hubs",
        "Power-law fit of the degree distribution and likelihood-ratio tests against lognormal, "
        "exponential and truncated power law",
        "A power law would mean a few players meet a very large share of the field; bracket sizes "
        "and calendars bound the number of opponents, so a bounded tail is expected.",
    ),
    (
        "Do top players meet top players",
        "Degree and ranking-band assortativity, band mixing against permutation nulls",
        "Positive values mean elite against elite; a hub-and-spoke tour gives negative values. "
        "The null that keeps the number of opponents separates seeding from plain activity.",
    ),
    (
        "Structural roles",
        "Cosine similarity of opponent vectors, QAP correlation with the ranking gap",
        "Players who face the same opponents occupy the same position in the tour; the QAP test "
        "asks whether this position tracks ranking.",
    ),
    (
        "Artefact of the degree distribution or real structure",
        "Configuration model, $z$-scores and permutation $p$-values, small-world index $\\sigma$",
        "A statistic far from its degree-preserving random value reflects how the tournaments "
        "are organised, not just how many opponents each player has.",
    ),
    (
        "Cohorts and surface circuits",
        "Louvain communities and modularity",
        "Communities in tennis are mostly career cohorts that never overlapped in time rather "
        "than geographic or stylistic blocs.",
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
                r"\begin{tabular}{@{}" + col % "0.23" + col % "0.29" + col % "0.44" + "@{}}",
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


def style():
    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
            "mathtext.fontset": "stix",
            "font.size": 9,
            "axes.labelsize": 9,
            "axes.titlesize": 9,
            "legend.fontsize": 8,
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
            "lines.markersize": 4,
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


def figure_degree():
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.3), sharey=True)
    for ax, (title, nets) in zip(axes, GROUPS, strict=True):
        for i, n in enumerate(nets):
            deg = np.sort(np.array([d for _, d in undirected(n).degree()]))
            ccdf = 1 - np.arange(len(deg)) / len(deg)
            ax.loglog(deg, ccdf, color=COLORS[i], label=PLAIN[n], marker=MARKERS[i], markevery=0.12, markersize=3.5)
        ax.set_title(title, loc="left")
        ax.set_xlabel("distinct opponents $k$")
        ax.legend(loc="lower left")
    axes[0].set_ylabel(r"$P(K \geq k)$")
    fig.tight_layout()
    save(fig, "fig_degree_ccdf")


def figure_robustness():
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.4), sharey=True)
    for ax, (title, nets) in zip(axes, GROUPS, strict=True):
        for i, n in enumerate(nets):
            c = pd.read_csv(TABLES / f"{n}_robustness.csv")
            ax.plot(c["fraction"], c["attack"], color=COLORS[i], marker=MARKERS[i], markersize=3, label=PLAIN[n])
            ax.plot(c["fraction"], c["random"], color=COLORS[i], linestyle="--", linewidth=1.1)
        ax.set_title(title, loc="left")
        ax.set_xlabel("share of players removed")
        ax.legend(loc="lower left")
    axes[0].set_ylabel("relative largest component")
    axes[2].text(
        0.98,
        0.98,
        "solid: by PageRank\ndashed: random",
        transform=axes[2].transAxes,
        ha="right",
        va="top",
        fontsize=7.5,
        color=MUTED,
    )
    fig.tight_layout()
    save(fig, "fig_robustness")


def figure_yearly():
    y = pd.read_csv(TABLES / "yearly_statistics.csv").set_index("season")
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.4))
    stats = ("top10_pagerank_share", "degree_centralization")
    labels = ("(a) top-10 PageRank share", "(b) degree centralization")
    for ax, stat, label in zip(axes, stats, labels, strict=True):
        ax.axvspan(2006.5, 2018.5, color=GRID, alpha=0.6, linewidth=0)
        for i, tour in enumerate(("ATP", "WTA")):
            s = y[f"{tour}_{stat}"].dropna()
            ax.plot(s.index, s.values, color=COLORS[i], marker=MARKERS[i], label=tour)
        ax.set_title(label, loc="left")
        ax.set_xlabel("season")
        ax.legend(loc="upper right")
    axes[0].text(2012.5, axes[0].get_ylim()[0], "2007-2018", ha="center", va="bottom", fontsize=7.5, color=MUTED)
    fig.tight_layout()
    save(fig, "fig_yearly")


def figure_network_core():
    fig, (ax_net, ax_triad) = plt.subplots(1, 2, figsize=(6.3, 3.0), gridspec_kw={"width_ratios": [1.15, 1.0]})

    # (a) Network core (Top 12 players of 2007-2012)
    spec_2007 = {"id": "td_atp_2007_2012", "file": "td_atp_2007_2012.csv", "directed": True}
    g = load_network(spec_2007)
    nodes_df = pd.read_csv(TABLES / "td_atp_2007_2012_nodes.csv").set_index("node")
    top_players = list(nodes_df["pagerank"].sort_values(ascending=False).head(12).index)
    sub = g.subgraph(top_players).copy()

    big4 = {"Nadal R.", "Djokovic N.", "Federer R.", "Murray A."}
    node_colors = ["#2a78d6" if p in big4 else "#eb6834" for p in top_players]
    node_sizes = [180 + 2600 * nodes_df.loc[p, "pagerank"] for p in top_players]

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
                color="#888888",
                lw=0.4 + 0.12 * min(w, 10),
                alpha=0.5,
                shrinkA=9,
                shrinkB=9,
                connectionstyle="arc3,rad=0.07",
            ),
        )

    ax_net.scatter(
        [pos[p][0] for p in top_players],
        [pos[p][1] for p in top_players],
        s=node_sizes,
        c=node_colors,
        zorder=5,
        edgecolors="#0b0b0b",
        linewidths=0.8,
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
            1.22 * x,
            1.22 * y,
            short_names.get(p, p),
            fontsize=6.5,
            ha=ha,
            va=va,
            weight="bold" if p in big4 else "normal",
            color="#0b0b0b",
        )

    # Legend for Big Four vs Contenders
    ax_net.scatter([], [], c="#2a78d6", s=50, edgecolors="#0b0b0b", lw=0.6, label="Big Four")
    ax_net.scatter([], [], c="#eb6834", s=50, edgecolors="#0b0b0b", lw=0.6, label="Contenders")
    ax_net.legend(loc="lower left", fontsize=6.5, frameon=False, bbox_to_anchor=(-0.05, -0.05))

    ax_net.set_xlim(-1.6, 1.6)
    ax_net.set_ylim(-1.6, 1.6)
    ax_net.axis("off")
    ax_net.set_title("(a) 2007-2012 elite core (N = 12)", loc="left", fontsize=8.5)

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
    colors = ["#2a78d6" if z >= 0 else "#eb6834" for z in zs]

    ax_triad.barh(y_pos, zs, color=colors, height=0.6, edgecolor="none", zorder=3)
    ax_triad.axvline(0, color="#0b0b0b", linewidth=0.8, zorder=4)
    ax_triad.axvline(1.96, color="#52514e", linestyle="--", linewidth=0.6, zorder=2)
    ax_triad.axvline(-1.96, color="#52514e", linestyle="--", linewidth=0.6, zorder=2)
    ax_triad.set_yticks(y_pos)
    ax_triad.set_yticklabels(triad_types, fontsize=6.5)
    ax_triad.set_xlabel("z-score vs configuration null", fontsize=7.5)
    ax_triad.set_title("(b) 16-class triad z-score spectrum", loc="left", fontsize=8.5)
    ax_triad.tick_params(axis="both", which="major", labelsize=6.5)
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

    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.9), gridspec_kw={"width_ratios": [1.3, 1, 1]}, layout="constrained")
    ax = axes[0]
    ax.imshow(density, cmap="Greys", vmin=0, vmax=np.quantile(density, 0.98), interpolation="nearest")
    edge = k / size - 0.5
    ax.add_patch(plt.Rectangle((-0.5, -0.5), edge + 0.5, edge + 0.5, fill=False, edgecolor=COLORS[1], linewidth=1.6))
    ax.set_title(f"(a) Core of {k} players ({stats['core_share']:.0%})", loc="left")
    ax.set_xlabel("players by decreasing degree")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)

    for ax, col, title in ((axes[1], "ratio_all", "(b) all players"), (axes[2], "ratio_deg", "(c) same degree")):
        m = matrix(col)
        im = ax.imshow(np.log2(m), cmap="RdBu_r", vmin=-4, vmax=4)
        ax.set_xticks(range(3), labels, rotation=45, ha="right")
        ax.set_yticks(range(3), labels if col == "ratio_all" else [""] * 3)
        for i in range(3):
            for j in range(3):
                strong = abs(np.log2(m[i, j])) > 2.5
                ax.text(j, i, f"{m[i, j]:.1f}", ha="center", va="center", fontsize=7, color="white" if strong else INK)
        ax.set_title(title, loc="left")
        ax.grid(False)
    cbar = fig.colorbar(im, ax=axes[1:], shrink=0.75, pad=0.02)
    cbar.set_label(r"$\log_2$ (observed / expected)")
    save(fig, "fig_core_homophily")


def main():
    table_networks()
    table_reproduction()
    table_global()
    samples = table_null()
    table_tests()
    table_top10()
    table_structure()
    table_levels()
    table_topology()
    table_abc()
    style()
    figure_degree()
    figure_robustness()
    figure_yearly()
    figure_network_core()
    figure_core_homophily()
    print(f"Tables in {OUT_TAB}, figures in {OUT_FIG} (null models: {samples} samples)")


if __name__ == "__main__":
    main()
