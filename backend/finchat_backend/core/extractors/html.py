"""HTML text extractor."""

from finchat_backend.core.extractors.base import TextExtractor


class HtmlTextExtractor(TextExtractor):
    """Extract readable text from HTML documents."""

    extensions = (".htm", ".html")

    def extract(self, content_bytes: bytes) -> str:
        """Parse HTML and collapse whitespace."""
        from bs4 import BeautifulSoup

        html = content_bytes.decode("utf-8")
        soup = BeautifulSoup(html, "lxml")
        return " ".join(soup.get_text().split())
