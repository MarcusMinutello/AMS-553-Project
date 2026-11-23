"""Correlated player outcomes: Gaussian copula with lognormal marginals.

Z ~ MVN(0, R), points_i = exp(m_i + s_i Z_i), where (m_i, s_i) match each player's
projected mean and SD. Optional importance sampling: draw Z ~ MVN(theta, R) and
return likelihood-ratio weights phi(Z; 0, R) / phi(Z; theta, R).
"""
import numpy as np
import pandas as pd


class OutcomeModel:
    def __init__(self, slate: pd.DataFrame, R: np.ndarray):
        mean = slate["proj"].to_numpy(float)
        sd = slate["sd"].to_numpy(float)
        cv2 = (sd / mean) ** 2
        self.s = np.sqrt(np.log1p(cv2))
        self.m = np.log(mean) - 0.5 * self.s ** 2
        self.R = R
        self.L = np.linalg.cholesky(R)
        self.Rinv = np.linalg.inv(R)
        self.P = len(mean)

    def to_points(self, Z: np.ndarray) -> np.ndarray:
        return np.exp(self.m + self.s * Z)

    def sample_z(self, n: int, rng: np.random.Generator, theta=None) -> tuple[np.ndarray, np.ndarray]:
        Z = rng.standard_normal((n, self.P)) @ self.L.T
        if theta is None:
            return Z, np.ones(n)
        Z = Z + theta
        # log LR = -theta' R^-1 Z + 0.5 theta' R^-1 theta
        a = self.Rinv @ theta
        logw = -(Z @ a) + 0.5 * theta @ a
        return Z, np.exp(logw)

    def sample(self, n: int, rng: np.random.Generator, theta=None) -> tuple[np.ndarray, np.ndarray]:
        """Returns (points[n, P], weights[n])."""
        Z, w = self.sample_z(n, rng, theta)
        return self.to_points(Z), w
