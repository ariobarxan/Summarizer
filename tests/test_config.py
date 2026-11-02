import pytest

from summarizer.config import Config


def test_defaults_and_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SUMMARIZER_PORT", "8001")
    monkeypatch.setenv("SUMMARIZER_READY_SELECTOR", "article")
    assert Config.from_env().port == 8001
    assert Config.from_env().readiness_selector == "article"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"port": 0},
        {"navigation_timeout_ms": 0},
        {"mock_chunk_size": 0},
        {"mock_delay_seconds": float("nan")},
        {"mock_delay_seconds": -1},
    ],
)
def test_invalid_configuration(kwargs: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        Config(**kwargs)  # type: ignore[arg-type]
