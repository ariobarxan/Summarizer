"""Gradio theme construction; static assets live in assets/."""

import gradio as gr


def create_theme() -> gr.themes.Soft:
    """Create a fresh theme using locally available system fonts."""
    return gr.themes.Soft(
        primary_hue="emerald",
        secondary_hue="teal",
        neutral_hue="slate",
        font=["ui-sans-serif", "system-ui", "sans-serif"],
        font_mono=["ui-monospace", "monospace"],
        radius_size="lg",
    )
