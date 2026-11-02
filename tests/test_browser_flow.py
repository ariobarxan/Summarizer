"""Real Gradio + Chromium + rendered local page + Trafilatura + mock smoke."""

import re
import socket
from pathlib import Path
from typing import Literal

import pytest
from playwright.async_api import async_playwright, expect
from test_web import local_page  # noqa: F401 — fixture shared with adapter integration

from summarizer.adapters.mock import MockSummarizer
from summarizer.adapters.web import PlaywrightPageLoader, TrafilaturaContentExtractor
from summarizer.application import SummarizePage
from summarizer.presentation import create_ui
from summarizer.ui_assets import UI_CSS
from summarizer.ui_style import create_theme


@pytest.mark.parametrize("color_scheme", ["light", "dark"])
async def test_real_gradio_flow(
    local_page: str,  # noqa: F811 — shared HTTP fixture
    tmp_path: Path,
    color_scheme: Literal["light", "dark"],
) -> None:
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
            theme=create_theme(),
            css=UI_CSS,
        )
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            try:
                page = await browser.new_page(color_scheme=color_scheme)
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                await page.goto(f"http://127.0.0.1:{port}")
                switch = page.get_by_role("switch", name="Dark mode", exact=True)
                await expect(switch).to_have_attribute(
                    "aria-checked", str(color_scheme == "dark").lower()
                )
                root = page.locator(".gradio-container")
                await expect(root).to_have_attribute("data-color-mode", color_scheme)
                initial_color = await page.locator("#input-card").evaluate(
                    "e => getComputedStyle(e).backgroundColor"
                )
                # Native switch remains usable with the keyboard.
                await switch.focus()
                await page.keyboard.press("Space")
                chosen = "dark" if color_scheme == "light" else "light"
                await expect(root).to_have_attribute("data-color-mode", chosen)
                assert initial_color != await page.locator("#input-card").evaluate(
                    "e => getComputedStyle(e).backgroundColor"
                )
                assert (
                    await page.evaluate("localStorage.getItem('summarizer-color-mode')") == chosen
                )
                # Explicit choice wins over a conflicting system preference on revisit.
                await page.reload()
                await expect(root).to_have_attribute("data-color-mode", chosen)
                await expect(switch).to_have_attribute(
                    "aria-checked", str(chosen == "dark").lower()
                )
                for width in [1100, 390]:
                    await page.set_viewport_size({"width": width, "height": 1000})
                    assert await page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                await page.set_viewport_size({"width": 1100, "height": 1000})
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
                # Storage can be denied in browser privacy configurations.
                private_page = await browser.new_page(color_scheme="light")
                try:
                    await private_page.add_init_script(
                        """for (const name of ['getItem', 'setItem']) {
                            Storage.prototype[name] = () => { throw new Error('Storage denied'); };
                        }"""
                    )
                    private_page.on("pageerror", lambda error: errors.append(str(error)))
                    await private_page.goto(f"http://127.0.0.1:{port}")
                    private_switch = private_page.get_by_role("switch", name="Dark mode")
                    await expect(private_switch).to_have_attribute("aria-checked", "false")
                    await private_switch.click()
                    await expect(private_switch).to_have_attribute("aria-checked", "true")
                    assert errors == []
                finally:
                    await private_page.close()
            finally:
                await browser.close()
    finally:
        app.close()
