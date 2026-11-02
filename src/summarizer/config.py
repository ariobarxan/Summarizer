"""Validated environment configuration, separate from orchestration."""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    """Local deployment and adapter settings."""

    port: int = 7860
    navigation_timeout_ms: int = 15000
    readiness_selector: str | None = None
    mock_chunk_size: int = 12
    mock_delay_seconds: float = 0.03

    def __post_init__(self) -> None:
        if not 1 <= self.port <= 65535:
            raise ValueError("Port must be in 1..65535")
        if self.navigation_timeout_ms <= 0 or self.mock_chunk_size <= 0:
            raise ValueError("Timeout and chunk size must be positive")
        if not 0 <= self.mock_delay_seconds <= 60:
            raise ValueError("Mock delay must be between 0 and 60 seconds")

    @classmethod
    def from_env(cls) -> "Config":
        """Read only documented SUMMARIZER_* variables."""
        return cls(
            port=int(os.getenv("SUMMARIZER_PORT", "7860")),
            navigation_timeout_ms=int(os.getenv("SUMMARIZER_TIMEOUT_MS", "15000")),
            readiness_selector=os.getenv("SUMMARIZER_READY_SELECTOR") or None,
            mock_chunk_size=int(os.getenv("SUMMARIZER_MOCK_CHUNK_SIZE", "12")),
            mock_delay_seconds=float(os.getenv("SUMMARIZER_MOCK_DELAY", "0.03")),
        )
