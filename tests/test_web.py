"""Adapter checks use a local HTTP server only; failure paths use controlled doubles."""

import asyncio
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from playwright.async_api import Error as PlaywrightError

from summarizer.adapters import web
from summarizer.contracts import ExtractionError, PageLoadError


@pytest.fixture
def local_page() -> Iterator[str]:
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<!doctype html><html><body><script>
                setTimeout(() => {
                  let article = document.createElement('article');
                  article.id = 'ready';
                  article.textContent = 'Rendered JavaScript article content is now available.';
                  document.body.appendChild(article);
                }, 100);
                </script></body></html>""")

        def log_message(self, format: str, *args: object) -> None:
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


async def test_load_renders_delayed_javascript(local_page: str) -> None:
    html = await web.PlaywrightPageLoader(readiness_selector="#ready").load(local_page)
    assert '<article id="ready">Rendered JavaScript article' in html


def test_extract_readable_article() -> None:
    paragraph = "The local library opens its renovated reading room this week. " * 12
    result = web.TrafilaturaContentExtractor().extract(
        f"<html><body><nav>Home | Contact</nav><article><h1>Library news</h1>"
        f"<p>{paragraph}</p></article></body></html>"
    )
    assert "renovated reading room" in result
    assert "Home | Contact" not in result


@pytest.mark.parametrize("html", ["", "<html><body></body></html>"])
def test_empty_extraction(html: str) -> None:
    with pytest.raises(ExtractionError, match="no readable content"):
        web.TrafilaturaContentExtractor().extract(html)


def test_extraction_failure_keeps_cause(monkeypatch: pytest.MonkeyPatch) -> None:
    error = ValueError("broken extractor")

    def fail(html: str) -> str:
        raise error

    monkeypatch.setattr(web, "extract", fail)
    with pytest.raises(ExtractionError) as caught:
        web.TrafilaturaContentExtractor().extract("html")
    assert caught.value.__cause__ is error


@pytest.fixture
def browser_double(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    page = SimpleNamespace(
        goto=AsyncMock(return_value=SimpleNamespace(status=200)),
        wait_for_selector=AsyncMock(),
        content=AsyncMock(return_value="<html>rendered</html>"),
    )
    browser = SimpleNamespace(new_page=AsyncMock(return_value=page), close=AsyncMock())
    manager = AsyncMock()
    manager.__aenter__.return_value = SimpleNamespace(
        chromium=SimpleNamespace(launch=AsyncMock(return_value=browser))
    )
    monkeypatch.setattr(web, "async_playwright", lambda: manager)
    return SimpleNamespace(page=page, browser=browser, manager=manager)


async def test_default_readiness_and_cleanup(browser_double: SimpleNamespace) -> None:
    assert await web.PlaywrightPageLoader(123).load("http://local/") == "<html>rendered</html>"
    browser_double.page.goto.assert_awaited_once_with(
        "http://local/", wait_until="domcontentloaded", timeout=123
    )
    browser_double.page.wait_for_selector.assert_not_awaited()
    browser_double.browser.close.assert_awaited_once()
    browser_double.manager.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("operation", ["new_page", "goto", "wait_for_selector", "content"])
async def test_failure_cleans_up_and_chains(
    browser_double: SimpleNamespace, operation: str
) -> None:
    error = PlaywrightError("browser failure or timeout")
    target = browser_double.browser if operation == "new_page" else browser_double.page
    getattr(target, operation).side_effect = error
    with pytest.raises(PageLoadError) as caught:
        await web.PlaywrightPageLoader(20, "#ready").load("http://local/")
    assert caught.value.__cause__ is error
    browser_double.browser.close.assert_awaited_once()
    browser_double.manager.__aexit__.assert_awaited_once()


async def test_cancellation_propagates_and_cleans_up(browser_double: SimpleNamespace) -> None:
    error = asyncio.CancelledError()
    browser_double.page.goto.side_effect = error
    with pytest.raises(asyncio.CancelledError) as caught:
        await web.PlaywrightPageLoader().load("http://local/")
    assert caught.value is error
    browser_double.browser.close.assert_awaited_once()
    browser_double.manager.__aexit__.assert_awaited_once()


async def test_http_error_cleans_up(browser_double: SimpleNamespace) -> None:
    browser_double.page.goto.return_value.status = 503
    with pytest.raises(PageLoadError, match="503"):
        await web.PlaywrightPageLoader().load("http://local/")
    browser_double.browser.close.assert_awaited_once()


@pytest.mark.parametrize("timeout", [0, -1])
def test_timeout_must_be_bounded(timeout: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        web.PlaywrightPageLoader(timeout)


async def test_real_selector_timeout_is_translated(local_page: str) -> None:
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError

    with pytest.raises(PageLoadError) as caught:
        await web.PlaywrightPageLoader(100, "#never-present").load(local_page)
    assert isinstance(caught.value.__cause__, PlaywrightTimeoutError)


async def test_launch_failure_stops_playwright(browser_double: SimpleNamespace) -> None:
    error = PlaywrightError("browser unavailable")
    browser_double.manager.__aenter__.return_value.chromium.launch.side_effect = error
    with pytest.raises(PageLoadError) as caught:
        await web.PlaywrightPageLoader().load("http://local/")
    assert caught.value.__cause__ is error
    browser_double.manager.__aexit__.assert_awaited_once()
    browser_double.browser.close.assert_not_awaited()
