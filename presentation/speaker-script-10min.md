# Speaker script: 10-minute deck (`slides_10min.pdf`)

Slide numbers match the bottom-right corner of the slides. Each slide lists a target time, a cumulative clock, who presents it, the main ideas, and an example of what to say. **[Brackets]** mark where to point on the slide. Hand-offs are marked **(hand-off)**.

The examples total about 1,600 words, roughly **11.5 minutes** at a normal speaking pace, which leaves a little room inside our 12 minutes. Rehearse with the examples. On the day, speak from the main ideas rather than reading.

**Split** (change it freely):

| Presenter | Slides | Time |
|---|---|---|
| Marcus | 1–3, then 11–12 | about 3:50 |
| Benjamin | 4–6 | about 3:25 |
| Alex | 7–10 | about 4:20 |

**If you're running long**, cut the "one technical note" on slide 7, the scatter-plot walkthrough on slide 9, and the "what we can't claim yet" sentence on slide 11. That saves about 45 seconds.

**Before presenting:** slide 2's real-contest figures (30% of the pool to first place, a $1 million prize) came from the group edit. Check them against a current Millionaire Maker payout table, or say "around" when you quote them.

---

## Slide 1: Title (0:20, clock 0:20), Marcus

**Main ideas**
- Who we are; this is a progress report.

**What to say**
> Hi, we're Marcus, Benjamin and Alex. Our project is about Daily Fantasy Sports contests with hundreds of thousands of entries, and whether you should build your lineup differently when only the very top finishers make real money. This is a progress report: the problem, our approach, our early results, and what we'll do before the final report.

---

## Slide 2: Large-field DFS (0:45, clock 1:05), Marcus

**Main ideas**
- The format: 9 players, $50,000 cap, salaries follow expected points.
- 100,000+ entries; payouts are extremely top-heavy.
- The 15% rake: the average entry loses money.

**What to say**
> Quick background. In DraftKings' NFL Millionaire Maker, you pick nine real NFL players (a quarterback, two running backs, three receivers, a tight end, a flex and a defense) under a fifty-thousand-dollar salary cap. Better players cost more. Your score is their real fantasy points that weekend. These contests draw over a hundred thousand entries every week, and the payouts are extremely top-heavy: first place alone takes around thirty percent of the prize pool, about a million dollars. And the house keeps fifteen percent, so the average entry loses fifteen cents on every dollar. The money is all at the very top.

---

## Slide 3: Points ≠ payout (1:05, clock 2:10), Marcus

**Main ideas**
- You need a boom, not a good average.
- Stacking correlated players creates useful variance.
- The field sets the bar: unpopular booms help you, popular ones help everyone.
- State the research question.

**What to say**
> That changes what a good lineup is. Most lineup tools maximize expected points, but three things make that the wrong target. **[left box]** First, you need a boom. A lineup with a great average still lands far below the winning score most weeks, so we want a high best case. **[middle box]** Second, correlation is a tool. A quarterback and his own receivers score together, so stacking them raises your variance, and in a top-heavy contest variance is what produces winning weeks. **[right box]** Third, the field sets the bar. If a player everyone drafted has a huge game, he lifts everyone and you gain nothing. If a player nobody drafted booms, he lifts only you.
>
> So our question is: can a lineup chosen for its upper-tail average, using a measure called Upside CVaR, beat the field and beat lineups built for expected points, by a statistically significant margin? Benjamin will explain how we set it up. **(hand-off)**

---

## Slide 4: Haugh & Singal, and what we change (1:15, clock 3:25), Benjamin

**Main ideas**
- Their key idea is to model the opponents, not just the players.
- Walk the table row by row: our three extensions are lognormal points, mean-CVaR candidates, and Upside CVaR with importance sampling. The opponent model is theirs, unchanged.
- Point out the note: today's results use the simpler version.

