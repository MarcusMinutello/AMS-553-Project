# Speaker script: final deck (`ams_553_slides_final.pdf`)

Slide numbers match the bottom-right corner of the slides (x / 11). The section-divider slides ("1. The problem", "2. The Papers Approach", "3. Our approach") have no number; click through them without stopping.

Each slide lists a target time, a running clock, who presents it, the main ideas, and an example of what to say. **[Brackets]** mark where to point on the slide. Hand-offs are marked **(hand-off)**.

The examples total about 1,500 words, roughly **10.5–11 minutes** at a normal pace. That leaves about a minute of slack in our 12. This deck has no results slides, so the script spends its time explaining the method clearly. Rehearse with the examples, then speak from the main ideas on the day.

**Split** (change it freely):

| Presenter | Slides | Time |
|---|---|---|
| Marcus | 1–4, then 10–11 | about 3:55 |
| Benjamin | 5–6 | about 3:00 |
| Alex | 7–9 | about 3:50 |

**If you're running long**, cut these (about 45 seconds in total):
- the stacking example on slide 4
- the dollar figures on slide 5
- the "why out-of-sample" sentence on slide 6

**If you're running short**, say the optional progress line on slide 10.

## Check before presenting

- **Slide 3's figures are unverified.** Check the 30% to first place and the $1 million prize against a current Millionaire Maker payout table, or say "around" when you quote them.
- **Our runs are smaller than the slides.**
  - Slides 6 and 9 say 100,000 opponents and 100 candidates.
  - Our runs so far used 10,000 opponents and about 320 candidates.
  - The slides describe the design, so this is fine. If anyone asks, the Q&A section has the answer.
- **Optional typo fixes:**
  - "The Papers Approach" should be "The Paper's Approach".
  - Some quote marks are backwards (’boom’).

---

## Slide 1: Title (0:20, clock 0:20), Marcus

**Main ideas**
- Who we are; the topic in one sentence.

**What to say**
> Hi, we're Marcus, Benjamin and Alex. Our project is about Daily Fantasy Sports contests with a hundred thousand entries, where only the very best lineups make real money. We use simulation to build lineups for the best-case scenarios instead of the average one.

---

## Slide 2: Outline (0:25, clock 0:45), Marcus

**Main ideas**
- Three parts: the problem, the paper's approach, our extensions.

**What to say**
> We'll go in three parts. First, the problem, and why winning one of these contests isn't about expected points. Second, the approach from the paper we build on, a three-stage simulation. And third, our three extensions: an Upside CVaR objective, importance sampling for the estimation, and skewed player distributions.

---

## Slide 3: Large-field DFS (1:00, clock 1:45), Marcus

**Main ideas**
- The format: 9 players, $50,000 salary cap, salaries track expected points.
- 100,000+ entries; first place takes about 30% of the pool, about $1 million.
- The 15% rake: the average entry loses money.
- Payouts are top-heavy.

**What to say**
> Quick background. In DraftKings' NFL Millionaire Maker, you pick nine real NFL players: a quarterback, two running backs, three receivers, a tight end, a flex and a defense. You have a fifty-thousand-dollar salary cap, and players who are expected to score more cost more, so you can't just take the best player at every position. Your score is their real fantasy points that weekend.
>
> **[numbers]** These contests draw over a hundred thousand entries every week. First place alone takes around thirty percent of the prize pool, about a million dollars, and that's roughly the top thousandth of a percent of entries. Meanwhile the house keeps fifteen percent of every entry fee, so the average entry loses fifteen cents on the dollar. **[bottom line]** The payouts are extremely top-heavy. To win big, you need an exceptional week.

---

## Slide 4: Maximizing expected points is not optimal (1:15, clock 3:00), Marcus

**Main ideas**
- You need a boom: the expected-points lineup usually lands short of where the money is.
- Stacking: a QB and his receivers are positively correlated, so they boom together.
- The field sets the bar: what matters is how you score relative to everyone else, so ownership matters.
- Our question (blue box). "Random chance" means a typical lineup from the field.

**What to say**
> Here's why that changes the problem. **[left box]** The natural strategy is to pick the lineup with the most expected points. That's a solid lineup, but on a normal weekend it lands well short of the scores that win. So we optimize for the best cases, not the average.
>
> **[middle box]** One way to get a better best case is stacking. A quarterback and his own receivers score together: when the quarterback throws a touchdown, one of his receivers catches it. That positive correlation adds variance, and in a top-heavy contest variance is what produces winning weeks.
>
> **[right box]** And the bar is set by everyone else. If a popular player has a huge game, most of the field goes up with him and you gain nothing. If a player almost nobody picked has a huge game, only you go up. So who everyone else picks matters as much as who you pick.
>
> **[blue box]** That leads to our question: can a lineup chosen for its upper-tail average relative to the field, its Upside CVaR, beat a typical entry by a statistically significant margin? Benjamin will walk through the paper we build on. **(hand-off)**

