# Local Webpage Summarizer

A local Gradio app that loads one rendered HTTP(S) page through Playwright,
extracts readable text with Trafilatura, and streams a **mock demonstration**.
The mock does not produce meaningful summaries, use an LLM, or follow instructions
in webpage text. Its output is fixed demonstration text plus the source character count.

## Setup and use

Requires Python 3.12+ and uv. All Python dependencies live in `.venv`.

```sh
uv sync --locked
uv run playwright install chromium
uv run --locked python -c 'import sys; print(sys.executable)'
uv run --locked python -m summarizer
```

The app opens a browser and binds only `127.0.0.1:7860`, with Gradio sharing disabled.
Paste a URL and click Summarize. Status reports loading, extraction and mock streaming.
Cancel stops the active event; partial output is retained. New runs clear previous output.
Fetching remote pages requires network access. Browser binaries use Playwright's own cache.
`uv.lock` is checked in; dependency changes require `uv sync` and review of the updated lock.

## Checks

```sh
uv sync --locked
uv run --locked pytest -q
uv run --locked ruff format --check src tests
uv run --locked ruff check src tests
uv run --locked mypy src tests
```

The suite requires installed Chromium, local socket binding, and browser process support.
It uses local HTTP fixtures, never public websites or LLMs. Browser smoke tests launch the
actual Gradio app and exercise extraction, streaming, completion, invalid input and cancellation.
Unit tests use independent substitutes to verify orchestration without starting Gradio or Chromium.
See PROGRESS.md for exact execution evidence, mutation checks, and independent review status.

## Architecture and decisions

- `contracts.py`: framework-free loader, extractor, streaming provider Protocols and errors.
- `application.py`: URL validation and summarize-page orchestration; receives dependencies explicitly.
- `adapters/web.py`: resource-owning Playwright loading and Trafilatura extraction.
- `adapters/mock.py`: deterministic deltas, cooperative cancellation, optional injected failures.
- `presentation.py`: Gradio components, event/status mapping and retained partial output on failure.
- `config.py`: validated environment settings; `__main__.py` constructs dependencies and launches.

Dependency direction is presentation → application → contracts; concrete adapters implement contracts.
Only composition constructs concrete dependencies. Application tests demonstrate replaceability.
No database, separate API server, agent framework, or direct HTTPX dependency is added (Gradio has
its own transitive dependencies). Async generators fit Gradio's streaming events and Playwright's
async lifecycle. Extracting synchronously keeps the small local pipeline simple; large extraction
can block the event loop and is a future optimization. Each request owns its browser, avoiding
shared mutable browser state at the cost of startup overhead.

Streams yield nonempty **deltas**, not snapshots. The application accumulates snapshots for UI.
Streams expose `aclose()` and are closed on early termination. Cancellation propagates unchanged;
adapters clean resources. Expected library failures become application errors with chained causes.
A failure after deltas leaves partial output visible and reports failure rather than completion.

Compatibility decisions were checked against installed Gradio 6.31.0, Playwright 1.64.1 and
Trafilatura 2.3.1. Gradio's async generator/event behavior is covered by the browser test;
[Gradio event docs](https://www.gradio.app/docs/gradio/blocks) document `cancels`.
[Playwright navigation docs](https://playwright.dev/python/docs/api/class-page#page-goto)
document bounded `domcontentloaded` navigation and the need to inspect HTTP status explicitly.

## Configuration

| Environment variable | Default | Meaning |
| --- | --- | --- |
| `SUMMARIZER_PORT` | `7860` | Loopback port, 1–65535 |
| `SUMMARIZER_TIMEOUT_MS` | `15000` | Positive navigation timeout; optional selector gets its own same timeout |
| `SUMMARIZER_READY_SELECTOR` | unset | Optional CSS selector to wait for before extracting rendered HTML |
| `SUMMARIZER_MOCK_CHUNK_SIZE` | `12` | Positive characters per simulated delta |
| `SUMMARIZER_MOCK_DELAY` | `0.03` | Delay per delta, 0–60 seconds |

Programmatic `MockSummarizer(fail_after_chunks=N)` injects failure after N deltas for tests.
It is intentionally not an end-user setting. No hidden singleton application state is used.

## Adding a local LLM later

Implement `StreamingSummarizer.stream(source)` as an async generator of nonempty deltas;
translate provider-specific errors to `SummarizationError` with chained diagnostic causes.
Honor cancellation and close owned resources. Treat source as quoted/untrusted material separated
from trusted instructions. Wire the adapter in composition and update provider-specific UI labels.
Run the reusable `TestStreamingProviderContract` with appropriate normal, delayed and failure
factories; exact generated text need not match the mock. Replace loading/extraction similarly
through their small contracts. Different capabilities can require contract changes.

Model configuration, token budgeting, context-window detection, splitting, summary combination,
and model-specific prompt defenses are deferred requirements of a future real provider.
There is no real summary-quality verification in this version.

## Limits

DOM-ready does not mean every dynamic site has finished rendering; configure a readiness selector
for delayed content. No login automation, crawling, download/PDF support or public-site compatibility
promise is provided. HTTP(S) validation is syntax checking, not a network security boundary; redirects,
private network addresses and arbitrary browser subresources are allowed. Use this on trusted URLs
in a trusted local environment. Page size and extraction CPU/memory are not capped. Browser cleanup
is tested for normal, error and cooperative cancellation paths, not process crashes or repeated forced
cancellation. The Gradio queue is bounded to eight pending jobs and one active submission.
