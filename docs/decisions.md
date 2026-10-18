# Design Decisions and Pipeline Strategy

This document records the architectural and procedural choices made during the development of the
tennis network analysis pipeline, providing a shared rationale for all team members and ensuring
transparency for the course evaluation.

---

## 1. Upfront Pipeline Construction (Code-First Approach)

### Context
In network analysis research projects, drafting the narrative sections (Introduction, Problem and
Motivation, Interpretation, Critique) before executing the empirical tests often leads to wasted effort:
theoretical conjectures might be invalidated by the data, requiring major rewrites close to the deadline.

### Decision
The data extraction, graph modeling, topological metrics and statistical hypothesis testing (H1 to H8)
were fully implemented and executed upfront.

### Rationale and Benefits
* **Empirical Grounding for Narrative**: Team members responsible for the Introduction (Role A) and
  Interpretation/Critique (Role C) now work with definitive, reproducible numbers rather than speculative
  assumptions. For instance, the rejection of H2 (networks are significantly more assortative than the
  null model due to tournament seeding) directly informs the problem formulation and critical discussion.
* **De-Risking the Deadline**: Complex statistical procedures (such as degree-preserving null models,
  season permutations and QAP tests) carry performance bottlenecks and numerical edge cases. Resolving
  these challenges early guarantees a predictable timeline towards the 27 November deadline.
* **Word Count Economy**: The course imposes a strict 5,000-word ceiling. Knowing the exact complexity of
  the results allows the team to allocate word budgets precisely across sections without unnecessary padding.

---

## 2. Fast Null Models and Result Freezing

### Context
Standard NetworkX functions for degree-preserving randomisation (`double_edge_swap`) can be prohibitively
slow on dense or medium-sized networks, taking several minutes per null sample across 13 networks.

### Decision
* We implemented an optimised degree-preserving edge swap in `tennis_networks.nullmodels` that runs
  ten to twenty times faster than the standard library implementation.
* The seed (`20261115`) is centrally pinned in `config/networks.json`.
* All generated summary tables and test statistics are committed to `results/tables/`.

### Rationale and Benefits
* Report generation (`make report-assets`) and PDF builds in CI take seconds instead of hours because
  they read the frozen results instead of re-running Monte Carlo simulations on every push.
* Full reproducibility is maintained: any collaborator or reviewer can re-run `make all` to regenerate
  every CSV from the raw data.

---

## 3. Multi-Level Hypothesis Structure (Course Slide L04)

### Context
The evaluation criteria and course syllabus (specifically slide L04) emphasise multi-level network analysis
distinguishing between network-level, monadic, dyadic and mixed phenomena.

### Decision
Hypotheses were structured into four explicit tiers:
1. **Network-level (H1 to H5)**: Global prestige concentration, degree assortativity, surface centralization,
   tour disparity and triad hierarchy rigidity.
2. **Monadic-level (H6)**: Player-level permutation regression testing whether PageRank predicts official
   ranking beyond nominal victory counts.
3. **Dyadic-level (H7)**: Quadratic Assignment Procedure (QAP) correlation verifying whether head-to-head
   dominance transfers across clay, hard and grass surfaces.
4. **Mixed-level (H8)**: QAP correlation testing whether homophily in surface specialisation profiles drives
   match frequencies.

### Rationale and Benefits
This mapping ensures direct alignment with the grading rubric, demonstrating methodical coverage of the
analytical tools taught in the lectures.

---

## 4. Dual-Mode Executable Pipeline Notebook

### Context
During the oral exam and group presentations, running thousands of permutation iterations live is
impractical due to time constraints (typically 15-20 minutes).

### Decision
The notebook `notebooks/full_pipeline.ipynb` provides a `QUICK` switch:
* `QUICK = True`: Executes with reduced null-model iterations (5 to 10 samples) to verify pipeline mechanics
  in under two minutes.
* `QUICK = False`: Runs the full statistical suite producing the final publication-grade tables.

### Rationale and Benefits
Enables seamless live demonstrations during the exam presentation without risking presentation timeouts
or hanging kernels.

---

## 5. Collaborative Team Authoring and Section Ownership

### Context
The course examination assesses three distinct conceptual pillars:
1. Context, Problem, and Motivation (20%): Role A (Shivam Kumar)
2. Datasets, Measures, and Results (60%): Role B1 (Francesco Castaldi), Role B2 (Jacopo Bonifazi), Role B3 (Gaetano Muscarello)
3. Interpretation and Critique (20%): Role C (Paolo Fusco)

### Decision
* **Role B1 (Francesco Castaldi)** implemented the data pipeline, reproducibility harness, automated LaTeX table/figure exports, and the draft for Sections 3 (*Datasets*) and 4 (*Validity and Reliability*).
* The preliminary narrative in Section 5 (*Measures and Results*) serves as an initial technical working scaffold assembled from pipeline outputs, providing clear empirical anchors so that Roles B2 and B3 do not start from a blank page.
* **Roles B2 (Jacopo Bonifazi) and B3 (Gaetano Muscarello)** hold full editorial ownership of Section 5. They are expected to revise, reorganize, expand or condense this technical text to reflect their own analysis and ensure a balanced word allocation across the 5,000-word group ceiling.
* Sections 1, 2, 6, and 7 remain reserved for Roles A and C, ensuring balanced contributions and authentic co-authoring across all five group members.
