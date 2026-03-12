"""Plain text extractor."""

from finchat_backend.core.extractors.base import TextExtractor


class PlainTextExtractor(TextExtractor):
    """Extract UTF-8 text from plain text files."""

    extensions = (".txt",)

    def extract(self, content_bytes: bytes) -> str:
        """Decode plain text bytes."""
        return content_bytes.decode("utf-8")
