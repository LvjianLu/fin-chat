"""Document extraction abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod


class TextExtractor(ABC):
    """Extract text from uploaded file bytes."""

    extensions: tuple[str, ...] = ()

    def can_handle(self, filename: str) -> bool:
        """Return whether this extractor supports the file name."""
        filename_lower = filename.lower()
        return any(filename_lower.endswith(extension) for extension in self.extensions)

    @abstractmethod
    def extract(self, content_bytes: bytes) -> str:
        """Extract plain text from file bytes."""
