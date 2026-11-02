"""Real Gradio + Chromium + rendered local page + Trafilatura + mock smoke."""

import re
import socket
from pathlib import Path

from playwright.async_api import async_playwright, expect
from test_web import local_page  # noqa: F401 — fixture shared with adapter integration

from summarizer.adapters.mock import MockSummarizer
from summarizer.adapters.web import PlaywrightPageLoader, TrafilaturaContentExtractor
from summarizer.application import SummarizePage
from summarizer.presentation import create_ui


async def test_real_gradio_flow(local_page: str, tmp_path: Path) -> None:  # noqa: F811
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    app = create_ui(
        SummarizePage(
            PlaywrightPageLoader(readiness_selector="#ready"),
            TrafilaturaContentExtractor(),
            MockSummarizer(chunk_size=8, delay_seconds=0.1),
        )
    )
    try:
        app.launch(
            server_name="127.0.0.1",
            server_port=port,
            share=False,
            prevent_thread_lock=True,
            quiet=True,
        )
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page()
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.goto(f"http://127.0.0.1:{port}")
                await page.get_by_label("Webpage URL", exact=True).fill(local_page)
                await page.get_by_role("button", name="Summarize", exact=True).click()
                status = page.get_by_label("Status", exact=True)
                output = page.get_by_label("Mock output", exact=True)
                await expect(output).to_have_value(re.compile(r"MOCK.+"), timeout=30000)
                assert "Connect a local language model provider" not in await output.input_value()
                await expect(status).to_have_value(
                    "Complete — mock demonstration only", timeout=30000
                )
                await expect(output).to_have_value(
                    re.compile("MOCK.*not a meaningful summary", re.DOTALL)
                )
                expected_length = len("Rendered JavaScript article content is now available.")
                assert f"Received {expected_length} source characters" in await output.input_value()
                await page.get_by_label("Webpage URL", exact=True).fill("invalid")
                await page.get_by_role("button", name="Summarize", exact=True).click()
                await expect(status).to_have_value(re.compile("Invalid URL.*"))
                await expect(output).to_have_value("")
                await page.get_by_label("Webpage URL", exact=True).fill(local_page)
                await page.get_by_role("button", name="Summarize", exact=True).click()
                await expect(output).to_have_value(re.compile(r"MOCK.+"), timeout=30000)
                await page.get_by_role("button", name="Cancel", exact=True).click()
                await expect(status).to_have_value(
                    "Cancelled — any partial demonstration is retained."
                )
                partial = await output.input_value()
                assert partial.startswith("MOCK")
                assert "Connect a local language model provider" not in partial
                assert errors == []
                await page.screenshot(path=str(tmp_path / "gradio-smoke.png"))
            finally:
                await browser.close()
    finally:
        app.close()
