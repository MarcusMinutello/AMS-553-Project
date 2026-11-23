# Speaker script

Slide numbers match the numbers in the bottom-right corner of the slides. The section divider pages ("1. The problem" and so on) have no number; pause on them for a second and move on.

Each slide has its main ideas, a target time, and an example of what to say. The examples run at about 130 words per minute, so reading them all straight through takes about 15 minutes. Use them for rehearsal; on the day, speak from the main ideas.

Suggested split (change it freely): **Marcus** slides 1–5 and 10–12, **Benjamin** slides 6, 8 and 9, **Alex** slides 7 and 13–15, **Marcus** closes with 16–17. Hand-offs are marked **(hand-off)**.

---

## Slide 1: Title (15 s), Marcus

**Main ideas**
- Who we are, and that this is a progress report.

**What to say**
> We're Benjamin, Alex and Marcus. Our project simulates huge Daily Fantasy Sports contests, the kind with hundreds of thousands of entries, and asks whether a lineup built for its best-case upside beats a lineup built for expected points. This is a progress report: we'll show the problem, our approach, our first results, and our plan for the final report.

## Slide 2: Roadmap (15 s), Marcus

**Main ideas**
- Four parts: the problem, our approach, early results, what's next.

**What to say**
> We'll start with why this problem is interesting, then walk through our three-stage simulation, then four early results, and finish with what we still have to do.

---

## Slide 3: Large-field DFS (60 s), Marcus

**Main ideas**
- Format: 9 players, $50,000 cap.
- Payouts are extremely top-heavy: the top 10 of 10,001 entries take 26% of the pool.
- The rake means the average player loses 15%.

**What to say**
> In a large-field DFS contest you draft nine real NFL players under a fifty-thousand-dollar salary cap, and you score their real fantasy points. Our simulated contest has about ten thousand entries; real ones have a hundred thousand or more. The key thing is the payout structure. Only the top twenty percent get paid at all, and most of them barely get their money back. The top ten entries, the top tenth of a percent, take about a quarter of the prize pool. And the house keeps fifteen percent, so an average player loses fifteen percent of every entry. To make money you need skill just to break even.

## Slide 4: Points vs. payout (60 s), Marcus

**Main ideas**
- You need a boom, not a good average.
- Stacking correlated players creates the variance you need.
- The winning score depends on what everyone else drafted.
- State the question.

**What to say**
> That payout structure is why maximizing expected points is the wrong goal. First, even the best-projected lineup usually finishes far from the top tenth of a percent, so what matters is your best case. Second, correlation is a lever: if you pair a quarterback with his own receivers, they boom together, which raises your variance. Third, the bar you have to clear is set by the field. If a player everyone owns has a huge game, the winning score goes up with him and you gain nothing. If a player nobody owns booms, only you benefit. So our question is: can a lineup chosen for its upper tail, using a measure called Upside CVaR, beat lineups chosen for expected points, by a statistically significant margin?

## Slide 5: Building on Haugh & Singal (60 s), Marcus

**Main ideas**
- Their key idea: model the opponents.
- We reuse their opponent model: Dirichlet-multinomial ownership, stacking, acceptance-rejection.
- In their 2017 NFL experiments, modeling opponents was worth about 4× in expected P&L.

**What to say**
> We're building on a 2019 paper by Haugh and Singal. Their main idea is that you have to model your opponents, not just the players. They model each position's ownership as Dirichlet-multinomial, add a probability that an opponent stacks a quarterback with a receiver, and generate full opponent lineups by acceptance-rejection, keeping only lineups that are legal and spend most of the cap. They then choose lineups by mean-variance optimization. Over the 2017 NFL season, modeling opponents roughly quadrupled their expected profit in top-heavy contests. We reuse their opponent model almost exactly. What we change is the objective: Upside CVaR instead of mean-variance. **(hand-off)**

---

## Slide 6: The pipeline (60 s), Benjamin

**Main ideas**
- Three stages: player outcomes, opponent field, contests.
- Selection sits in the middle: candidate lineups from a MILP, chosen by Upside CVaR.
- Separate random seeds for generation, selection and testing.

**What to say**
> Here's the whole pipeline. Stage one simulates how many points every player scores, with realistic correlations. Stage two simulates ten thousand opponent lineups. Stage three runs the contest: rank everyone, pay out, split ties. In the middle is lineup selection. We generate about three hundred twenty candidate lineups by solving a mixed-integer program, then pick the one with the highest Upside CVaR on five thousand simulated scenarios. The important design choice is the seeds: generating candidates, selecting one, and testing it all use different random numbers. We never grade a lineup on the same scenarios that picked it. **(hand-off)**

