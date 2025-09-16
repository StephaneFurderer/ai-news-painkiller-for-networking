from typing import Optional

# We prefer trafilatura for robust content extraction.
try:
    import trafilatura  # type: ignore
    _HAS_TRAFILATURA = True
except Exception:
    _HAS_TRAFILATURA = False

# Fallback to readability-lxml for article boilerplate removal.
try:
    from readability import Document  # type: ignore
    _HAS_READABILITY = True
except Exception:
    _HAS_READABILITY = False

# Final fallback: BeautifulSoup to strip tags if others are unavailable.
try:
    from bs4 import BeautifulSoup  # type: ignore
    _HAS_BS4 = True
except Exception:
    _HAS_BS4 = False


def extract_readable_text(html: str, url: Optional[str] = None, max_length: Optional[int] = None) -> str:
    """Extract readable main text from raw HTML using battle-tested libraries.

    Preference order:
    1) trafilatura.extract (best quality)
    2) readability-lxml (good boilerplate removal)
    3) BeautifulSoup get_text (basic fallback)

    Args:
        html: Raw HTML content
        url: Optional source URL to help extractors
        max_length: Optional character cap for the returned text

    Returns:
        Clean readable text suitable for LLM prompts or previews.
    """
    text: str = ""

    if _HAS_TRAFILATURA:
        try:
            text = trafilatura.extract(
                html,
                url=url,
                favor_recall=True,
                include_links=False,
                include_images=False,
                with_metadata=False,
            ) or ""
        except Exception:
            text = ""

    if not text and _HAS_READABILITY:
        try:
            doc = Document(html)
            summary_html = doc.summary(html_partial=True)
            if _HAS_BS4:
                soup = BeautifulSoup(summary_html, "lxml")
                text = soup.get_text(separator=" ", strip=True)
            else:
                # Extremely naive strip if bs4 is missing
                text = summary_html
        except Exception:
            text = ""

    if not text and _HAS_BS4:
        try:
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(separator=" ", strip=True)
        except Exception:
            text = ""

    text = text.strip()
    if max_length is not None and max_length > 0 and len(text) > max_length:
        return text[:max_length]
    return text


def build_readable_snippet(html: str, url: Optional[str] = None, max_chars: int = 500) -> str:
    """Convenience helper to get a concise readable snippet from HTML."""
    return extract_readable_text(html, url=url, max_length=max_chars)