**What to say**
> We build on Haugh and Singal, 2019. Their key idea is that you have to model your opponents, not just the players. They model how often each player is drafted with a Dirichlet-multinomial distribution, let opponents stack a quarterback with his receiver, and generate opponent lineups by acceptance-rejection. Then they build candidate lineups with an integer program using mean-variance, and pick the best one by Monte Carlo. Over the 2017 season, modeling opponents roughly quadrupled their expected profit.
>
> **[table, right column]** We keep their opponent model exactly, and make three extensions. One: player points are lognormal instead of normal, because fantasy scores are skewed. Two: candidates come from mean-CVaR instead of mean-variance. Three: we pick the best candidate by Upside CVaR, estimated with importance sampling instead of plain Monte Carlo.
>
> **[blue note]** To be upfront: the results today come from a simpler version, with mean-plus-lambda-sigma candidates and plain Monte Carlo. The CVaR candidates and importance-sampled selection are what we're building now.

---

## Slide 5: The simulation pipeline (1:05, clock 4:30), Benjamin

**Main ideas**
- Three stages: player outcomes, opponent field, contests.
- Selection: 317 candidates, pick the highest Upside CVaR on 5,000 scenarios.
- Testing: 2,000 new contests, the same ones for every strategy (paired comparisons).
- Separate random numbers for each stage, so there's no grading on the training data.

**What to say**
> Here's the simulation. **[box 1]** Stage one generates player outcomes: eighty fictional players on eight teams, with correlations by position (a quarterback and his top receiver move together; a defense and the opposing quarterback move opposite) and lognormal points. **[box 2]** Stage two generates the opponents: ten thousand per contest, from the paper's algorithm. **[box 3]** Stage three runs the contest: rank everyone, pay out the top-heavy prize table, split ties.
>
> **[bottom box]** In between, we build 317 candidate lineups with an integer program and pick the one with the highest Upside CVaR on five thousand scenarios. Then we test that lineup on two thousand brand-new contests. Every strategy plays the same contests, so the comparisons are paired. **[footer]** The key design rule: generation, selection and testing each use their own random numbers, so we never grade a lineup on the scenarios that picked it.

---

## Slide 6: Why Upside CVaR (1:05, clock 5:35), Benjamin

**Main ideas**
- U-CVaR is the average of your best (1 − α) share of outcomes.
- Under normality, mean and variance determine the tail. Fantasy scores aren't normal.
- Field-aware version: score each scenario as our points minus the top-0.1% score in that same contest.

**What to say**
> Why Upside CVaR? **[formula]** It's the average of your best one-minus-alpha share of outcomes. With alpha equal to 0.99, it's the average of your best one percent of simulated weeks. The paper motivates mean-variance with a normal model, and under normality that's enough, because mean and variance pin down the whole tail. But fantasy scores are skewed. **[figure]** These two curves have the same mean and the same variance, but the orange one has a long right tail. Mean-variance can't tell them apart; Upside CVaR can.
>
> **[third bullet]** And we make it field-aware. Instead of our raw score, each scenario counts our points minus the top-zero-point-one-percent score in that same contest. So a lineup only gets credit for a boom if the boom beats the field. Alex will show what this gives us. **(hand-off)**

---

## Slide 7: Result 1, the simulator matches theory (0:55, clock 6:30), Alex

**Main ideas**
- A lineup drawn like the field's must return exactly −15% (the rake).
- We get −16.2%, CI −19.4% to −13.1%; the cash rate and top-0.1% rate also match.
- The winning line varies a lot (mean 148, SD 20), so it has to be simulated.

**What to say**
> First, we checked the simulator against something we know exactly. A lineup drawn from the same generator as the field is interchangeable with every opponent, so its expected return has to be exactly minus the rake: minus fifteen percent. **[left numbers]** We got minus 16.2, with a confidence interval of minus 19.4 to minus 13.1, which contains the theory. It cashes 20.0 percent of the time against a theoretical 20, and finishes in the top tenth of a percent exactly 0.10 percent of the time.
>
> **[histogram]** This chart is the score you need to reach the top 0.1 percent. It moves a lot from contest to contest (mean 148, standard deviation 20), which is why we simulate the winning line instead of assuming a fixed target. One technical note: all our confidence intervals are clustered by simulated field, because contests that share a field are correlated.

