"""Explicit demonstration provider; no model or semantic summarization is performed."""

import asyncio
import math
from collections.abc import AsyncGenerator

from summarizer.contracts import SummarizationError


class MockSummarizer:
    """Stream fixed mock text with optional delay and deterministic failure injection."""

    def __init__(
        self,
        *,
        chunk_size: int = 24,
        delay_seconds: float = 0.02,
        fail_after_chunks: int | None = None,
    ) -> None:
        if isinstance(chunk_size, bool) or not isinstance(chunk_size, int) or chunk_size < 1:
            raise ValueError("chunk_size must be a positive integer")
        if isinstance(delay_seconds, bool) or not isinstance(delay_seconds, (int, float)):
            raise TypeError("delay_seconds must be a finite nonnegative number")
        if not math.isfinite(delay_seconds) or delay_seconds < 0:
            raise ValueError("delay_seconds must be a finite nonnegative number")
        if fail_after_chunks is not None and (
            isinstance(fail_after_chunks, bool)
            or not isinstance(fail_after_chunks, int)
            or fail_after_chunks < 0
        ):
            raise ValueError("fail_after_chunks must be a nonnegative integer or None")
        self._chunk_size = chunk_size
        self._delay = delay_seconds
        self._fail_after_chunks = fail_after_chunks

    async def stream(self, source: str) -> AsyncGenerator[str, None]:
        """Yield mock deltas; source content never controls the demonstration output.

        Failure is injected after exactly the configured number of yielded chunks,
        including after the final chunk. A count beyond the stream length never fails.
        Each chunk has a cancellation checkpoint, even when delay is zero.
        """
        output = (
            "MOCK demonstration — this is not a meaningful summary. "
            f"Received {len(source)} source characters. "
            "Connect a local language model provider to generate an actual summary."
        )
        emitted = 0
        for offset in range(0, len(output), self._chunk_size):
            if self._fail_after_chunks == emitted:
                raise SummarizationError("MOCK provider simulated failure")
            await asyncio.sleep(self._delay)
            yield output[offset : offset + self._chunk_size]
            emitted += 1
        if self._fail_after_chunks == emitted:
            raise SummarizationError("MOCK provider simulated failure")
