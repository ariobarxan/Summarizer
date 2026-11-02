"""Rendered webpage loading and main-content extraction adapters."""

from playwright.async_api import Error as PlaywrightError
from playwright.async_api import async_playwright
from trafilatura import extract

from summarizer.contracts import ExtractionError, PageLoadError


class PlaywrightPageLoader:
    """Use one browser per request and bounded DOM/optional selector readiness.

    DOM content loaded is the default: sites with delayed content can configure a
    readiness selector. No unbounded network-idle wait is used.
    """

    def __init__(
        self, navigation_timeout_ms: int = 30_000, readiness_selector: str | None = None
    ) -> None:
        if navigation_timeout_ms <= 0:
            raise ValueError("navigation_timeout_ms must be positive")
        self.navigation_timeout_ms = navigation_timeout_ms
        self.readiness_selector = readiness_selector

    async def load(self, url: str) -> str:
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                try:
                    page = await browser.new_page()
                    response = await page.goto(
                        url,
                        wait_until="domcontentloaded",
                        timeout=self.navigation_timeout_ms,
                    )
                    if response is not None and response.status >= 400:
                        raise PageLoadError(f"Page returned HTTP {response.status}.")
                    if self.readiness_selector is not None:
                        await page.wait_for_selector(
                            self.readiness_selector,
                            state="attached",
                            timeout=self.navigation_timeout_ms,
                        )
                    return await page.content()
                finally:
                    await browser.close()
        except PlaywrightError as exc:
            raise PageLoadError("Unable to load the webpage.") from exc


class TrafilaturaContentExtractor:
    """Extract readable text from rendered HTML without navigation clutter."""

    def extract(self, html: str) -> str:
        try:
            text = extract(html)
        except Exception as exc:
            raise ExtractionError("Unable to extract readable webpage content.") from exc
        if not text or not text.strip():
            raise ExtractionError("The webpage contains no readable content.")
        return text.strip()