---

## Slide 8: Result 2, max projection is hard to beat (1:20, clock 7:50), Alex

**Main ideas**
- How to read it: rows are lineups, panels are finish ranges, dots are estimates, bars are 95% CIs, the dotted line is a typical entry.
- Max projection (blue): top 1% in 5.15% of contests, top 0.1% in 0.95%, ROI +355%.
- Our field-aware pick (bottom row): 5.05% and 0.70%, ROI +205%. Payout difference −1.51, p = 0.12, so no edge yet, and the difference isn't significant either way.
- Why: the paper's opponents rarely build near-optimal lineups, so max projection is already far ahead.
- Present this as a finding, not a failure.

**What to say**
> Here's the main comparison. Each row is a lineup, and each panel shows how often it finished in a range across the two thousand test contests: cashing, the top 1 percent, and the top 0.1 percent. Dots are estimates, bars are 95 percent intervals, and the dotted line is a typical field entry.
>
> **[blue row]** The max-projection lineup is very strong here. It reaches the top 0.1 percent in almost one percent of contests, nine and a half times a typical entry, for a return of plus 355 percent. **[bottom row]** Our field-aware pick does well too, but not better: 0.7 percent in the top 0.1 percent, plus 205 percent. The payout difference is minus 1.51 dollars per one-dollar entry, with a p-value of 0.12, so there's no edge yet in either direction.
>
> **[third bullet]** Why? The paper's opponents pick players by popularity, so they rarely build anything close to an optimal lineup. Their average lineup projects to 89 points against 103 for max projection, so the best-projected lineup is already far ahead and there's little to gain by being different. That's a useful finding in itself: in this field, our extensions have to beat a very strong baseline.

---

## Slide 9: Result 3, noisy tail estimates pick the wrong lineup (1:15, clock 9:05), Alex

**Main ideas**
- Our pick looked best during selection (+397%) but scored +205% on new contests. Max projection looked like +311% and scored +355%.
- This is the optimizer's curse: choosing the maximum of noisy estimates picks the luckiest one.
- Validating α didn't help: every α from 0.90 to 0.99 chose the same lineup.
- Upside: across all 317 candidates, field-aware U-CVaR is the best predictor of test payout (0.79 vs. 0.56 for projection).

**What to say**
> So why didn't our method pick the best lineup? **[table]** During selection, our pick looked like the best candidate, plus 397 percent. On new contests it scored 205. Meanwhile max projection looked like 311 and actually scored 355. **[scatter]** Each gray dot is a candidate; the diagonal is where the selection estimate equals the test result. Our pick, in orange, is far below the line.
>
> This is the optimizer's curse. When you choose the maximum of many noisy estimates, you tend to choose the one that got lucky. And it's not a tuning problem: every alpha we tried, from 0.9 to 0.99, picked the same lineup.
>
> **[last bullet]** The encouraging part: across all 317 candidates, field-aware Upside CVaR predicts test payout better than anything else we measured, a correlation of 0.79 against 0.56 for projection. The ranking works; the estimates at the very top are just too noisy to separate the best few. That's a variance problem, which leads to our last result.

---

## Slide 10: Result 4, importance sampling (0:50, clock 9:55), Alex

**Main ideas**
- Tail events are rare, so plain Monte Carlo wastes most draws.
- Shift sampling toward booms for our lineup's players; reweight by the likelihood ratio so the estimate stays unbiased.
- 6× to 21× variance reduction, bigger for rarer events; 500 IS draws beat 2,000 plain draws.

