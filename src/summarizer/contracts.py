"""Framework-independent boundaries and error semantics.

Streams yield nonempty text deltas, never accumulated snapshots. A provider may
raise SummarizationError after deltas; consumers retain partial output. Cancellation
propagates unchanged. Consumers close streams; adapters own and clean their resources.
Source text is untrusted data, never provider instructions.
"""

from collections.abc import AsyncGenerator
from typing import Protocol


class SummarizerError(Exception):
    """Expected application failure, safe to describe to users via presentation mapping."""


class InvalidURLError(SummarizerError):
    """URL is not a supported absolute HTTP(S) URL."""


class PageLoadError(SummarizerError):
    """Rendered page could not be loaded."""


class ExtractionError(SummarizerError):
    """Readable content could not be extracted."""


class SummarizationError(SummarizerError):
    """Provider failed, possibly after partial output."""


class PageLoader(Protocol):
    async def load(self, url: str) -> str:
        """Return rendered HTML; own resources; raise PageLoadError on library failures."""
        ...


class ContentExtractor(Protocol):
    def extract(self, html: str) -> str:
        """Return nonempty readable text or raise ExtractionError."""
        ...


class StreamingSummarizer(Protocol):
    def stream(self, source: str) -> AsyncGenerator[str, None]:
        """Yield nonempty deltas; raise SummarizationError; propagate cancellation."""
        ...
