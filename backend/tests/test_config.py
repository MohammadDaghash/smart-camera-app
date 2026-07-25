from app import config


def test_env_float_clamps_to_minimum_and_maximum(monkeypatch):
    monkeypatch.setenv("TEST_FLOAT", "2.5")

    assert config._env_float("TEST_FLOAT", 0.5, minimum=0.0, maximum=1.0) == 1.0

    monkeypatch.setenv("TEST_FLOAT", "-0.5")

    assert config._env_float("TEST_FLOAT", 0.5, minimum=0.0, maximum=1.0) == 0.0


def test_env_float_uses_default_for_invalid_values(monkeypatch):
    monkeypatch.setenv("TEST_FLOAT", "not-a-number")

    assert config._env_float("TEST_FLOAT", 0.45, minimum=0.0, maximum=1.0) == 0.45


def test_env_int_clamps_to_minimum_and_maximum(monkeypatch):
    monkeypatch.setenv("TEST_INT", "150")

    assert config._env_int("TEST_INT", 10, minimum=1, maximum=100) == 100

    monkeypatch.setenv("TEST_INT", "-2")

    assert config._env_int("TEST_INT", 10, minimum=1, maximum=100) == 1
