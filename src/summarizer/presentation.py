"""Gradio presentation and testable event logic."""

import logging
from collections.abc import AsyncGenerator
from contextlib import aclosing

import gradio as gr

from .application import Stage, SummarizePage
from .contracts import (
    ExtractionError,
    InvalidURLError,
    PageLoadError,
    SummarizationError,
)
from .ui_assets import (
    APPEARANCE_HTML,
    COLOR_MODE_JS,
    FOOTER_HTML,
    HERO_HTML,
    MOCK_NOTICE_HTML,
    OUTPUT_HEADING_HTML,
    SOURCE_HEADING_HTML,
)

logger = logging.getLogger(__name__)


async def summarize_event(
    use_case: SummarizePage, url: str
) -> AsyncGenerator[tuple[str, str], None]:
    """Reset output, render progress, retain partial output on expected failures."""
    stage_messages = {
        Stage.LOADING: "Loading page",
        Stage.EXTRACTING: "Extracting readable text",
        Stage.STREAMING: "Streaming mock demonstration",
        Stage.COMPLETE: "Complete — mock demonstration only",
    }
    text = ""
    yield text, "Starting — mock provider"
    try:
        async with aclosing(use_case.stream(url)) as updates:
            async for update in updates:
                text = update.output_text
                yield text, stage_messages[update.stage]
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
        with gr.Column(elem_id="workspace"):
            gr.HTML(
                APPEARANCE_HTML,
                elem_id="appearance-bar",
                js_on_load=COLOR_MODE_JS,
            )
            gr.HTML(HERO_HTML, elem_id="hero")
            gr.HTML(MOCK_NOTICE_HTML, elem_id="mock-notice")
            with gr.Column(elem_id="input-card"):
                gr.HTML(SOURCE_HEADING_HTML)
                url = gr.Textbox(
                    label="Webpage URL",
                    placeholder="https://example.com/an-interesting-article",
                    elem_id="url-input",
                )
                with gr.Row(elem_id="actions"):
                    button = gr.Button(
                        "Summarize", variant="primary", scale=3, elem_id="summarize-button"
                    )
                    cancel = gr.Button("Cancel", scale=1, elem_id="cancel-button")
            with gr.Column(elem_id="output-card"):
                gr.HTML(OUTPUT_HEADING_HTML)
                status = gr.Textbox(
                    label="Status",
                    value="Ready — add a webpage to begin.",
                    interactive=False,
                    elem_id="flow-status",
                )
                output = gr.Textbox(
                    label="Mock output",
                    lines=7,
                    interactive=False,
                    elem_id="summary-output",
                    placeholder="Your mock demonstration will appear here…",
                )
            gr.HTML(FOOTER_HTML, elem_id="page-note")
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
