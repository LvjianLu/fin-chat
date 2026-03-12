"""Market data tool for retrieving real-time stock information."""

import logging
from typing import Dict, Any, Optional, List

from .base import Tool, ToolResult
from .data_sources.yahoo_adapter import YahooFinanceAdapter
from .data_sources.base import DataSourceResult

logger = logging.getLogger(__name__)


class MarketDataTool(Tool):
    """Tool for retrieving real-time market data and stock information.

    This tool provides current stock prices, company information, historical data,
    and basic market metrics for publicly traded companies.
    """

    def __init__(self, data_source: Optional[YahooFinanceAdapter] = None):
        """Initialize market data tool.

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
        return "get_market_data"

    @property
    def description(self) -> str:
        """Return tool description for LLM."""
        return "Retrieve real-time market data for a stock symbol including current price, change, company info, and optionally historical data."

    def get_parameters_schema(self) -> Dict[str, Any]:
        """Return JSON Schema for market data tool parameters."""
        return {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol (e.g., AAPL, MSFT, BABA)"
                },
                "data_type": {
                    "type": "string",
                    "enum": ["quote", "info", "historical", "all"],
                    "description": "Type of data to retrieve: quote (current price), info (company information), historical (price history), all (everything)",
                    "default": "quote"
                },
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"],
                    "description": "Historical data period (for historical or all data_type)",
                    "default": "1mo"
                },
                "interval": {
                    "type": "string",
                    "enum": ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"],
                    "description": "Historical data interval (for historical or all data_type)",
                    "default": "1d"
                }
            },
            "required": ["symbol"]
        }

    def execute(
        self,
        symbol: str,
        data_type: str = "quote",
        period: str = "1mo",
        interval: str = "1d"
    ) -> ToolResult:
        """Execute market data retrieval.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")
            data_type: Type of data to retrieve:
                - "quote": current stock quote (default)
                - "info": company information
                - "historical": historical price data
                - "all": all available data
            period: Historical data period (used only if data_type="historical" or "all")
                Options: "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"
            interval: Historical data interval:
                Options: "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"

        Returns:
            ToolResult with market data or error
        """
        try:
            # Validate input
            if not symbol or not isinstance(symbol, str):
                return ToolResult(
                    success=False,
                    error="Invalid symbol: must be a non-empty string"
                )

            symbol = symbol.upper()
            valid_types = ["quote", "info", "historical", "all"]
            if data_type not in valid_types:
                return ToolResult(
                    success=False,
                    error=f"Invalid data_type. Must be one of: {', '.join(valid_types)}"
                )

            result_data: Dict[str, Any] = {}
            metadata: Dict[str, Any] = {
                "symbol": symbol,
                "data_type": data_type,
            }

            # Retrieve requested data
            if data_type in ["quote", "all"]:
                quote_result = self.data_source.get_stock_price(symbol)
                if quote_result.success:
                    result_data["quote"] = quote_result.data
                else:
                    logger.warning(
                        "Failed to retrieve quote",
                        extra={"symbol": symbol, "error": quote_result.error}
                    )

            if data_type in ["info", "all"]:
                info_result = self.data_source.get_company_info(symbol)
                if info_result.success:
                    result_data["info"] = info_result.data
                else:
                    logger.warning(
                        "Failed to retrieve company info",
                        extra={"symbol": symbol, "error": info_result.error}
                    )

            if data_type in ["historical", "all"]:
                hist_result = self.data_source.get_historical_data(
                    symbol, period=period, interval=interval
                )
                if hist_result.success:
                    result_data["historical"] = hist_result.data
                    metadata.update(hist_result.metadata or {})
                else:
                    logger.warning(
                        "Failed to retrieve historical data",
                        extra={"symbol": symbol, "period": period, "interval": interval, "error": hist_result.error}
                    )

            # Check if we got any data
            if not result_data:
                return ToolResult(
                    success=False,
                    error=f"Failed to retrieve any market data for {symbol}"
                )

            logger.info(
                "Market data retrieved",
                extra={"symbol": symbol, "data_type": data_type}
            )

            return ToolResult(
                success=True,
                data=result_data
            )

        except Exception as e:
            logger.error(
                "Market data retrieval failed",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True
            )
            return ToolResult(
                success=False,
                error=f"Failed to retrieve market data: {str(e)}"
            )
