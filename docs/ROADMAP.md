# Project Roadmap: Large-Field DFS Simulation with U-CVaR

**Team:** Benjamin Minkin, Marcus Minutello, Alex Dolce
**Build day:** Monday, Nov 23 · **Presentation:** Tuesday, Nov 24 (10–20 min) · **Final report:** Wednesday, Dec 9, 5:00 PM

---

## 0. Status (Sunday, Nov 22)

The pipeline is built and runs end to end (`python run_all.py`, about 2 minutes). Figures come from `python make_figures.py`. Headline results so far:

| Result | Finding |
|---|---|
| Validation | A typical field lineup returns −15.9% (95% CI −19.0% to −12.8%), matching the −15% rake |
| Points-only U-CVaR (S1) | Picks the same QB–WR stack as the max-projection-plus-stack benchmark. No edge |
| Field-aware U-CVaR, α = 0.99 (S2) | Over-fits the far tail: estimated +150% ROI, realized −16% |
| Field-aware U-CVaR, α chosen by validation (S2-CV, α = 0.975) | +146% ROI vs +51% for max projection. Top-1% rate +0.95 pts (p = 0.04), top-0.1% rate +0.35 pts (p = 0.052). Payout difference not yet significant (p = 0.15) |
| Importance sampling | 6× variance reduction at p ≈ 3.5%, rising to 21× at p ≈ 0.17% |

Changes from the original plan: the field is 80% Algorithm-1 "minnows" plus 20% optimizer-built "sharks" (without sharks the field was too weak). Ownership uses projection and salary as features, as in the paper's Dirichlet regression. We added S2-CV and an all-candidate out-of-sample evaluation to diagnose over-fitting.

## 1. Goal for Tuesday

We won't have a finished project by Tuesday, and that's fine. The presentation needs four things:

1. **The problem:** why winning a top-heavy DFS contest is not the same as maximizing expected points.
2. **The idea:** a three-stage simulation pipeline (player outcomes, then the opponent field, then contests) and a lineup chosen by **Upside CVaR (U-CVaR)**.
3. **A couple of results:** a working end-to-end simulation on one synthetic slate, with at least one strategy comparison and one variance-reduction (importance sampling) result.
4. **Next steps:** what we'll do between Nov 25 and Dec 9.

The course rubric asks the talk to cover *objectives*, *main techniques and tools (input/output analysis, variance reduction)*, and *expected outcomes/insights*. Every part of this plan maps to one of those.

### Definition of done for Monday night

- [ ] One synthetic slate (about 80 players, 8 NFL teams) with salaries, projections, SDs, and a correlation matrix
- [ ] A correlated player-outcome sampler
- [ ] An opponent field generator (Dirichlet-multinomial ownership, stacking, accept/reject on salary)
- [ ] At least 2 lineup strategies: a **max-projection benchmark** and a **U-CVaR lineup**
- [ ] An out-of-sample contest simulator reporting ROI, P(top 0.1%), and P(cash) with 95% CIs
- [ ] 1 importance-sampling vs. crude Monte Carlo comparison
- [ ] Slides, rehearsed once start to finish

---

## 2. What we're building on (Haugh & Singal, 2019)

What we take from the paper, and where we differ:

| Paper | Us |
|---|---|
| Players' points δ ~ MVN(μ, Σ), μ from FantasyPros, correlations from RotoViz position-pair averages | Same structure, but **synthetic** μ, σ, and position-pair correlations. Lognormal marginals to get right skew |
| Opponents: Dirichlet-multinomial per position, a stacking copula with prob. q (0.35 for top-heavy), accept/reject requiring salary ≥ 0.99·B (Alg. 1) | **Same algorithm.** Ownership comes from a simple value model instead of a fitted Dirichlet regression |
| Objective: maximize expected payout via a mean-variance BQP over a λ grid (Alg. 4/7), solved with Gurobi | **U-CVaR**: maximize the mean of the top (1−α) tail of lineup score, chosen from a scenario-generated candidate pool. No Gurobi needed |
| Monte Carlo for order statistics of the field, with splitting (50 δ draws per field draw) | Same splitting idea for speed. **Importance sampling** for tail events (from our proposal) |
| Real 2017 FanDuel contests, about 200k opponents | Simulated DraftKings-style contest, **O = 10,000** opponents (scaled down) |

