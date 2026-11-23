"""Synthetic DraftKings-style NFL slate and position-pair correlation matrix.

Each team carries 1 QB, 2 RB, 4 WR, 2 TE and 1 DST (10 players). Teams are paired
into games (team 2k plays team 2k+1). Projections scale with a random team-strength
factor; salaries are roughly linear in projection plus noise, so some players are
mispriced ("value"). Players are fictional.
"""
import numpy as np
import pandas as pd

# role -> (position, base projection, coefficient of variation)
ROLES = [
    ("QB1", "QB", 18.0, 0.40),
    ("RB1", "RB", 14.0, 0.55),
    ("RB2", "RB", 7.0, 0.65),
    ("WR1", "WR", 14.0, 0.60),
    ("WR2", "WR", 10.5, 0.65),
    ("WR3", "WR", 7.0, 0.75),
    ("WR4", "WR", 4.0, 0.85),
    ("TE1", "TE", 9.0, 0.65),
    ("TE2", "TE", 4.0, 0.85),
    ("DST", "DST", 7.0, 0.80),
]

# salary ~ intercept + slope * projection (DraftKings-like price levels)
SALARY_MODEL = {
    "QB": (2000, 300), "RB": (1500, 470), "WR": (1500, 470),
    "TE": (1500, 420), "DST": (1800, 230),
}
SALARY_BOUNDS = {"QB": (5000, 8200), "RB": (4000, 9500), "WR": (3000, 9000),
                 "TE": (2500, 7500), "DST": (2000, 4000)}

# Position-pair correlations in the latent Gaussian space (RotoViz-style averages,
# as described in Haugh & Singal Appendix C). Keys are role names.
SAME_TEAM = {
    ("QB1", "WR1"): 0.45, ("QB1", "WR2"): 0.35, ("QB1", "WR3"): 0.25, ("QB1", "WR4"): 0.15,
    ("QB1", "TE1"): 0.30, ("QB1", "TE2"): 0.10,
    ("QB1", "RB1"): 0.10, ("QB1", "RB2"): 0.05,
    ("RB1", "RB2"): -0.15, ("RB1", "DST"): 0.15, ("RB2", "DST"): 0.05,
    ("QB1", "DST"): -0.05,
}
SAME_TEAM_DEFAULT_WR_WR = -0.05   # receivers compete for targets
SAME_TEAM_DEFAULT_WR_TE = -0.05
OPPONENT = {
    ("QB1", "QB1"): 0.20,          # shootouts
    ("QB1", "WR1"): 0.15, ("QB1", "WR2"): 0.10, ("QB1", "TE1"): 0.05,
    ("WR1", "WR1"): 0.10,
}
OPP_DST_VS_OFFENSE = {"QB1": -0.35, "RB1": -0.20, "RB2": -0.10, "WR1": -0.20,
                      "WR2": -0.15, "WR3": -0.10, "WR4": -0.05, "TE1": -0.15, "TE2": -0.05}


def build_slate(n_teams: int = 8, seed: int = 553) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    teams = [f"TM{t + 1}" for t in range(n_teams)]
    strength = rng.uniform(0.85, 1.15, size=n_teams)     # offensive strength
    rows = []
    for t, team in enumerate(teams):
        opp_idx = t + 1 if t % 2 == 0 else t - 1
        for role, pos, base, cv in ROLES:
            if pos == "DST":
                # defense is better against weak offenses
                proj = base * (2.0 - strength[opp_idx]) * rng.uniform(0.9, 1.1)
            else:
                proj = base * strength[t] * rng.uniform(0.85, 1.15)
            a, b = SALARY_MODEL[pos]
            sal = (a + b * proj) * rng.lognormal(0.0, 0.08)
            lo, hi = SALARY_BOUNDS[pos]
            sal = int(np.clip(round(sal / 100) * 100, lo, hi))
            rows.append(dict(name=f"{team}_{role}", team=team, opp=teams[opp_idx],
                             pos=pos, role=role, salary=sal,
                             proj=round(proj, 2), sd=round(proj * cv, 2)))
    df = pd.DataFrame(rows)
    df.insert(0, "pid", np.arange(len(df)))
    df["value"] = df["proj"] / (df["salary"] / 1000.0)
    return df


def _pair(table, r1, r2):
    return table.get((r1, r2), table.get((r2, r1)))


def build_correlation(slate: pd.DataFrame) -> np.ndarray:
    """Latent Gaussian correlation matrix R, repaired to be positive definite."""
    P = len(slate)
    R = np.eye(P)
    team = slate["team"].to_numpy()
    opp = slate["opp"].to_numpy()
    role = slate["role"].to_numpy()
    pos = slate["pos"].to_numpy()
    for i in range(P):
        for j in range(i + 1, P):
            rho = 0.0
            if team[i] == team[j]:
                rho = _pair(SAME_TEAM, role[i], role[j])
                if rho is None:
                    if pos[i] == "WR" and pos[j] == "WR":
                        rho = SAME_TEAM_DEFAULT_WR_WR
                    elif {pos[i], pos[j]} == {"WR", "TE"}:
                        rho = SAME_TEAM_DEFAULT_WR_TE
                    else:
                        rho = 0.0
            elif opp[i] == team[j]:
                if role[i] == "DST" and role[j] != "DST":
                    rho = OPP_DST_VS_OFFENSE.get(role[j], 0.0)
                elif role[j] == "DST" and role[i] != "DST":
                    rho = OPP_DST_VS_OFFENSE.get(role[i], 0.0)
                else:
                    rho = _pair(OPPONENT, role[i], role[j]) or 0.0
            R[i, j] = R[j, i] = rho
    return nearest_correlation(R)


def nearest_correlation(R: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    """Clip negative eigenvalues and rescale to unit diagonal (simple PSD repair)."""
    w, V = np.linalg.eigh(R)
    if w.min() > eps:
        return R
    w = np.clip(w, eps, None)
    R2 = (V * w) @ V.T
    d = np.sqrt(np.diag(R2))
    return R2 / np.outer(d, d)
