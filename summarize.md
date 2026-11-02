# Local Webpage Summarizer

## Purpose

A local app that accepts a webpage URL and displays a summary beneath the input. Summarization uses the user's existing local LLM, rather than a hosted LLM service.

## Technology stack

| Component | Technology | Responsibility |
| --- | --- | --- |
| Application language | Python | Coordinates page loading, extraction, and summarization. |
| Local user interface | Gradio | Provides a URL text box, a Summarize button, and a summary output below the input. Runs locally and opens in a web browser. |
| Webpage loading | Playwright for Python | Loads the requested webpage in a headless browser and executes JavaScript when needed. |
| Content extraction | Trafilatura | Extracts the main readable content from the rendered HTML, removing navigation and other clutter where possible. |
| Summarization | Existing local LLM | Receives the extracted text and generates the summary locally. The model and its serving interface are still to be identified. |

## Workflow

1. The user pastes a URL into the Gradio text box and clicks Summarize.
2. The UI displays a loading animation while processing.
3. Playwright loads the webpage and retrieves its rendered HTML.
4. Trafilatura extracts the main text.
5. Python sends the extracted text and summarization instructions to the existing local LLM through its supported local interface.
6. The summary appears below the URL input. If the local LLM interface supports streaming, display the summary progressively as it is generated.

## Scope and implementation notes

- This is a single-page summarizer; it does not need to follow links or crawl an entire website.
- The UI and LLM run locally. Fetching public webpages still requires network access.
- No hosted LLM API, React frontend, separate FastAPI server, or database is required for the initial version.
- HTTPX is optional and is not part of the initial stack. It could later fetch simple pages before falling back to Playwright.
- Keep page loading, extraction, and local LLM integration in separate Python modules so they can be maintained independently of the UI.
- Handle invalid URLs, page loading failures, empty extraction, and an unavailable local LLM with clear UI messages.
- For text longer than the local model's context window, split it into sections, summarize each section, and combine the results.
- Treat webpage text as source material, not as instructions that can override the summarization prompt.

## Remaining configuration

- Identify the existing local LLM and how it is served or called.
- Configure its local endpoint or runtime, model identifier, context limit, and streaming support.
