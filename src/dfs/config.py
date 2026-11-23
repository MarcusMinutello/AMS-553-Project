"""Default parameters for the whole pipeline (see ROADMAP.md section 3)."""
from dataclasses import dataclass, field


@dataclass
class Config:
    # --- slate ---
    n_teams: int = 8                      # 4 games
    salary_cap: int = 50_000
    lineup_size: int = 9

    # --- opponent field (Haugh & Singal Alg. 1) ---
    n_opponents: int = 10_000             # O
    stack_prob: float = 0.35              # q (paper's top-heavy estimate)
    dirichlet_kappa: float = 200.0        # concentration: larger = more predictable ownership
    salary_floor_frac: float = 0.98       # B_lb / B
    own_beta_proj: float = 0.8            # ownership weight on standardized projection
    own_beta_salary: float = -0.8         # ownership weight on standardized salary (paper: cost feature)
    shark_frac: float = 0.20              # share of field built by an optimizer
    shark_pool_size: int = 800            # distinct shark lineups per stage
    shark_noise: float = 0.15             # sharks' projection noise (log-scale sd)
    flex_pos_weights: dict = field(default_factory=lambda: {"RB": 0.45, "WR": 0.45, "TE": 0.10})

    # --- contest ---
    entry_fee: float = 1.0
    rake: float = 0.15
    paid_frac: float = 0.20               # top 20% cash
    min_cash: float = 2.0
    first_place_frac: float = 0.10        # 1st place ~ 10% of the pool

    # --- optimization ---
    ucvar_alpha: float = 0.99
    n_gen_scenarios: int = 300            # scenario-optimal candidate lineups
    lambda_grid: tuple = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5)
    n_select_fields: int = 50             # selection: fields x draws scenarios
    n_select_draws: int = 100

    # --- out-of-sample test ---
    n_test_fields: int = 200
    n_test_draws: int = 10                # "splitting": outcome draws per field
    n_field_lineup_baseline: int = 200    # held-out field lineups per test field

    # --- seeds (separate streams for each stage) ---
    seed_slate: int = 553
    seed_gen: int = 1001
    seed_select: int = 2002
    seed_test: int = 3003
    seed_is: int = 4004

    @property
    def salary_floor(self) -> float:
        return self.salary_floor_frac * self.salary_cap
