# Author Briefing: Role A (Context, Problem and Motivation)

**Lead Author**: Shivam Kumar (Role A)  
**Evaluation Weight**: 20% of the final exam grade  
**Target Word Budget**: ~950 words total (strictly under group allocation)  
* Section 1: *Introduction* (~450 words target)  
* Section 2: *Problem and Motivation* (~500 words target)  
**Target File**: `report/main.tex` (between `\begin{document}` and `\section{Datasets}`)

---

## 1. Executive Summary and Role Scope

In the exam grading rubric set by Prof. Saverio Giallorenzo, Role A is responsible for the theoretical foundation, scientific context, and motivating research questions of the study.

All data collection, topological metrics, null models, and multi-level hypothesis tests have already been implemented and frozen in the code repository (`src/tennis_networks/`) and results directory (`results/tables/`). You do not need to guess what the data will show: all numerical outcomes are established facts. Your goal is to construct a compelling, academically rigorous narrative that introduces network science in professional tennis, cites foundational literature, poses three sharp comparative research questions, and outlines the eight hypotheses tested in our study.

---

## 2. Section 1: Introduction (~450 words target)

### Recommended Narrative Structure
1. **Network Science in Sport Analytics**:
   * Traditional sport analytics relies on monadic attributes (points, aces, break points, win-loss percentages).
   * Network science provides a relational perspective, treating matches as structural interactions that capture the collective competitive ecosystem of the professional tour.
2. **Modeling Matches as Complex Networks**:
   * Node definition: professional tennis players.
   * Edge definition: directed from loser to winner, weighted by the number of victories between the pair in the given period.
   * Rationale for directed orientation (loser $\to$ winner): matches prestige flow. When player A beats player B, prestige flows from B to A. In-strength measures total wins, while out-strength measures total defeats.
3. **Prior Literature and Theoretical Benchmarks**:
   * **Radicchi (2011, PLoS ONE)**: *Who is the best player ever? A complex network analysis of the history of professional tennis*. Introduced PageRank to tennis match graphs, establishing that a victory over an elite contender should confer substantially more prestige than defeating an unseeded qualifier.
   * **Michieli (2018, arXiv:1804.08138)**: *Complex network analysis of men single ATP tennis matches*. Analyzed historical ATP matrices (M1 to M4) from 1968 to 2018, reporting small-world properties, degree distributions, and authority scores.
   * **Methodological Gap**: Existing studies predominantly aggregate decades of matches into single monolithic graphs or focus exclusively on men's singles. They overlook systematic comparisons across historical eras, court surfaces, and gender circuits, and do not test relational hypotheses across multiple topological levels.

---

## 3. Section 2: Problem and Motivation (~500 words target)

### Recommended Narrative Structure
1. **Core Problem**:
   * Professional tennis is governed by strict tournament knockout brackets, seeded entries, surface changes, and distinct governing bodies (ATP and WTA).
   * How do these institutional constraints shape the competitive hierarchy, elite dominance, and structural resilience of professional tennis networks?
2. **Three Guiding Research Questions (RQs)**:
   * **RQ1 (Historical Evolution and Eras)**: How did competitive centralization and hierarchical transitivity shift across eras, particularly during the peak of the Big Three (Federer, Nadal, Djokovic) compared to the preceding transition era and the contemporary Next Gen cohort?
   * **RQ2 (Surface Ecology and Specialization)**: How do physical court characteristics (clay, hard, grass) and calendar length impact network density, player reciprocity, and prestige centralization?
   * **RQ3 (Gender and Circuit Comparison)**: Do structural properties and prestige concentration differ between the ATP (men's tour) and the WTA (women's tour) over an identical modern observation window (2007-2025)?
3. **Overview of the Multi-Level Hypothesis Framework (Course Slide L04)**:
   * **Network level (Macro)**:
     * *H1*: Prestige concentration during the Big Three era (2007-2018) versus 2019-2025.
     * *H2*: Degree assortativity compared to Maslov-Sneppen configuration null models (testing if early-round matchmaking creates disassortativity).
     * *H3*: Centralization and prestige on grass versus clay and hard courts.
     * *H4*: Top-10 PageRank concentration in ATP versus WTA tours.
     * *H5*: Triad hierarchy (cyclic upset ratio $030C/030T$) during the Big Three peak (2007-2012) versus other periods.
   * **Monadic level**:
     * *H6*: Network prestige (PageRank) as an explanatory predictor of official ranking beyond raw victory volume.
   * **Dyadic level**:
     * *H7*: Cross-surface carry-over of head-to-head dominance matrices using Quadratic Assignment Procedure (QAP).
   * **Mixed level**:
     * *H8*: Scheduling homophily driven by player surface specialisation profiles using QAP matrix correlation.

---

## 4. Key Citations to Include in LaTeX
Ensure the following references are cited in your draft:
* `\cite{radicchi2011}`: Filippo Radicchi, *PLoS ONE*, 2011.
* `\cite{michieli2018}`: Umberto Michieli, *arXiv*, 2018.
* `\cite{newman2018}`: Mark Newman, *Networks*, 2nd edition, 2018.
* `\cite{freeman1978}`: Linton Freeman, *Social Networks*, 1978.

---

## 5. Style and Collaboration Rules
* **No AI stylistic markers**: Do not use em-dashes, en-dashes, or double hyphens to separate clauses. Use standard human punctuation such as commas, colons, parentheses, or periods.
* **Word ceiling**: Keep Section 1 around 450 words and Section 2 around 500 words. Total word count for Role A should not exceed 950-1,000 words.
* **File encoding**: Ensure your LaTeX text is saved in pure UTF-8 encoding without BOM.
* **Git workflow**: Work on the `main` branch. Pull before editing, make focused commits, and run the word count check:
  ```powershell
  .venv\Scripts\python -m tennis_networks.wordcount
  ```
