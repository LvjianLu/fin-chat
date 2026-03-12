"""SEC filing analysis and financial data extraction."""

import logging
import re
from typing import Any, Dict, List, Optional

from ..constants import SECTION_PATTERNS
from ..models import FinChatError, FinMetric

logger = logging.getLogger(__name__)


class FinDataExtractor:
    """Extract structured financial data from filings."""

    @staticmethod
    def extract_numbers_with_context(
        text: str, query: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Extract dollar amounts and percentages with surrounding context.

        Args:
            text: Text to search
            query: Optional query to filter results

        Returns:
            List of matches with value and context
        """
        patterns = [
            r"\$[\d,]+\.?\d*\s*(?:million|billion|thousand|M|B|K)?",
            r"[\d,]+\.?\d*\s*(?:%|percent|dollars|USD)",
            r"(?:revenue|sales|income|profit|loss|assets|liabilities|equity)[^\$]*?\$?[\d,]+\.?\d*\s*(?:million|billion|thousand)?",
        ]

        results = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                match_text = match.group()
                context = text[
                    max(0, match.start() - 100) : min(len(text), match.end() + 100)
                ].strip()

                # If query provided, check if relevant
                if query:
                    query_lower = query.lower()
                    context_lower = context.lower()
                    if query_lower not in context_lower:
                        continue

                results.append(
                    {
                        "match": match_text,
                        "context": context,
                        "position": match.start(),
                    }
                )

        # Limit results and sort by position
        results = sorted(results, key=lambda x: x["position"])[:50]

        logger.debug(
            "Extracted numbers",
            extra={"pattern_count": len(patterns), "results_count": len(results)},
        )
        return results

    @staticmethod
    def extract_metrics(text: str) -> List[FinMetric]:
        """Extract structured financial metrics.

        Args:
            text: Text content

        Returns:
            List of FinMetric objects
        """
        patterns = {
            "revenue": r"(?:revenue|sales)[^\$]*?\$?([\d,]+\.?\d*\s*(?:million|billion|thousand)?)",
            "net_income": r"(?:net income|net profit)[^\$]*?\$?([\d,]+\.?\d*\s*(?:million|billion|thousand)?)",
            "assets": r"(?:total assets|assets)[^\$]*?\$?([\d,]+\.?\d*\s*(?:million|billion|thousand)?)",
            "liabilities": r"(?:total liabilities|liabilities)[^\$]*?\$?([\d,]+\.?\d*\s*(?:million|billion|thousand)?)",
        }

        metrics = []
        for name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                metric = FinMetric(
                    name=name.replace("_", " ").title(),
                    value=matches[0],
                    context="",
                    source_section=None,
                )
                metrics.append(metric)

        logger.info("Extracted metrics", extra={"count": len(metrics)})
        return metrics
