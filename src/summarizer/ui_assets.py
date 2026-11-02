"""Load trusted, bundled UI fragments independently of the working directory.

These are static presentation resources, not templates for interpolating page text
or user input. Package resources keep the same loading behavior in an installed wheel.
"""

from importlib.resources import files


def _read_asset(relative_path: str) -> str:
    return files("summarizer").joinpath("assets", relative_path).read_text(encoding="utf-8")


APPEARANCE_HTML = _read_asset("templates/appearance.html")
HERO_HTML = _read_asset("templates/hero.html")
MOCK_NOTICE_HTML = _read_asset("templates/mock_notice.html")
SOURCE_HEADING_HTML = _read_asset("templates/source_heading.html")
OUTPUT_HEADING_HTML = _read_asset("templates/output_heading.html")
FOOTER_HTML = _read_asset("templates/footer.html")
UI_CSS = _read_asset("styles.css")
COLOR_MODE_JS = _read_asset("color_mode.js")
