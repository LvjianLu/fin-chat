"""Financial analysis tool for generating document analysis."""

import logging
from typing import TYPE_CHECKING

from .base import Tool, ToolResult

if TYPE_CHECKING:
    from agent_service.agent.llm import LLMProvider

logger = logging.getLogger(__name__)


class FinAnalysisTool(Tool):
    """Tool for generating comprehensive financial analysis.

    This tool uses the LLM to analyze the currently loaded document
    and produce a structured financial summary.
    """

    ANALYSIS_PROMPT = """Please provide a concise financial analysis summary including:
1. Key revenue figures and trends
2. Profitability metrics (net income, margins)
3. Balance sheet highlights (total assets, liabilities)
4. Cash flow status
5. Notable risk factors
6. Overall financial health assessment

Format as bullet points with specific numbers where available."""

    def __init__(self, llm: "LLMProvider"):
        """Initialize financial analysis tool.

        Args:
            llm: LLM provider to use for generating analysis
        """
        self.llm = llm

    @property
    def name(self) -> str:
        """Return tool identifier."""
        return "analyze_financials"

    @property
    def description(self) -> str:
        """Return tool description for LLM."""
        return "Generate a comprehensive financial analysis summary of the loaded document, including revenue, profitability, balance sheet, cash flow, and risk factors."

    def execute(self, document_context: str = None, **kwargs) -> ToolResult:
        """Execute financial analysis.

        Args:
            document_context: The loaded document text to analyze (required)
            **kwargs: Additional arguments (ignored)

        Returns:
            ToolResult with analysis text on success
        """
        try:
            if not document_context:
                return ToolResult(
                    success=False,
                    error="Document context is required for analysis."
                )

            # Build messages with document context
            messages = [
                {"role": "system", "content": self._get_system_prompt()},
                {
                    "role": "system",
                    "content": f"Document Context:\n\n{document_context}\n\nUse this document to answer the analysis request.",
                },
                {"role": "user", "content": self.ANALYSIS_PROMPT},
            ]

            # Call LLM to generate analysis
            analysis = self.llm.chat(messages)

            logger.info("Financial analysis generated")

            return ToolResult(success=True, data=analysis)

        except Exception as e:
            logger.error("Financial analysis failed", exc_info=True)
            return ToolResult(
                success=False,
                error=f"Analysis failed: {str(e)}"
            )

    def _get_system_prompt(self) -> str:
        """Get system prompt for analysis.

        Returns:
            System prompt string (same as FinChat's system prompt)
        """
        # We use the same system prompt as the FinChat agent
        return """You are a financial analyst assistant specializing in SEC filings and financial statement analysis.

Your capabilities:
- Analyze financial statements (10-K, 10-Q, 8-K)
- Extract and explain key financial metrics
- Answer questions about revenue, income, assets, liabilities, cash flow
- Provide insights on financial trends and ratios
- Explain accounting concepts in simple terms

Guidelines:
1. Always base your answers on the provided document context
2. If information is not available, state that clearly
3. Use bullet points for clarity when listing multiple items
4. Include relevant dollar amounts and percentages when available
5. Be concise but thorough
6. Highlight red flags or important trends
7. Don't provide investment advice (disclaim if necessary)

When analyzing:
- Look for revenue growth trends
- Check profitability margins (gross, operating, net)
- Examine balance sheet strength (debt/equity ratios)
- Review cash flow health
- Identify key risk factors from risk factors section
- Summarize business overview if relevant

Format responses with clear sections and bullet points when appropriate."""