---

## Slide 5: Building on Haugh & Singal (2019) (1:45, clock 4:45), Benjamin

**Main ideas**
- Their key idea: model the opponents, not just the players.
- Ownership: each contest draws position-by-position ownership shares from a Dirichlet; opponents pick players with those shares (multinomial). Opponents stack QB–WR with probability q.
- Acceptance–rejection: propose a lineup, keep it only if it's legal and spends most of the cap.
- Candidates: mean–variance optimization over a grid of λ, from safe to aggressive.
- Selection: Monte Carlo simulation of the contest picks the best candidate.
- Their payoff: about 4× expected profit, 3× realized profit.

**What to say**
> We build on Haugh and Singal's 2019 paper, "How to Play Fantasy Sports Strategically (and Win)." Their main idea is to model the opponents, not just the players. **[first bullets]** They simulate the whole field. In each contest, every position gets ownership shares drawn from a Dirichlet distribution, centered on how popular each player is expected to be. Each opponent then picks players using those shares, and with probability q they stack a quarterback with one of his receivers. **[acceptance–rejection]** Not every random lineup is legal, so they use acceptance–rejection: propose a lineup, and keep it only if it fits the roster rules and spends most of the salary cap, like real players do.
>
> **[candidate bullet]** To build their own lineups, they solve an integer program that trades expected points against variance, with a weight lambda. Running it over a grid of lambdas gives a menu of candidates, from safe to aggressive. **[last bullet]** Then they simulate many contests against the modeled field and pick the candidate with the best simulated payout.
>
> **[right side]** It worked. Modeling the opponents raised their expected profit in top-heavy contests about four times, from roughly fourteen hundred to six thousand dollars over the 2017 season, and their portfolio's realized profit was three times the benchmark's.

---

## Slide 6: Three simulation stages (1:15, clock 6:00), Benjamin

**Main ideas**
- Stage 1: player outcomes, correlated by position, sampled with crude Monte Carlo.
- Stage 2: the opponent field (Dirichlet ownership, stacking, acceptance–rejection).
- Selection: simulate to find the best of the mean–variance candidates.
- Stage 3: new contests, used only to test the chosen lineup (out-of-sample).

**What to say**
> Here's that method as a pipeline. **[box 1]** Stage one simulates player outcomes. In our implementation that's 80 players, with correlations by position, like a quarterback and his receivers, sampled with ordinary Monte Carlo. **[box 2]** Stage two builds the opponent field using the ownership model I just described, aiming at the size of a real contest: a hundred thousand opponents. **[bottom box]** The selection step combines the two. It generates candidate lineups with mean–variance and simulates contests to find the best one. **[box 3]** Stage three tests that chosen lineup on brand-new contests it has never seen.
>
> That last step matters. If you choose the best of a hundred candidates using noisy estimates, you tend to choose the one that got lucky, so its estimate is biased upward. Testing on fresh contests gives an honest measure of how good the choice really is. Alex will explain what we change. **(hand-off)**

---

## Slide 7: Our changes (1:30, clock 7:30), Alex

**Main ideas**
- 1. Mean–CVaR instead of mean–variance for candidates. Upside CVaR = the average of the best (1 − α) share of outcomes, measured against the field.
- 2. Importance sampling to choose the best candidate: booms are rare, so sample them more often and reweight to stay unbiased.
- 3. Skewed player distributions instead of normal.

**What to say**
> We keep the paper's opponent model and change three things. **[first bullet]** First, candidates come from mean–CVaR instead of mean–variance. Upside CVaR is the average of your best outcomes: with alpha 0.99, it's the average of your best one percent of simulated weeks. Variance penalizes or rewards good and bad weeks alike. Upside CVaR looks only at the good ones, which is where the money is. We also measure it against the field: in each simulated contest, our score minus the score needed for the top 0.1 percent. So a lineup gets credit for booming when the field doesn't.
>
> **[second bullet]** Second, we choose the best candidate with importance sampling. The events we care about, like beating the winning score, are rare, so plain Monte Carlo spends most of its draws on ordinary weeks. Importance sampling shifts the draws toward big games for our lineup's players, then reweights each draw by a likelihood ratio, so the estimate stays unbiased but has much less variance. In our early tests that cut the variance six to twenty-one times, more for rarer events.
>
> **[third bullet]** Third, we drop the normal assumption and give players skewed score distributions. The next slide shows why.

---

## Slide 8: Why skewness matters for candidate selection (1:10, clock 8:40), Alex

**Main ideas**
- The paper assumes multivariate normal scores, which justifies mean–variance.
- Under normality, skewness is zero and mean plus variance fix every tail probability.
- Real fantasy scores are right-skewed; two players can share a mean and variance but have very different upside.
- Upside CVaR sees that difference; mean–variance can't.

