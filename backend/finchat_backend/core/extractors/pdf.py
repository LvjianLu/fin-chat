"""PDF text extractor."""

import io

from finchat_backend.core.extractors.base import TextExtractor


class PdfTextExtractor(TextExtractor):
    """Extract text from PDFs with a fallback parser."""

    extensions = (".pdf",)

    def extract(self, content_bytes: bytes) -> str:
        """Extract text from PDF bytes."""
        import PyPDF2
        import pdfplumber

        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content_bytes))
            return "".join((page.extract_text() or "") + "\n" for page in pdf_reader.pages)
        except Exception:
            with pdfplumber.open(io.BytesIO(content_bytes)) as pdf:
                return "".join((page.extract_text() or "") + "\n" for page in pdf.pages)
