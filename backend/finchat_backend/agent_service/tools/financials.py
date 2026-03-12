"""Financial statements tool for retrieving company financial data."""

import logging
from typing import Any, Dict, Optional

from .base import Tool, ToolResult
from .data_sources.yahoo_adapter import YahooFinanceAdapter
from .data_sources.base import DataSourceResult

logger = logging.getLogger(__name__)


class FinancialStatementsTool(Tool):
    """Tool for retrieving company financial statements from Yahoo Finance.

    This tool provides access to income statements, balance sheets, and cash flow
    statements for publicly traded companies.
    """

    def __init__(self, data_source: Optional[YahooFinanceAdapter] = None):
        """Initialize financial statements tool.

        Args:
            data_source: Optional data source adapter. If None, creates a new YahooFinanceAdapter.
        """
        if data_source is None:
            try:
                self.data_source = YahooFinanceAdapter()
            except ImportError as e:
                raise ImportError(
                    "YahooFinanceAdapter requires yfinance. "
                    f"Install with: pip install yfinance. Error: {e}"
                )
        else:
            self.data_source = data_source

    @property
    def name(self) -> str:
        """Return tool identifier."""
        return "get_financial_statements"

    @property
    def description(self) -> str:
        """Return tool description for LLM."""
        return "Retrieve financial statements (income statement, balance sheet, cash flow) for a company by ticker symbol. Returns structured financial data for analysis."

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for financial statements tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, MSFT, BABA)"
                },
                "statement_type": {
                    "type": "string",
                    "enum": ["income", "balance", "cash_flow", "all"],
                    "description": "Type of financial statement: income (income statement), balance (balance sheet), cash_flow (cash flow statement), all (everything)",
                    "default": "all"
                },
                "period": {
                    "type": "string",
                    "enum": ["annual", "quarterly"],
                    "description": "Reporting period frequency",
                    "default": "annual"
                }
            },
            "required": ["symbol"]
        }

    def execute(
        self,
        symbol: str,
        statement_type: str = "all",
        period: str = "annual"
    ) -> ToolResult:
        """Execute financial statements retrieval.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            statement_type: Type of statement - "income", "balance", "cash_flow", or "all" (default)
            period: "annual" or "quarterly" (default: "annual")

        Returns:
            ToolResult with financial statement data or error
        """
        try:
            # Validate input
            if not symbol or not isinstance(symbol, str):
                return ToolResult(
                    success=False,
                    error="Invalid symbol: must be a non-empty string"
                )

            symbol = symbol.upper()
            valid_types = ["income", "balance", "cash_flow", "all"]
            if statement_type not in valid_types:
                return ToolResult(
                    success=False,
                    error=f"Invalid statement_type. Must be one of: {', '.join(valid_types)}"
                )

            if period not in ["annual", "quarterly"]:
                return ToolResult(
                    success=False,
                    error="Invalid period. Must be 'annual' or 'quarterly'"
                )

            # Get financial data from data source
            result: DataSourceResult = self.data_source.get_financials(symbol)

            if not result.success:
                return ToolResult(
                    success=False,
                    error=result.error or "Failed to retrieve financial data"
                )

            financials = result.data or {}

            # Filter by statement type if requested
            if statement_type != "all":
                key_map = {
                    "income": "income_statement",
                    "balance": "balance_sheet",
                    "cash_flow": "cash_flow"
                }
                statement_key = key_map.get(statement_type)
                if statement_key and statement_key in financials:
                    financials = {statement_key: financials[statement_key]}
                else:
                    logger.warning(
                        "Requested statement type not available",
                        extra={"symbol": symbol, "type": statement_type}
                    )

            # Add metadata
            metadata = {
                "symbol": symbol,
                "statement_type": statement_type,
                "period": period,
                "source": "YahooFinance",
            }

            logger.info(
                "Financial statements retrieved",
                extra={"symbol": symbol, "type": statement_type, "period": period}
            )

            return ToolResult(
                success=True,
                data=financials
            )

        except Exception as e:
            logger.error(
                "Financial statements retrieval failed",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True
            )
            return ToolResult(
                success=False,
                error=f"Failed to retrieve financial statements: {str(e)}"
            )
