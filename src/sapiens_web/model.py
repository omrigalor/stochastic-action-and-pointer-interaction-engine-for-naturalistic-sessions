"""SAPIENS-Web: stochastic models of human–web interaction dynamics.

The package generates synthetic interaction traces for simulation, interface testing,
and research prototyping. It does not identify people and it does not claim that the
generated traces are indistinguishable from measured human behavior.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Iterable, Literal

TrajectoryModel = Literal["bezier", "wind", "sigma_lognormal", "minimum_jerk", "mixed"]


@dataclass(frozen=True)
class Point:
    """One sample in a two-dimensional pointer trajectory."""

    t: float
    x: float
    y: float


@dataclass(frozen=True)
class SessionParameters:
    """Parameters for the browsing layer of the model."""

    mean_dwell_seconds: float = 8.0
    dwell_shape: float = 0.8
    mean_session_depth: float = 8.0
    session_shape: float = 12.0
    minimum_break_seconds: float = 30.0
    maximum_break_seconds: float = 900.0
    break_alpha: float = 1.3


class SapiensModel:
    """Seedable hierarchical generator for pointer motion and browsing cadence."""

    models = ("bezier", "wind", "sigma_lognormal", "minimum_jerk")

    def __init__(self, seed: int | None = None, session: SessionParameters | None = None):
        self.rng = random.Random(seed)
        self.session = session or SessionParameters()

    def fitts_time(self, distance: float, target_width: float = 40.0) -> float:
        """Sample movement time from the Shannon form of Fitts's law."""

        width = max(target_width, 1.0)
        expected = 0.12 + 0.14 * math.log2(max(distance, 0.0) / width + 1.0)
        return expected * self.rng.uniform(0.85, 1.25)

    @staticmethod
    def _minimum_jerk(tau: float) -> float:
        return 10 * tau**3 - 15 * tau**4 + 6 * tau**5

    def _sample_count(self, duration: float, hz: float | None) -> int:
        return max(12, int(duration * (hz or self.rng.uniform(70.0, 120.0))))

    def minimum_jerk(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        target_width: float = 40.0,
        hz: float | None = None,
    ) -> list[Point]:
        """Smooth reach with minimum-jerk timing and a small curved deviation."""

        x0, y0 = start
        x1, y1 = end
        distance = math.hypot(x1 - x0, y1 - y0)
        duration = self.fitts_time(distance, target_width)
        n = self._sample_count(duration, hz)
        angle = math.atan2(y1 - y0, x1 - x0)
        bow = self.rng.gauss(0.0, 0.055) * distance
        cx = (x0 + x1) / 2 - bow * math.sin(angle)
        cy = (y0 + y1) / 2 + bow * math.cos(angle)
        points: list[Point] = []
        for i in range(n + 1):
            tau = i / n
            s = self._minimum_jerk(tau)
            x = (1 - s) ** 2 * x0 + 2 * (1 - s) * s * cx + s**2 * x1
            y = (1 - s) ** 2 * y0 + 2 * (1 - s) * s * cy + s**2 * y1
            points.append(Point(tau * duration, x, y))
        return points

    def bezier(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        target_width: float = 40.0,
        hz: float | None = None,
    ) -> list[Point]:
        """Cubic Bézier reach with randomized control points and Fitts timing."""

        x0, y0 = start
        x3, y3 = end
        dx, dy = x3 - x0, y3 - y0
        distance = math.hypot(dx, dy)
        duration = self.fitts_time(distance, target_width)
        n = self._sample_count(duration, hz)
        nx, ny = (-dy / distance, dx / distance) if distance else (0.0, 0.0)
        bend = self.rng.gauss(0.0, 0.08) * distance
        c1 = (x0 + dx * self.rng.uniform(0.22, 0.38) + nx * bend,
              y0 + dy * self.rng.uniform(0.22, 0.38) + ny * bend)
        c2 = (x0 + dx * self.rng.uniform(0.62, 0.82) + nx * bend * 0.45,
              y0 + dy * self.rng.uniform(0.62, 0.82) + ny * bend * 0.45)
        points: list[Point] = []
        for i in range(n + 1):
            tau = i / n
            s = self._minimum_jerk(tau)
            q = 1 - s
            x = q**3 * x0 + 3 * q**2 * s * c1[0] + 3 * q * s**2 * c2[0] + s**3 * x3
            y = q**3 * y0 + 3 * q**2 * s * c1[1] + 3 * q * s**2 * c2[1] + s**3 * y3
            points.append(Point(tau * duration, x, y))
        return points

    def wind(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        target_width: float = 40.0,
        hz: float | None = None,
    ) -> list[Point]:
        """Dynamical reach in which attraction and autocorrelated lateral force interact."""

        x, y = map(float, start)
        x1, y1 = end
        vx = vy = wx = wy = 0.0
        dt = 1.0 / (hz or self.rng.uniform(85.0, 125.0))
        points = [Point(0.0, x, y)]
        elapsed = 0.0
        for _ in range(5000):
            distance = math.hypot(x1 - x, y1 - y)
            if distance < max(0.8, target_width * 0.02):
                break
            wind = min(3.0, distance)
            wx = wx / math.sqrt(3) + self.rng.uniform(-wind, wind) / math.sqrt(5)
            wy = wy / math.sqrt(3) + self.rng.uniform(-wind, wind) / math.sqrt(5)
            if distance < 12.0:
                wx /= math.sqrt(3)
                wy /= math.sqrt(3)
            vx += wx + 9.0 * (x1 - x) / distance
            vy += wy + 9.0 * (y1 - y) / distance
            speed = math.hypot(vx, vy)
            cap = 5.0 if distance < 12.0 else 15.0
            if speed > cap:
                clipped = self.rng.uniform(cap / 2, cap)
                vx, vy = vx / speed * clipped, vy / speed * clipped
            x += vx
            y += vy
            elapsed += dt
            points.append(Point(elapsed, x, y))
        points.append(Point(elapsed + dt, x1, y1))
        return points

    @staticmethod
    def _normal_cdf(z: float) -> float:
        return 0.5 * (1 + math.erf(z / math.sqrt(2)))

    def sigma_lognormal(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        target_width: float = 40.0,
        hz: float | None = None,
    ) -> list[Point]:
        """Primary lognormal stroke followed by an overlapping corrective stroke."""

        x0, y0 = start
        x1, y1 = end
        dx, dy = x1 - x0, y1 - y0
        distance = math.hypot(dx, dy)
        if distance < 1.0:
            return [Point(0.0, x0, y0), Point(0.02, x1, y1)]
        duration = self.fitts_time(distance, target_width)
        angle = math.atan2(dy, dx)
        miss = self.rng.uniform(0.90, 1.06)
        lateral = self.rng.gauss(0.0, 0.025 * distance + 1.0)
        px = x0 + miss * dx - lateral * math.sin(angle)
        py = y0 + miss * dy + lateral * math.cos(angle)
        mu1 = math.log(max(0.04, duration * 0.46))
        sigma1 = self.rng.uniform(0.20, 0.30)
        correction_start = max(0.03, math.exp(mu1) * self.rng.uniform(0.95, 1.20))
        mu2 = math.log(max(0.04, duration * self.rng.uniform(0.16, 0.25)))
        sigma2 = self.rng.uniform(0.22, 0.34)
        end_time = correction_start + math.exp(mu2 + 3 * sigma2)
        sample_hz = hz or self.rng.uniform(75.0, 120.0)
        n = max(16, int(end_time * sample_hz))
        points: list[Point] = []
        for i in range(n + 1):
            t = max(i / sample_hz, 1e-6)
            primary = self._normal_cdf((math.log(t) - mu1) / sigma1)
            if t <= correction_start:
                correction = 0.0
            else:
                correction = self._normal_cdf((math.log(t - correction_start) - mu2) / sigma2)
            x = x0 + (px - x0) * primary + (x1 - px) * correction
            y = y0 + (py - y0) * primary + (y1 - py) * correction
            points.append(Point(t, x, y))
        points.append(Point(end_time + 1 / sample_hz, x1, y1))
        return points

    def trajectory(
        self,
        start: tuple[float, float],
        end: tuple[float, float],
        target_width: float = 40.0,
        model: TrajectoryModel = "mixed",
        hz: float | None = None,
    ) -> tuple[str, list[Point]]:
        """Generate a trajectory and return the selected model name with its samples."""

        selected = self.rng.choice(self.models) if model == "mixed" else model
        if selected not in self.models:
            raise ValueError(f"unknown trajectory model: {selected}")
        generator = getattr(self, selected)
        return selected, generator(start, end, target_width=target_width, hz=hz)

    def dwell_time(self, word_count: int = 0) -> float:
        """Sample screen-and-glean page dwell with an optional reading component."""

        p = self.session
        scale = p.mean_dwell_seconds / math.gamma(1 + 1 / p.dwell_shape)
        dwell = min(self.rng.weibullvariate(scale, p.dwell_shape), p.mean_dwell_seconds * 8)
        reading = min(word_count / self.rng.uniform(600, 1200) * 60 * self.rng.uniform(0.10, 0.30), 20)
        return max(0.4 * p.mean_dwell_seconds, dwell + reading) + self.rng.uniform(0.3, 1.2)

    def session_depth(self) -> int:
        """Sample pages per session from an inverse-Gaussian distribution."""

        mu = self.session.mean_session_depth
        lam = self.session.session_shape
        v = self.rng.gauss(0.0, 1.0) ** 2
        candidate = mu + mu * mu * v / (2 * lam) - mu / (2 * lam) * math.sqrt(
            4 * mu * lam * v + mu * mu * v * v
        )
        sample = candidate if self.rng.random() <= mu / (mu + candidate) else mu * mu / candidate
        return max(1, int(round(sample)))

    def break_time(self) -> float:
        """Sample a bounded-Pareto between-session pause."""

        p = self.session
        low, high, alpha = p.minimum_break_seconds, p.maximum_break_seconds, p.break_alpha
        u = self.rng.random()
        return low / (1 - u * (1 - (low / high) ** alpha)) ** (1 / alpha)

    def record_interval(self, records_per_day: int = 1000) -> float:
        """Sample an interval whose mean spreads a quota across 24 hours."""

        center = 86_400 / max(1, records_per_day)
        return self.rng.triangular(center * 0.65, center * 1.35, center)


def speed_series(points: Iterable[Point]) -> list[tuple[float, float]]:
    """Return (time, pixels/second) for consecutive trajectory samples."""

    samples = list(points)
    result: list[tuple[float, float]] = []
    for previous, current in zip(samples, samples[1:]):
        dt = current.t - previous.t
        if dt > 0:
            result.append((current.t, math.hypot(current.x - previous.x, current.y - previous.y) / dt))
    return result
