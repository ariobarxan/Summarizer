import asyncio

import pytest
from test_application import Extractor, Loader, Provider

from summarizer.application import SummarizePage
from summarizer.contracts import ExtractionError, PageLoadError, SummarizationError
from summarizer.presentation import create_ui, summarize_event


async def test_ui_resets_and_completes() -> None:
    events = [
        u
        async for u in summarize_event(
            SummarizePage(Loader(), Extractor(), Provider()), "http://test"
        )
    ]
    assert events[0][0] == ""
    assert events[-1] == ("first second", "Complete — mock demonstration only")
    assert any(status == "Loading page" for _, status in events)
    assert any(text == "first" for text, _ in events)


@pytest.mark.parametrize(
    "stage,message",
    [
        ("load", "Could not load"),
        ("extract", "No readable text"),
        ("provider", "partial demonstration"),
    ],
)
async def test_visible_failures(stage: str, message: str) -> None:
    app = SummarizePage(
        Loader(PageLoadError() if stage == "load" else None),
        Extractor(ExtractionError() if stage == "extract" else None),
        Provider(SummarizationError() if stage == "provider" else None),
    )
    events = [u async for u in summarize_event(app, "http://test")]
    assert message in events[-1][1]
    assert events[-1][0] == ("first" if stage == "provider" else "")


async def test_invalid_url_visible() -> None:
    events = [
        u async for u in summarize_event(SummarizePage(Loader(), Extractor(), Provider()), "bad")
    ]
    assert events[-1][1].startswith("Invalid URL")


async def test_unexpected_error_does_not_expose_source() -> None:
    app = SummarizePage(Loader(RuntimeError("private detail")), Extractor(), Provider())
    events = [u async for u in summarize_event(app, "http://test")]
    assert "private detail" not in events[-1][1]
    assert events[-1][1].startswith("Unexpected error")


async def test_ui_cancel_propagates_and_closes() -> None:
    provider = Provider(asyncio.CancelledError())  # type: ignore[arg-type]
    with pytest.raises(asyncio.CancelledError):
        _ = [
            u
            async for u in summarize_event(
                SummarizePage(Loader(), Extractor(), provider), "http://test"
            )
        ]
    assert provider.closed


def test_gradio_builds_with_async_generator_and_cancel() -> None:
    ui = create_ui(SummarizePage(Loader(), Extractor(), Provider()))
    assert any(fn.fn is not None and fn.fn.__name__ == "submit" for fn in ui.fns.values())
    assert any(fn.cancels for fn in ui.fns.values())
