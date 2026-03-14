"""CSV text extractor."""

import csv
import io

from finchat_backend.core.extractors.base import TextExtractor


class CsvTextExtractor(TextExtractor):
    """Extract text from CSV files."""

    extensions = (".csv",)

    def extract(self, content_bytes: bytes) -> str:
        """Parse CSV and convert to readable text format."""
        try:
            text = content_bytes.decode("utf-8")
            if not text.strip():
                return ""

            # Auto-detect dialect
            sniffer = csv.Sniffer()
            try:
                dialect = sniffer.sniff(text[:1024])
                has_header = sniffer.has_header(text[:1024])
            except csv.Error:
                # If sniffer fails, use default dialect
                dialect = csv.excel
                has_header = False

            reader = csv.reader(io.StringIO(text), dialect)
            rows = list(reader)

            if not rows:
                return ""

            # Build formatted output
            result = []
            if has_header and rows:
                header = rows[0]
                result.append(" | ".join(header))
                result.append("-" * len(" | ".join(header)))

                for row in rows[1:]:
                    result.append(" | ".join(row))
            else:
                for row in rows:
                    result.append(" | ".join(row))

            return "\n".join(result)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file: {e}") from e
