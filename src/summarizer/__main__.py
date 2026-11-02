"""Composition root and local-only launch entry point."""

from .adapters.mock import MockSummarizer
from .adapters.web import PlaywrightPageLoader, TrafilaturaContentExtractor
from .application import SummarizePage
from .config import Config
from .presentation import create_ui
from .ui_assets import UI_CSS
from .ui_style import create_theme


def main() -> None:
    """Construct adapters and launch a loopback-only Gradio server."""
    config = Config.from_env()
    use_case = SummarizePage(
        PlaywrightPageLoader(
            navigation_timeout_ms=config.navigation_timeout_ms,
            readiness_selector=config.readiness_selector,
        ),
        TrafilaturaContentExtractor(),
        MockSummarizer(chunk_size=config.mock_chunk_size, delay_seconds=config.mock_delay_seconds),
    )
    create_ui(use_case).launch(
        server_name="127.0.0.1",
        server_port=config.port,
        share=False,
        inbrowser=True,
        theme=create_theme(),
        css=UI_CSS,
    )


if __name__ == "__main__":
    main()