**What to say**
> Importance sampling is how we attack that noise. The events we care about, like scoring above the winning line, are rare, so plain Monte Carlo spends most of its draws on ordinary weeks. Instead, we shift the sampling toward big games for our lineup's players and reweight each draw by the likelihood ratio, so the estimate stays unbiased. **[chart]** The rarer the event, the bigger the gain: six times less variance at the winning line, up to twenty-one times for the rarest threshold. In practice, 500 importance-sampled draws are more accurate than two thousand plain ones. That's why it's going into the selection step next. Marcus will wrap up. **(hand-off)**

---

## Slide 11: Next steps (1:00, clock 10:55), Marcus

**Main ideas**
- Each extension gets tested: skewed vs. normal (row 1), mean-CVaR candidates (row 3), importance sampling in selection (row 4).
- Real data: a DraftKings slate and ownership fitted with Dirichlet regression, as in the paper.
- What we can't claim yet.
- The goal: do the extensions beat the paper's method and max projection, significantly?

**What to say**
> Here's our plan before the final report on December 9th, and it lines up with our three extensions. First, a real DraftKings slate, where we'll compare skewed player distributions against the normal ones the paper uses. Second, ownership fitted to real data with Dirichlet regression, as the paper does, and a larger field. Third, switch the candidates to mean-CVaR, and compare multi-entry portfolios against the paper's. Fourth, run selection with importance sampling and add test contests, to fix the noise we just saw. Then sensitivity analysis and the report.
>
> **[footer]** What we can't claim yet: the slate is synthetic, our field is ten thousand rather than a hundred thousand, we enter a single lineup, and the payout intervals are wide. The goal is to test whether our three extensions beat the paper's method and max projection, by a significant margin.

---

## Slide 12: Takeaways / Questions (0:40, clock 11:35), Marcus

**Main ideas**
- Read the three takeaways, then open for questions.

**What to say**
> To sum up: we built a three-stage contest simulator that reproduces the house's fifteen-percent edge for a typical entry. In the paper's opponent field, max projection is hard to beat: our field-aware pick has no edge yet, although field-aware Upside CVaR is the best predictor of test payout. And tail estimates are noisy enough to pick the wrong lineup, which is exactly what importance sampling and mean-CVaR candidates are for. Thank you, and we're happy to take questions.

---

## Likely questions

- **"So your method doesn't work?"** Not yet, and not in this field. These results use the simpler version (mean + λσ candidates, plain Monte Carlo). Result 3 shows the selection step is limited by noise, which is what importance sampling fixes. Whether the full method beats max projection is what the final report will test.
- **"Why does max projection make +355%? Real players don't earn that."** Right. Our opponents follow the paper's algorithm with made-up ownership parameters, so they're weaker than a real field. The paper fits those parameters to real ownership data, and that's on our plan.
- **"What if some opponents use optimizers too?"** We tried it: we replaced 20% of the field with optimizer-built lineups. Max projection's ROI fell to +51%, and our field-aware pick reached the top 0.1% more than three times as often (0.50% vs. 0.15%). So the answer depends heavily on how strong the field is, which is why fitting ownership to real data matters. (Only bring this up if asked.)
- **"If field-aware U-CVaR predicts payout best, why did it pick a worse lineup?"** The correlation measures how well it ranks all 317 candidates. At the very top, the best few candidates' estimates are within noise of each other, so the maximum is partly luck. Sharper estimates (importance sampling) should fix exactly that.
- **"Did you validate α?"** Yes: α was chosen on half of the selection data and checked on the other half, never on the test contests. Here every α from 0.90 to 0.99 picked the same lineup, so α wasn't the problem.
- **"p = 0.12: so max projection is better?"** Not significantly. Neither lineup is significantly better yet. More test contests and importance sampling should settle it.
- **"Did you compare lognormal to normal?"** Not yet. The skewness slide is the motivation; the comparison is the first item on the plan.
- **"Your results use mean + λσ candidates and plain Monte Carlo. Will the new method change them?"** That's what the next two weeks test. Mean-CVaR changes the pool we choose from; importance sampling makes the tail estimates sharper, which targets the problem in Result 3.
- **"Why synthetic data?"** So we could build and validate the whole pipeline in the time we had. Real data is the first item on the plan.
