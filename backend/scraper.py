"""
scraper.py — Fetches and cleans the main text content from a URL.
"""

import requests
from bs4 import BeautifulSoup
import re


_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Tags whose content we always discard
_SKIP_TAGS = {
    "script", "style", "nav", "header", "footer",
    "aside", "form", "button", "noscript", "iframe",
    "svg", "img", "figure", "figcaption", "advertisement",
}

MAX_CHARS = 4_000   # characters to keep per page (keeps token cost down)


def fetch_page_content(url: str) -> str:
    """
    Download `url` and return cleaned plain text (up to MAX_CHARS chars).
    Returns an empty string on any error.
    """
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=12, allow_redirects=True)
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        if "text/html" not in content_type and "text/plain" not in content_type:
            return ""  # skip PDFs, images, etc.

        return _clean_html(resp.text)

    except Exception as e:
        print(f"[scraper] Failed to fetch {url}: {e}")
        return ""


# ──────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────

def _clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")

    # Remove noisy tags
    for tag in soup(_SKIP_TAGS):
        tag.decompose()

    # Try to find the main content area
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(id=re.compile(r"(content|main|body|article)", re.I))
        or soup.find(class_=re.compile(r"(content|main|body|article|post)", re.I))
        or soup.body
        or soup
    )

    text = main.get_text(separator="\n")
    text = _normalize_whitespace(text)
    return text[:MAX_CHARS]


def _normalize_whitespace(text: str) -> str:
    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse spaces / tabs within a line
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()
