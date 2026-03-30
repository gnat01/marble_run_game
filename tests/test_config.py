from src import config


def test_fixed_timestep_is_positive() -> None:
    assert config.FIXED_TIMESTEP_SECONDS > 0


def test_target_fps_is_positive() -> None:
    assert config.TARGET_FPS > 0


def test_restitution_is_in_valid_range() -> None:
    assert 0.0 <= config.PHYSICS_GLOBAL_RESTITUTION <= 1.0


def test_damping_matches_no_damping_v1_profile() -> None:
    assert config.PHYSICS_DAMPING == 1.0


def test_default_friction_matches_v1_profile() -> None:
    assert config.PHYSICS_DEFAULT_FRICTION == 0.0


def test_marble_radius_is_positive() -> None:
    assert config.MARBLE_RADIUS > 0


def test_receptacle_dimensions_are_positive() -> None:
    assert config.RECEPTACLE_WIDTH > 0
    assert config.RECEPTACLE_HEIGHT > 0
