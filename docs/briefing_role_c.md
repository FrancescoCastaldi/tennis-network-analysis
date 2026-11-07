# Author Briefing: Role C (Interpretation and Critique)

**Lead Author**: Paolo Fusco (Role C)  
**Evaluation Weight**: 20% of the final exam grade  
**Target Word Budget**: ~950 words total (strictly under group allocation)  
* Section 6: *Conclusion* (~450 words target)  
* Section 7: *Critique* (~500 words target)  
**Target File**: `report/main.tex` (between line `\section{Conclusion}` and `\begin{thebibliography}`)

---

## 1. Executive Summary and Role Scope

In the exam grading rubric set by Prof. Saverio Giallorenzo, Role C is responsible for the qualitative synthesis, domain interpretation, and critical reflection on methodological limitations.

All empirical tables, figures, and hypothesis tests have been computed, validated, and summarized in Section 5 (*Measures and Results*). Your task is not to recalculate metrics, but to step back and provide an executive interpretation: what do these findings tell us about professional tennis as a competitive ecosystem? What are the limitations and caveats of our modeling choices?

---

## 2. Section 6: Conclusion (~450 words target)

### Key Empirical Findings to Synthesize
1. **Network Topology and Absence of Scale-Free Structure**:
   * All degree distributions (degree CCDF figure) are concave on a log-log scale and drop sharply after 100 opponents.
   * Professional tennis is fundamentally bounded by tournament regulations: bracket caps (32 to 128 players) and annual tournament limits (~20 to 25 events per player) prevent power-law scale-free emergence.
2. **The Touring Core and Percolation Robustness**:
   * The Borgatti-Everett discrete core-periphery model identifies a compact core encompassing 16% to 20% of all players (107 to 131 individuals), with intra-core density (~0.65) ten times higher than core-periphery density.
   * Targeted node removal by PageRank (robustness figure) reveals that the tour relies on this elite core for overall cohesion: removing the top 20% halves the largest connected component.
   * Notably, the contemporary era (2019-2025) is the most resilient, retaining 60% of its giant component at 20% node removal (compared to 51% to 55% in earlier eras), indicating a broader distribution of high-level competitive volume among Next Gen contenders.
3. **The Big Three Era: Nuanced Concentration and Triad Rigidity**:
   * In H1, annual top-10 PageRank share was higher during 2007-2018 than 2019-2025 (0.265 against 0.234), but the difference was not statistically significant ($p = 0.060$). Concentration peaked in specific dominant seasons (2009, 2012, 2015) rather than remaining uniformly elevated across twelve years.
   * However, in H5, triadic hierarchy was significantly more rigid during the Big Three peak (2007-2012): the cyclic upset ratio ($030C/030T$) dropped significantly to 0.184 compared to 0.211 in other periods ($p = 0.020$). When the Big Three met mid-tier players, transitive hierarchies were almost unbreachable.
4. **Rejection of Assortativity Null Models (H2)**:
   * Degree assortativity is close to zero ($-0.04$ to $0.10$), significantly less negative than degree-preserving configuration null models ($-0.19$ to $-0.06, z \ge 15$). Tournament seeding systematically guarantees that top players advance to face each other in semifinals and finals, preventing the extreme disassortativity that random pairing would generate.
5. **Multi-Level Relational Insights (H6, H7, H8)**:
   * *Monadic (H6)*: Network PageRank completely subsumes raw win counts in predicting official player rankings ($\beta_1 \approx -0.75, p = 0.001$, while $\beta_2 \approx -0.05, p \ge 0.415$). Quality of victories matters far more than volume.
   * *Dyadic (H7)*: Head-to-head dominance carries over significantly across clay, hard, and grass courts ($r \approx 0.12$ to $0.15, p = 0.001$ via QAP matrix permutation). Psychological and stylistic dominance between player pairs transcends surface speed.
   * *Mixed (H8)*: Players with similar surface specialisation profiles encounter each other significantly more often ($r = 0.056, p = 0.001$), demonstrating scheduling homophily driven by selective tournament entry.
6. **Gender Differences (H4)**:
   * The WTA tour displays significantly lower top-10 PageRank concentration than the ATP tour ($p = 0.016$), especially after 2013, alongside a mild tendency towards cyclic upsets ($p = 0.098$). The women's circuit provided greater competitive parity and turnover among title contenders.

---

## 3. Section 7: Critique (~500 words target)

### Critical Limitations to Discuss
1. **Main-Draw Truncation and Survivor Bias**:
   * Our comparative networks rely on official ATP/WTA main-draw matches.
   * Lower-tier circuits (ATP Challenger Tour, ITF World Tennis Tour, and Grand Slam qualifying draws) are excluded.
   * Consequence: Survivor bias. Peripheral players in our networks are already successful enough to qualify for main draws. The vast majority of professional tennis players competing in lower tiers are invisible, understating the true diameter and degree disparity of the global tennis pyramid.
2. **Multi-Year Temporal Aggregation**:
   * Aggregating matches over multi-year windows (such as six-year eras or 26-season surface graphs) treats static networks as time-invariant snapshots.
   * Consequence: A victory in 2007 receives the same structural weight as a victory in 2012, masking intra-career aging, sudden injury recoveries, and short-term tactical adjustments. Dynamic or temporal network models (time-stamped edge streams) would provide finer temporal resolution.
3. **Size-Dependence of Network Centrality**:
   * Comparing raw network metrics across graphs of unequal sizes (for example, grass with 881 players versus clay with 1,191 players) introduces structural size bias.
   * While we mitigated this through season-level resampling and permutation null models, metrics like PageRank and Freeman degree centralization naturally compress on larger node populations.
4. **Missing Player Attribute Data**:
   * The primary dataset lacks exogenous player covariates such as nationality, age, playing hand (left-handed versus right-handed), height, and backhand style (one-handed versus two-handed).
   * Consequence: We could not test homophily based on geographic proximity, training academies, or generational cohorts through Exponential Random Graph Models (ERGMs) or mixed dyadic regression.
5. **Handling of Incomplete Matches (Walkovers versus Retirements)**:
   * We discarded walkovers (since no tennis was contested), but retained match retirements where players withdrew mid-match due to acute injury.
   * In a small fraction of matches, physical incapacitation rather than tactical dominance determined the edge direction, introducing minor noise into the win-loss graph.

---

## 4. Key Citations to Include in LaTeX
* `\cite{borgatti2000}`: Stephen Borgatti and Martin Everett, *Social Networks*, 2000 (core-periphery modeling).
* `\cite{krackhardt1988}`: David Krackhardt, *Social Networks*, 1988 (QAP permutation tests).
* `\cite{radicchi2011}`: Filippo Radicchi, *PLoS ONE*, 2011.
* `\cite{newman2002}`: Mark Newman, *Physical Review Letters*, 2002.

---

## 5. Style and Collaboration Rules
* **No AI stylistic markers**: Do not use em-dashes, en-dashes, or double hyphens to separate clauses. Use standard human punctuation such as commas, colons, parentheses, or periods.
* **Word ceiling**: Keep Section 6 around 450 words and Section 7 around 500 words. Total word count for Role C should not exceed 950-1,000 words.
* **File encoding**: Ensure your LaTeX text is saved in pure UTF-8 encoding without BOM.
* **Git workflow**: Work on a feature branch and open a pull request (see `CONTRIBUTING.md`). Pull before editing, make focused commits, and run the word count check:
  ```powershell
  .venv\Scripts\python -m tennis_networks.wordcount
  ```