## Slide 7: Stage 1, player outcomes (60 s), Alex

**Main ideas**
- Synthetic slate: 8 teams, 80 players.
- Position-pair correlations; matrix repaired to be positive definite.
- Lognormal marginals give a long right tail.

**What to say**
> For inputs, we built a synthetic slate so we could get the whole pipeline working first: eight teams, four games, eighty players, with DraftKings-style salaries. Correlations are set by position pair. For example, a quarterback and his top receiver are correlated at about 0.45, and a defense against the opposing quarterback at about minus 0.35. The heatmap shows one game. Points are a Gaussian copula with lognormal marginals, matched to each player's projected mean and standard deviation. Lognormal matters because points can't be negative and the upside is long: this receiver averages about fifteen points, but his 99th percentile is over forty. That tail is what wins tournaments. **(hand-off)**

## Slide 8: Stage 2, the opponents (75 s), Benjamin

**Main ideas**
- 80% minnows from the paper's Algorithm 1; 20% optimizer-built sharks.
- 10% acceptance rate; 32% stack rate (target 35%).
- Without sharks the field was too weak.

**What to say**
> For opponents, eighty percent are what the DFS world calls minnows, generated by the paper's Algorithm 1. Each contest, we draw positional ownership from a Dirichlet, so popularity varies week to week, then draw each opponent's players, stack the quarterback with his top receiver thirty-five percent of the time, and accept the lineup only if it's legal and spends at least forty-nine thousand dollars. About ten percent of candidates pass. The other twenty percent are sharks: lineups built by an optimizer on noisy projections. We added them because with minnows alone the field was unrealistically weak. The chart shows the result: a realistic amount of chalk, with the most popular quarterback in 37 percent of lineups.

## Slide 9: The objective (75 s), Benjamin

**Main ideas**
- Upside CVaR: the average of your best (1 − α) share of simulated weeks.
- S1 uses points alone; S2 uses points minus the winning score in the same contest.
- Field-aware picks are much less owned.

**What to say**
> Upside CVaR is the mirror image of the usual CVaR from risk management: instead of averaging your worst outcomes, you average your best ones, the top one percent of simulated weeks when α is 0.99. We tried it two ways. S1 uses your score alone. S2 is field-aware: it uses your score minus the score needed for the top tenth of a percent in the same simulated contest. That's the key difference. When a popular player booms, the winning score rises with him, so a lineup full of popular players gets no credit. The chart shows every candidate lineup: the field-aware picks, at the top, are much less owned than the max-projection lineups on the right. **(hand-off)**

---

## Slide 10: Result 1, validation (60 s), Marcus

**Main ideas**
- A lineup drawn from the field must lose exactly the 15% rake.
- Simulated: −15.9%, CI −19.0% to −12.8%. Cash rate and top-0.1% rate also match.
- The winning line varies a lot, so it has to be simulated.

**What to say**
> Before comparing strategies, we checked the simulator. A lineup drawn from the field is interchangeable with every opponent, so its expected return has to be exactly minus fifteen percent, the rake. We held out two hundred field lineups per contest, four hundred thousand entries in total, and got minus 15.9 percent, with a confidence interval that contains minus fifteen. The cash rate and the top-tenth-of-a-percent rate match their theoretical values too. The chart shows the score needed to win across two thousand contests: it moves by about twenty points from contest to contest, which is why it has to be simulated rather than treated as a fixed target. All of our confidence intervals are clustered by simulated field.

## Slide 11: Result 2, strategy comparison (90 s), Marcus

**Main ideas**
- Points-only Upside CVaR picked the same stack as benchmark B2: no edge.
- Field-aware with α chosen by validation (S2-CV) reaches the top 1% and top 0.1% more often (p = 0.04 and 0.052), but cashes less.
- Its lineup is a game stack.

**What to say**
> Here are two thousand out-of-sample contests, with every strategy entered in the same contests, so all comparisons are paired. Grey is a typical field lineup. The first finding: points-only Upside CVaR, in green, picked exactly the same lineup as the stacked benchmark. Upside on points alone just rediscovers the obvious stack. The second finding is the bottom row, the field-aware version with α chosen by validation. It cashes less often, but it reaches the top one percent and the top tenth of a percent more often than max projection, with p-values of 0.04 and 0.052, and five times as often as a typical field lineup. That's the trade a top-heavy payout rewards. And the lineup it chose is a game stack: one team's quarterback, running back and top receiver, plus the opposing team's top receiver. That's a well-known pro strategy, and the method found it on its own.

