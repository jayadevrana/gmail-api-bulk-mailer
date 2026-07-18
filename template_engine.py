"""Simple placeholder-based template engine for personalization."""
from __future__ import annotations

import re
from typing import Dict, Tuple, Set
import logging

logger = logging.getLogger(__name__)

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*(?P<key>[a-zA-Z0-9_\.]+)\s*\}\}")


def render_template(template: str, data: Dict[str, str]) -> Tuple[str, Set[str]]:
    """Render template replacing {{placeholders}} with values.

    Returns rendered string and set of missing keys.
    Missing keys are replaced with empty string but logged by caller.
    """

    missing: Set[str] = set()

    def replace(match: re.Match) -> str:
        key = match.group("key")
        if key in data and data[key] is not None:
            return str(data[key])
        missing.add(key)
        return ""

    rendered = PLACEHOLDER_PATTERN.sub(replace, template)
    return rendered, missing


def inject_tracking_pixel(html_body: str, pixel_url: str = "https://www.google.com/images/cleardot.gif") -> str:
    """Append a 1x1 tracking pixel (optional, transparent Google GIF by default)."""
    pixel_tag = f'<img src="{pixel_url}" alt="" width="1" height="1" style="display:none;"/>'
    return html_body + "\n" + pixel_tag