**What to say**
> The paper assumes player scores are multivariate normal, and that's what makes mean–variance a sensible way to pick candidates. **[second bullet]** A normal distribution is symmetric, so once you know the mean and variance, you know every tail probability. Nothing else is left to optimize.
>
> But fantasy scores aren't symmetric. Most weeks a player does about what's expected, and once in a while he has a huge game. **[figure]** Both curves here have mean zero and variance one. The normal is symmetric; the lognormal is bunched on the left with a long tail on the right. Mean–variance treats them as identical. Upside CVaR, which looks only at the upper tail, sees that the skewed one has more upside. **[third bullet]** In our model, each player's score is lognormal, matched to his mean and standard deviation, and we keep the correlations between players with a Gaussian copula.

---

## Slide 9: Updated simulation stages (1:10, clock 9:50), Alex

**Main ideas**
- Same pipeline, two boxes changed: Stage 1 uses importance sampling; candidates come from mean–CVaR.
- Opponents stay exactly the paper's, so any difference comes from our changes.
- How we'll evaluate: paired comparison on the same out-of-sample contests against the paper's method and max projection; skewed vs. normal.

**What to say**
> Here's the pipeline with our changes. **[box 1]** Player outcomes are now skewed and sampled with importance sampling. **[bottom box]** Candidates come from mean–CVaR instead of mean–variance. **[box 2]** The opponent field is exactly the paper's. We kept that the same on purpose, so any difference in results comes from our changes and not from a different field.
>
> **[box 3]** For evaluation, every lineup (ours, the paper's mean–variance pick, and the simple max-projection lineup) plays the same set of new contests, with the same random draws. That makes it a paired comparison, which takes out a lot of noise, and we test whether the difference in payout is statistically significant. We'll also run everything with normal and with skewed player scores, to see whether the skew changes which lineup wins. Marcus will wrap up. **(hand-off)**

---

## Slide 10: Summary (0:50, clock 10:40), Marcus

**Main ideas**
- Read the four bullets briefly.
- Optional (use if time allows): progress so far, the simulator reproduces the 15% rake for a typical entry.
- Next: a real DraftKings slate and ownership fitted to real data.

**What to say**
> To sum up. **[bullets]** We're modeling a top-heavy contest against a hundred thousand opponents. We simulate the rare boom weeks with importance sampling. We build the lineup that's best against the opponents we expect, not just the one with the most points. And we test whether that holds when player scores are skewed.
>
> *(Optional:)* So far, we've built the full simulator and checked it against theory: a typical lineup from the field loses about fifteen percent, exactly the rake.
>
> Next, we'll run it on a real DraftKings slate and fit the ownership model to real data, for the final report.

---

## Slide 11: Questions (0:05, clock 10:45), Marcus

**What to say**
> Thank you, we're happy to take questions.

---

## Likely questions

- **"Do you have results yet?"** Early ones, from a simpler version of the method (mean + λσ candidates, plain Monte Carlo selection):
  - **The simulator matches theory.** A typical field lineup returned −16%, with a 95% interval that includes the theoretical −15%.
  - **Max projection is hard to beat** in a field built only from the paper's Algorithm 1. Our field-aware pick returned +205% against +355% for max projection, and the gap isn't significant (p = 0.12).
  - **Tail estimates are noisy.** That's why we're adding importance sampling to the selection step.
- **"Why is max projection so strong there?"**
  - The paper's opponents pick players by popularity, so they rarely build near-optimal lineups. Their average lineup projects to about 89 points, against 103 for max projection.
  - When we replaced 20% of the field with optimizer-built lineups, the picture flipped: the field-aware lineup reached the top 0.1% more than three times as often.
  - So field strength matters a lot, which is why we want ownership fitted to real data.
- **"Your slides say 100,000 opponents. Did you simulate that?"** Not yet. Our runs so far used 10,000 opponents and about 320 candidates. 100,000 is the size of a real Millionaire Maker, and the target for the final runs.
- **"What does 'beat random chance' mean?"** It means beating a lineup drawn the same way as the field. That lineup should lose exactly the 15% rake, so it's the natural baseline.
- **"How is importance sampling still unbiased?"** Each draw is weighted by the likelihood ratio between the original distribution and the shifted one. Over-sampling booms is exactly cancelled by giving each boom a smaller weight.
- **"How do you choose α?"** On half of the selection data, checked on the other half; the test contests are never used. At α = 0.99 with 5,000 scenarios, the tail is only 50 scenarios, which is noisy.
- **"Why lognormal?"** It's right-skewed, positive, and easy to match to each player's mean and standard deviation, and the Gaussian copula keeps the correlations between players.
- **"How do you test significance?"** Every lineup plays the same simulated contests, so we test the paired difference in payout. Intervals are clustered by simulated field, because contests that share a field are correlated.
- **"Why synthetic data?"** So we could build and validate the whole pipeline first. A real slate is next.