## Slide 12: Result 3, over-fitting (75 s), Marcus

**Main ideas**
- At α = 0.99 the field-aware pick looked like +150% and returned −16%.
- The tail is only 50 scenarios; choosing α by validation fixed it.
- The payout gain over max projection is not yet significant.

**What to say**
> There's a catch, and it's the optimizer's curse. Each grey dot is one candidate lineup: the horizontal axis is the return we estimated during selection, the vertical axis is what it actually returned on new contests. At α of 0.99, the field-aware pick, in orange, looked like the best lineup in the pool and then lost sixteen percent. The top one percent of five thousand scenarios is only fifty scenarios, so we were fitting noise. The fix was to choose α by validation: pick on half the selection data, check on the other half, never touching the test set. That chose 0.975, and that lineup held up. To be clear about the limits: its payout advantage over max projection is ninety-five points of ROI, but with a p-value of 0.15 it's not significant yet. **(hand-off)**

## Slide 13: Result 4, importance sampling (60 s), Alex

**Main ideas**
- Shift the latent normal's mean toward our lineup's players; reweight by the likelihood ratio.
- 8× fewer samples for the same accuracy.
- 6× to 21× variance reduction as the event gets rarer.

**What to say**
> The over-fitting problem is really an estimation problem in the tail, and that's where importance sampling comes in. To estimate the probability that our lineup clears a winning-level score, we shift the mean of the correlated normals toward our lineup's players, so booms happen more often, and reweight each draw by the likelihood ratio so the estimate stays unbiased. With 250 draws, importance sampling is as accurate as crude Monte Carlo with two thousand, eight times fewer samples. And the rarer the event, the bigger the gain: from six times less variance up to twenty-one times. That's exactly the regime where our α of 0.99 broke down.

---

## Slide 14: Limitations (30 s), Alex

**Main ideas**
- Synthetic slate; smaller field; single entry; noisy tail.

**What to say**
> To be upfront about what these results don't show yet: the slate is synthetic, the field is ten times smaller than a real one, we only enter one lineup when pros enter up to a hundred fifty, and payout estimates in the tail are still noisy. Two first-place finishes account for a third of our best strategy's winnings.

## Slide 15: Plan (60 s), Alex

**Main ideas**
- Real data, better opponent model, multi-entry, IS inside selection, sensitivity, report.
- Goal: test whether the payout edge becomes significant.

**What to say**
> Here's our plan for the final report. First, real inputs: a historical DraftKings slate with fitted distributions and correlations. Second, a Dirichlet regression for ownership, as in the paper. Third, multi-entry portfolios, compared with the paper's mean-variance method. Fourth, and most important, importance sampling inside the Upside-CVaR selection itself, plus more test contests, so we have the power to detect a payout difference. Then sensitivity analysis and the report. The goal is to find out whether the field-aware edge in expected payout is statistically significant. **(hand-off)**

## Slide 16: Summary (45 s), Marcus

**Main ideas**
- The simulator works and reproduces the rake.
- Points-only upside gives no edge; field-aware upside reaches the top more often.
- The far tail over-fits; validation and importance sampling address it.

**What to say**
> To sum up: we have a working simulation of a ten-thousand-entry contest that reproduces the house edge. Upside measured on points alone just finds the obvious stack. Upside measured against the simulated field finds a low-owned game stack that reaches the top of the contest more often than max projection. Selecting on the far tail over-fits, but validating α fixes that, and importance sampling is how we'll estimate the tail properly for the final report.

## Slide 17: Questions

**Likely questions**
- *Why synthetic data?* So we could build and validate the full pipeline in the time we had; real data is the first item in our plan.
- *Why does max projection do so well?* Eighty percent of our field doesn't optimize, which matches the paper's estimate of how many players are casual.
- *Isn't picking α = 0.975 cherry-picking?* No: α was chosen using only the selection data, before we looked at the test contests. The α = 0.99 result is shown alongside it.
- *Why Upside CVaR instead of maximizing expected payout directly?* We tried that too (S3); it chose the same lineup as α = 0.99 and over-fit the same way.
