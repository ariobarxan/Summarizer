"""Summarize-page orchestration, independent of UI and concrete adapters."""

from collections.abc import AsyncGenerator
from contextlib import aclosing
from dataclasses import dataclass
from enum import Enum, auto
from urllib.parse import urlsplit

from .contracts import ContentExtractor, InvalidURLError, PageLoader, StreamingSummarizer


def validate_url(value: str) -> str:
    """Accept absolute HTTP(S) URLs without credentials or control/space characters."""
    url = value.strip()
    try:
        parsed = urlsplit(url)
        if (
            # Only HTTP and HTTPS are supported by this webpage summarizer.
            parsed.scheme.lower() not in {"http", "https"}
            # A hostname is required to identify the server to visit.
            or not parsed.hostname
            # Embedded login credentials are outside this app's supported scope.
            or parsed.username is not None
            # Embedded passwords could also leak through copied URLs or logs.
            or parsed.password is not None
            # Whitespace and control characters can make URL parsing unreliable.
            or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url)
            # Python and browsers may interpret backslashes differently.
            or "\\" in url
        ):
            raise ValueError("Unsupported URL")
        _ = parsed.port
    except ValueError as exc:
        raise InvalidURLError("Enter an absolute HTTP or HTTPS URL without credentials.") from exc
    return url


class Stage(Enum):
    """Provider-independent steps in the summarization flow."""

    LOADING = auto()
    EXTRACTING = auto()
    STREAMING = auto()
    COMPLETE = auto()


@dataclass(frozen=True)
class SummarizationSnapshot:
    """Accumulated output and current pipeline stage for presentation."""

    stage: Stage
    output_text: str = ""


class SummarizePage:
    """Coordinate replaceable loader, extractor and summarizer dependencies."""

    def __init__(
        self, loader: PageLoader, extractor: ContentExtractor, summarizer: StreamingSummarizer
    ) -> None:
        self.loader = loader
        self.extractor = extractor
        self.summarizer = summarizer

    async def stream(self, url: str) -> AsyncGenerator[SummarizationSnapshot, None]:
        """Yield snapshots; errors/cancellation propagate and summarizer streams close."""
        valid_url = validate_url(url)
        yield SummarizationSnapshot(Stage.LOADING)
        html = await self.loader.load(valid_url)
        yield SummarizationSnapshot(Stage.EXTRACTING)
        source = self.extractor.extract(html)
        yield SummarizationSnapshot(Stage.STREAMING)
        accumulated = ""
        async with aclosing(self.summarizer.stream(source)) as chunks:
            async for delta in chunks:
                accumulated += delta
                yield SummarizationSnapshot(Stage.STREAMING, accumulated)
        yield SummarizationSnapshot(Stage.COMPLETE, accumulated)
