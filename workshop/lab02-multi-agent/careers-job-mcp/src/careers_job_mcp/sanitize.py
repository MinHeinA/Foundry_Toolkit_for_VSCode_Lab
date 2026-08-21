"""Non-executing HTML-to-text normalization."""

from __future__ import annotations

import html
import re
import unicodedata

from bs4 import BeautifulSoup, Comment

_BLOCKED_ELEMENTS = (
    "script",
    "style",
    "template",
    "noscript",
    "iframe",
    "object",
    "embed",
    "svg",
    "canvas",
)
_SPACE_RE = re.compile(r"[^\S\n]+")
_NEWLINES_RE = re.compile(r"\n{3,}")


def _decode_entities(value: str) -> str:
    for _ in range(3):
        decoded = html.unescape(value)
        if decoded == value:
            return value
        value = decoded
    return value


def sanitize_html(value: str) -> str:
    """Convert untrusted, possibly malformed HTML to normalized plain text."""
    if not isinstance(value, str):
        raise TypeError("HTML value must be a string")

    soup = BeautifulSoup(_decode_entities(value), "html.parser")
    for element in soup.find_all(_BLOCKED_ELEMENTS):
        element.decompose()
    for comment in soup.find_all(string=lambda item: isinstance(item, Comment)):
        comment.extract()

    text = unicodedata.normalize("NFKC", soup.get_text(separator="\n"))
    cleaned: list[str] = []
    for char in text:
        if char in "\n\t":
            cleaned.append(char)
        elif not unicodedata.category(char).startswith("C"):
            cleaned.append(char)
    text = "".join(cleaned).replace("\r\n", "\n").replace("\r", "\n")
    lines = [_SPACE_RE.sub(" ", line).strip() for line in text.split("\n")]
    return _NEWLINES_RE.sub("\n\n", "\n".join(line for line in lines if line)).strip()
