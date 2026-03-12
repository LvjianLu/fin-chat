"""Text processing utilities."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional


def truncate_text(text: str, max_length: int = 100_000, keep_end: bool = False) -> str:
    """Truncate text to maximum length while preserving readability.

    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        keep_end: If True, keep the end of the text instead of the beginning

    Returns:
        Truncated text with ellipsis if truncated
    """
    if len(text) <= max_length:
        return text

    if keep_end:
        # Keep the end (useful for recent content)
        return "..." + text[-max_length + 3 :]
    else:
        # Keep the beginning (default)
        return text[: max_length - 3] + "..."


def clean_text(text: str) -> str:
    """Clean text by normalizing whitespace.

    Args:
        text: Raw text

    Returns:
        Cleaned text with normalized whitespace
    """
    # Replace multiple whitespace with single space
    cleaned = " ".join(text.split())
    return cleaned.strip()


def extract_financial_metrics(text: str) -> list:
    """Extract potential financial metrics from text.

    Args:
        text: Text to analyze

    Returns:
        List of potential metric strings
    """
    # Patterns for common financial metrics
    patterns = [
        r"\$[\d,]+\.?\d*\s*(?:million|billion|thousand|M|B|K)",  # Dollar amounts
        r"[\d,]+\.?\d*\s*%",  # Percentages
        r"(?:revenue|sales|income|profit|loss|assets|liabilities|equity)\s+of\s+\$?[\d,]+\.?\d*",
    ]

    metrics = []
    for pattern in patterns:
        matches = []
        for match in re.finditer(pattern, text, re.IGNORECASE):
            metrics.append(
                {
                    "text": match.group(),
                    "position": match.start(),
                    "pattern_type": pattern.split()[0],
                }
            )
        metrics.extend(matches)

    # Sort by position and remove duplicates
    seen = set()
    unique_metrics = []
    for metric in sorted(metrics, key=lambda x: x["position"]):
        if metric["text"] not in seen:
            seen.add(metric["text"])
            unique_metrics.append(metric)

    return unique_metrics[:100]  # Limit to 100


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem usage.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    normalized = filename.replace("\\", "/")
    name = Path(normalized).name

    # Replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, "_")

    # Limit length
    if len(name) > 100:
        name = name[:100]

    return name


def extract_numbers_with_context(
    text: str, query: Optional[str] = None, context_chars: int = 100
) -> List[Dict[str, Any]]:
    """Extract numbers with surrounding context.

    Args:
        text: Text to search
        query: Optional query to filter results
        context_chars: Number of characters to include as context

    Returns:
        List of matches with context
    """
    import re

    patterns = [
        r"\$[\d,]+\.?\d*\s*(?:million|billion|thousand|M|B|K)?",
        r"[\d,]+\.?\d*\s*(?:%|percent|dollars|USD)",
        r"(?:revenue|sales|income|profit|loss|assets|liabilities|equity)[^\$]*?\$?[\d,]+\.?\d*\s*(?:million|billion|thousand)?",
    ]

    results = []
    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            match_text = match.group()
            start = max(0, match.start() - context_chars)
            end = min(len(text), match.end() + context_chars)
            context = text[start:end].strip()

            if query:
                query_lower = query.lower()
                if query_lower not in context.lower():
                    continue

            results.append(
                {
                    "match": match_text,
                    "context": context,
                    "position": match.start(),
                }
            )

    # Sort by position and limit
    results = sorted(results, key=lambda x: x["position"])[:50]
    return results
