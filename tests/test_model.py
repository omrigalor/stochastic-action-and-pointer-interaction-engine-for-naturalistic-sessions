import math

import pytest

from naturalistic_interaction_engine import NaturalisticInteractionEngine, speed_series


@pytest.mark.parametrize("name", NaturalisticInteractionEngine.models)
def test_trajectory_reaches_target(name):
    model = NaturalisticInteractionEngine(seed=19)
    selected, points = model.trajectory((12, 30), (640, 410), model=name, hz=100)
    assert selected == name
    assert len(points) >= 12
    assert points[0].t >= 0
    assert points[-1].x == pytest.approx(640)
    assert points[-1].y == pytest.approx(410)
    assert all(b.t >= a.t for a, b in zip(points, points[1:]))


def test_fitts_time_increases_with_distance_for_fixed_noise_seed():
    near = NaturalisticInteractionEngine(seed=7).fitts_time(80, 40)
    far = NaturalisticInteractionEngine(seed=7).fitts_time(800, 40)
    assert far > near


def test_session_layer_is_seed_reproducible_and_bounded():
    left = NaturalisticInteractionEngine(seed=11)
    right = NaturalisticInteractionEngine(seed=11)
    left_values = (left.dwell_time(300), left.session_depth(), left.break_time(), left.record_interval())
    right_values = (right.dwell_time(300), right.session_depth(), right.break_time(), right.record_interval())
    assert left_values == right_values
    assert left_values[0] > 0
    assert left_values[1] >= 1
    assert 30 <= left_values[2] <= 900
    assert 56 <= left_values[3] <= 117


def test_speed_series_is_finite_and_nonnegative():
    _, points = NaturalisticInteractionEngine(seed=3).trajectory((0, 0), (500, 220), model="minimum_jerk")
    speeds = speed_series(points)
    assert speeds
    assert all(math.isfinite(speed) and speed >= 0 for _, speed in speeds)
