"""Gradio presentation and testable event logic."""

import logging
from collections.abc import AsyncGenerator
from contextlib import aclosing

import gradio as gr

from .application import SummarizePage
from .contracts import (
    ExtractionError,
    InvalidURLError,
    PageLoadError,
    SummarizationError,
)

logger = logging.getLogger(__name__)


async def summarize_event(
    use_case: SummarizePage, url: str
) -> AsyncGenerator[tuple[str, str], None]:
    """Reset output, render progress, retain partial output on expected failures."""
    text = ""
    yield text, "Starting — mock provider"
    try:
        async with aclosing(use_case.stream(url)) as updates:
            async for update in updates:
                text = update.text
                yield text, update.stage
    except InvalidURLError:
        yield text, "Invalid URL. Enter an absolute HTTP or HTTPS URL without credentials."
    except PageLoadError:
        yield text, "Could not load the page. Check the address, connectivity, or timeout."
    except ExtractionError:
        yield text, "No readable text could be extracted from this page."
    except SummarizationError:
        yield text, "Mock provider failed. Any partial demonstration is retained."
    except Exception:
        logger.exception("Unexpected summarizer failure")
        yield text, "Unexpected error. See the local application logs for details."


def create_ui(use_case: SummarizePage) -> gr.Blocks:
    """Build a local UI; dependencies are supplied by composition, not globals."""

    async def submit(url: str) -> AsyncGenerator[tuple[str, str], None]:
        async with aclosing(summarize_event(use_case, url)) as updates:
            async for update in updates:
                yield update

    demo = gr.Blocks(title="Local Webpage Summarizer")
    with demo:
        gr.Markdown(
            "# Local Webpage Summarizer\n"
            "**MOCK provider: output is a deterministic streaming demonstration, "
            "not a meaningful summary.** Page text is treated as untrusted source data."
        )
        url = gr.Textbox(label="Webpage URL", placeholder="https://example.com/article")
        with gr.Row():
            button = gr.Button("Summarize", variant="primary")
            cancel = gr.Button("Cancel")
        output = gr.Textbox(label="Mock output", lines=8, interactive=False)
        status = gr.Textbox(label="Status", interactive=False)
        event = button.click(
            submit,
            inputs=url,
            outputs=[output, status],
            concurrency_limit=1,
            show_progress="full",
            api_visibility="private",
        )
        cancel.click(
            lambda: "Cancelled — any partial demonstration is retained.",
            outputs=status,
            cancels=[event],
            queue=False,
            api_visibility="private",
        )
    demo.queue(max_size=8)
    return demo