Key results from the paper to cite in the talk:
- In top-heavy contests you are almost always "out of the money" in expectation (Assumption 5.1), so **variance is good**. That's the justification for an upside-tail objective like U-CVaR.
- Modeling opponents was worth about 4× expected P&L over the benchmark in top-heavy contests (§7.1: roughly $1,400 vs $6,000 over the season).
- Diversifying across multiple entries beats replicating one lineup in top-heavy contests (§5.1–5.2). That's our multi-entry next step.

---

## 3. Scope decisions (made, don't revisit Monday)

| Decision | Choice | Why |
|---|---|---|
| Data | **Synthetic slate** | Scraping or cleaning real DFS data takes more than a day. Real data moves to next steps |
| Contest format | DraftKings NFL: QB, 2 RB, 3 WR, TE, FLEX (RB/WR/TE), DST; $50,000 cap; 9 players | Matches the Millionaire Maker framing in our proposal |
| Language/stack | Python: `numpy`, `scipy` (`scipy.optimize.milp`, HiGHS solver), `pandas`, `matplotlib` | Nothing extra to install. No license problems |
| Player outcomes | Gaussian copula with **lognormal** marginals: Z ~ MVN(0, R), points = exp(m + s·Z) | Non-negative and right-skewed (upside matters), and only one line more than MVN |
| Field size | O = 10,000 opponents + our entry | Fast. Top 0.1% = top 10 entries |
| Optimizer | Candidate pool + exact U-CVaR selection (see §5.3) | Maximizing a tail *mean* directly is non-concave. The pool approach is simple, exact on the pool, and defensible |
| Seeds | Fixed RNG seeds per stage; **separate scenario sets** for candidate generation, selection, and testing | Avoids the optimizer's curse and makes results reproducible |

### Default parameters (use these unless something breaks)

