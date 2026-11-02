"""Summarize-page orchestration, independent of UI and concrete adapters."""

from collections.abc import AsyncGenerator
from contextlib import aclosing
from dataclasses import dataclass
from urllib.parse import urlsplit

from .contracts import ContentExtractor, InvalidURLError, PageLoader, StreamingSummarizer


def validate_url(value: str) -> str:
    """Accept absolute HTTP(S) URLs without credentials or control/space characters."""
    url = value.strip()
    try:
        parsed = urlsplit(url)
        if (
            parsed.scheme.lower() not in {"http", "https"}
            or not parsed.hostname
            or parsed.username is not None
            or parsed.password is not None
            or any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url)
            or "\\" in url
        ):
            raise ValueError("Unsupported URL")
        _ = parsed.port
    except ValueError as exc:
        raise InvalidURLError("Enter an absolute HTTP or HTTPS URL without credentials.") from exc
    return url


@dataclass(frozen=True)
class Update:
    """Accumulated output and current pipeline stage for presentation."""

    stage: str
    text: str = ""


class SummarizePage:
    """Coordinate replaceable loader, extractor and streaming provider dependencies."""

    def __init__(
        self, loader: PageLoader, extractor: ContentExtractor, provider: StreamingSummarizer
    ) -> None:
        self.loader = loader
        self.extractor = extractor
        self.provider = provider

    async def stream(self, url: str) -> AsyncGenerator[Update, None]:
        """Yield snapshots; errors/cancellation propagate and provider streams close."""
        valid_url = validate_url(url)
        yield Update("Loading page")
        html = await self.loader.load(valid_url)
        yield Update("Extracting readable text")
        source = self.extractor.extract(html)
        yield Update("Streaming mock demonstration")
        accumulated = ""
        async with aclosing(self.provider.stream(source)) as chunks:
            async for delta in chunks:
                accumulated += delta
                yield Update("Streaming mock demonstration", accumulated)
        yield Update("Complete — mock demonstration only", accumulated)
