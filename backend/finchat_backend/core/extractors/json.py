"""JSON text extractor."""

import json

from finchat_backend.core.extractors.base import TextExtractor


class JsonTextExtractor(TextExtractor):
    """Extract readable text from JSON files."""

    extensions = (".json",)

    def extract(self, content_bytes: bytes) -> str:
        """Parse JSON and convert to readable text format."""
        try:
            data = json.loads(content_bytes.decode("utf-8"))
            return self._format_json(data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON file: {e}") from e

    def _format_json(self, data, indent: int = 0) -> str:
        """Recursively format JSON data into readable text."""
        result = []
        spaces = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    result.append(f"{spaces}{key}:")
                    result.append(self._format_json(value, indent + 1))
                else:
                    result.append(f"{spaces}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                result.append(f"{spaces}[{i}]:")
                result.append(self._format_json(item, indent + 1))
        else:
            result.append(f"{spaces}{data}")

        return "\n".join(result)