| Parameter | Value |
|---|---|
| Teams / games | 8 teams / 4 games |
| Players per team | 1 QB, 2 RB, 4 WR, 2 TE, 1 DST (10 per team, 80 total) |
| Salary cap B | $50,000 |
| Opponent salary floor B_lb | 0.98·B ($49,000). Drop to 0.97 if acceptance is too slow |
| Stacking probability q | 0.35 (paper's top-heavy estimate) |
| Dirichlet concentration κ | 200 (higher means ownership is more predictable) |
| Entry fee / rake | $1 / 15% → prize pool = $8,500.85 for 10,001 entries |
| Payouts | Top 20% cash. Power-law decay, 1st ≈ 10% of pool, min cash = $2 |
| U-CVaR level α | 0.99 (top 1% of scenarios); also report 0.999 with IS |
| Scenarios | 5,000 selection, 300 candidate-generation |
| Test contests | 2,000 (e.g., 200 fields × 10 δ draws each, "splitting") |

---

## 4. Code layout

```
src/
  slate.py       # build synthetic slate -> data/slate.csv; correlation matrix R
  outcomes.py    # sample_outcomes(slate, R, n, rng, shift=None) -> (points[n,P], weights[n])
  field.py       # generate_field(slate, O, rng, q, kappa, b_lb) -> lineups[O,9] (player indices)
  optimize.py    # max_projection(), max_projection_stacked(), candidate_pool(), select_ucvar()
  contest.py     # payout_table(O), simulate_contests(strategies, slate, n_fields, n_draws, rng)
  analysis.py    # summary stats, CIs, paired tests, plots -> results/
  is_demo.py     # importance sampling vs crude MC for P(lineup score > top-0.1% cutoff)
run_all.py       # one command reproduces every number and figure in the slides
results/         # CSVs and PNGs (gitignored if large)
```

### Shared contracts (agree on these at 9:00 AM so everyone can work in parallel)

- **`data/slate.csv`** columns: `pid, name, team, opp, pos, salary, proj, sd`. `pid` is 0..P−1 and indexes every array.
- **Lineup** = sorted `np.ndarray` of 9 `pid`s. A field is an `int` array of shape `[O, 9]`.
- **Score** of lineups under outcomes `D[n, P]`: `D[:, lineups].sum(axis=-1)`.
- **Weights** returned by `sample_outcomes` are all ones for crude MC and the likelihood ratio for IS.
- Anyone can test their piece on a 2-team toy slate before the real one exists.

---

## 5. Technical plan by component

### 5.1 Inputs: slate and player outcomes (Alex)
1. **Slate:** projections by role tier (e.g., QB 14–24, RB1 12–18, WR1 12–17, TE1 8–12, DST 5–9). Salary ≈ linear in projection plus noise, so mispriced "value" players exist. Set SD as a fraction of the mean by position (QB ~0.35, RB ~0.5, WR ~0.6, TE ~0.6, DST ~0.7).
2. **Correlations by position pair** (cite the paper's RotoViz-style averages):
   - Same team: QB–WR1 +0.45, QB–WR2 +0.35, QB–TE +0.30, QB–RB +0.10, RB–DST +0.15, WR–WR −0.05
   - Opposing: QB–QB +0.20 (shootouts), DST vs. opposing offense −0.30, QB vs. opposing WR1 +0.15
   - **Check positive semidefiniteness.** If it fails, clip negative eigenvalues and rescale to a unit diagonal.
3. **Sampler:** Z = L·ε (Cholesky of R), then points = exp(m + s·Z), with (m, s) chosen so each player's mean and SD equal `proj` and `sd`.
4. **IS hook:** an optional mean shift θ in Z-space. Weight = φ(Z; 0, R) / φ(Z; θ, R) = exp(−θᵀR⁻¹Z + ½θᵀR⁻¹θ).
5. **Input-analysis visuals for slides:** a correlation heatmap and one player's marginal distribution showing the right skew.

### 5.2 Opponent field (Benjamin)
Implement the paper's Algorithm 1:
1. Ownership "truth" per position: pᵖᵒˢ ∝ exp(β₁·value + β₂·proj), where value = proj / (salary/1000). Then draw p ~ Dirichlet(κ·pᵖᵒˢ) **once per field**, so ownership uncertainty varies across contests.
2. For each opponent: stack ~ Bernoulli(q). Sample QB, RBs, WRs, TE, FLEX, and DST from the multinomials without replacement. If stacking, replace WR #1 with the QB's team WR1.
3. **Accept** only if the lineup is legal (positions, cap, no duplicates) and salary ≥ B_lb.
4. **Vectorize:** draw batches of ~50k candidates with numpy and filter with array ops. A per-opponent Python loop will be too slow.
5. Log the acceptance rate, stack rate, and ownership. These are output-analysis checks for the slides.

### 5.3 Lineup strategies (Benjamin, Marcus reviews)
All lineups come from a single MILP template (`scipy.optimize.milp`): binary xᵢ, position counts, cap, and an objective vector c.

| Strategy | How |
|---|---|
| **B1: Max projection** | c = μ |
| **B2: Max projection + QB–WR stack** | c = μ, plus a constraint requiring the QB's team WR1 (paper's Benchmark 2) |
| **S1: U-CVaR** | (a) **Candidate pool:** solve the MILP with c = δ_s for ~300 generation scenarios, plus c = μ + λσ for λ ∈ {0, 0.25, …, 1.5}. Dedupe to roughly 200–400 lineups. (b) **Select:** score every candidate on 5,000 *separate* selection scenarios and pick the one with the largest U-CVaR_α = weighted mean of its top (1−α) scores |
| **S2 (stretch): Strategic U-CVaR** | Same as S1, but rank candidates by the U-CVaR of *(score − field top-0.1% cutoff)* in each scenario, which uses simulated fields. This is the "model the opponents" step the paper found most valuable |
| **Sanity baseline: random field lineup** | Our entry is just another draw from the field. **Its ROI should come out at about −15% (the rake).** That validates the whole contest simulator |

### 5.4 Out-of-sample contest simulation (Marcus)
1. Fresh seeds, **unweighted** outcomes (proposal step 3).
2. For each of 200 fields: generate O = 10,000 opponents, then draw 10 outcome vectors (splitting). Score field and our lineups with one matrix multiply, then rank and pay.
3. **Common random numbers:** every strategy plays the *same* 2,000 contests, so comparisons are paired.
4. Report per strategy: mean payout/ROI ± 95% CI, P(cash), P(top 1%), P(top 0.1%), mean percentile rank.
5. Significance: a paired t-test on payout differences (S1 − B1) plus a bootstrap CI. Payouts are extremely heavy-tailed, so also compare **P(top 0.1%)**, a binomial proportion with tighter CIs. Be honest in the talk if the ROI difference is not yet significant; that's a next-step story about sample size and variance reduction.

### 5.5 Importance sampling demo (Alex, Marcus helps with plots)
A clean, self-contained variance-reduction result:
- Target: p = P(score of our S1 lineup > c), where c is the simulated top-0.1% field cutoff (a rare event, p ≈ 10⁻³).
- **Crude MC** vs. **IS with a mean shift** in Z-space along the lineup's direction. Pick θ so the tilted mean score ≈ c (exponential-tilting heuristic).
- Show: estimate ± CI vs. n for both methods, the variance ratio, and the relative error. This hits the course's "variance reduction" bullet directly.

---

## 6. Monday schedule

| Time | Alex | Benjamin | Marcus |
|---|---|---|---|
| **9:00–9:30** | *All: kickoff. Confirm contracts (§4), create repo scaffold, `requirements.txt`, seeds* | | |
| **9:30–12:30** | `slate.py` + `outcomes.py`, PSD check, heatmap | `field.py` (vectorized Alg. 1) | `contest.py`: payout table, ranking, scoring on toy data; `analysis.py` skeleton |
| **12:30–1:00** | *All: **Integration check 1**: generate one field on the real slate, plot the field score histogram, check acceptance and stack rates* | | |
| **1:00–4:00** | `is_demo.py` | `optimize.py`: B1, B2, candidate pool, U-CVaR selection | Wire `run_all.py` end to end with small n; random-lineup sanity check (≈ −15% ROI) |
| **4:00** | *All: **FEATURE FREEZE.** Launch the full run (2,000 contests) in the background. Only bug fixes after this* | | |
| **4:00–6:30** | IS figures + slide content for inputs/IS | Slides: problem, method, field model | Results table, CIs, paired tests, figures |
| **6:30–8:30** | *All: assemble the deck, do a timed run-through, cut to 15 min* | | |
| **8:30–9:00** | *All: commit code + results, write down open issues for next steps* | | |

### Cut lines (if we fall behind)
- **At 1:00 PM, field generator not working:** use a simpler field. Each opponent = max-projection MILP on noise-perturbed projections. Mention the Dirichlet model as a next step.
- **At 4:00 PM, U-CVaR selection not working:** present B1 vs. B2 vs. random-field results, and show U-CVaR scores of a small hand-built pool.
- **At 4:00 PM, full run too slow:** cut to 500 contests (50 fields × 10 draws) and say so on the slide.
- **IS demo is the first thing dropped** from the main pipeline. Keep it standalone; it doesn't depend on anything but the sampler.
- **S2 (strategic U-CVaR) is a stretch goal.** Only attempt it if S1 results are in by 3:00 PM.

---

## 7. Presentation outline (target 15 minutes)

| # | Slide | Content | Who |
|---|---|---|---|
| 1 | Title | Team, course | — |
| 2 | What is large-field DFS? | Draft 9 players under a cap; 100k+ entries; top-heavy payouts (top 0.1% takes a big share) | Marcus |
| 3 | The problem | Max expected points ≠ max expected payout. We're "out of the money" on average, so upside variance and differentiation from the field matter | Marcus |
| 4 | Prior work | Haugh & Singal (2019): model opponents, mean-variance BQP, ~4× value from modeling opponents | Benjamin |
| 5 | Our pipeline | Diagram: player outcomes (IS), then field (accept/reject), then out-of-sample contests | Benjamin |
| 6 | Input analysis | Slate, lognormal marginals, correlation heatmap | Alex |
| 7 | Field model | Dirichlet-multinomial + stacking + salary floor; acceptance rate, ownership plot | Benjamin |
| 8 | Objective: U-CVaR | Definition (mean of top (1−α) tail), candidate pool + selection, why it targets "ship-it" scenarios | Benjamin |
| 9 | Result 1: validation | Random field lineup ROI ≈ −15%; field score distribution and top-0.1% cutoff | Marcus |
| 10 | Result 2: strategy comparison | Table: ROI, P(cash), P(top 0.1%) ± CI for B1, B2, S1 (S2); paired test | Marcus |
| 11 | Result 3: importance sampling | Crude MC vs. IS: CI width vs. n, variance ratio | Alex |
| 12 | Limitations | Synthetic data, scaled-down field, single entry, heavy-tailed payouts need many reps | Marcus |
| 13 | Next steps | §8 below, condensed | All |
| 14 | Questions | — | — |

---

## 8. Plan for the rest of the project (Nov 25 – Dec 9)

Thanksgiving is Thu Nov 26, so plan light that week.

| Phase | Dates | Work | Owner |
|---|---|---|---|
| **1. Real inputs** | Nov 25 – Nov 30 | Calibrate to one or more historical DraftKings slates (salaries, projections, realized ownership). Fit marginals and check goodness-of-fit. Estimate position-pair correlations from historical box scores | Alex |
| **2. Better opponents** | Nov 27 – Dec 2 | Fit ownership with a Dirichlet regression on features (projection, salary, value) as in the paper (§3.1.2). Calibrate q and B_lb to observed stacking and budget usage | Alex, Benjamin |
| **3. Better strategies** | Nov 28 – Dec 3 | Strategic U-CVaR (S2). **Multi-entry**: greedy diversification with ≤ 6 shared players between entries (paper's Alg. 7). Compare against the paper's mean-variance objective | Benjamin |
| **4. Better estimation** | Nov 30 – Dec 4 | Bring IS into U-CVaR selection at α = 0.999. Choose the tilt with the cross-entropy method. Use CRN and pick the number of replications for a target relative precision | Alex, Marcus |
| **5. Sensitivity analysis** | Dec 2 – Dec 5 | Vary q, κ, field size O, α, and the payout curve. Find when U-CVaR beats the benchmarks and when it doesn't | Marcus |
| **6. Report** | Dec 3 – Dec 9 | ≥ 4 pages (title, names, figures, tables; no code). **Open with a summary of problems and results.** Internal draft by Dec 7, final PDF emailed by **Dec 9, 5:00 PM** (no extensions) | Marcus (lead), all |

### Questions the final report should answer
1. Does a U-CVaR lineup beat max-projection and stacked benchmarks by a statistically significant margin in P(top 0.1%) and expected payout?
2. How much does modeling the field (S2 vs. S1) add, and how does that compare with the paper's ~4×?
3. How much variance reduction does importance sampling buy for tail-probability and U-CVaR estimates?
4. How sensitive are the conclusions to opponent behavior (stacking rate, ownership predictability) and contest size?

---

## 9. Known risks

| Risk | Mitigation |
|---|---|
| Accept/reject is too slow (low acceptance at a 98% salary floor) | Vectorize. Lower the floor to 97%. Sample the highest-salary positions first |
| U-CVaR at α = 0.999 is too noisy with 5,000 scenarios (only 5 tail points) | Use α = 0.99 Monday. α = 0.999 with IS is a next step |
| Heavy-tailed payouts mean ROI CIs overlap everything | Lead with P(top 0.1%) and percentile rank. Present ROI with honest CIs |
| Optimizer's curse (a lineup looks great on the scenarios it was picked on) | Separate seeds for generation, selection, and test scenarios |
| Synthetic slate looks arbitrary | Show the parameter table openly. Frame it as a controlled experiment; real data is Phase 1 |
