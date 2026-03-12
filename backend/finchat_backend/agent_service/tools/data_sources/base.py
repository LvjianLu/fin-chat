"""Base class for data source adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class DataSourceResult:
    """Standardized result from data source operations.

    Attributes:
        success: Whether the operation succeeded
        data: The retrieved data (can be any type depending on the operation)
        error: Error message if operation failed
        metadata: Additional metadata about the data retrieval
    """

    success: bool
    data: Any = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def __bool__(self) -> bool:
        """Allow DataSourceResult to be used in boolean context."""
        return self.success


class DataSourceAdapter(ABC):
    """Abstract base class for all data source adapters.

    Data source adapters provide a unified interface for fetching data from
    external sources like Yahoo Finance, Alpha Vantage, etc.
    """

    @abstractmethod
    def get_stock_price(self, symbol: str) -> DataSourceResult:
        """Get current stock price for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")

        Returns:
            DataSourceResult with price data or error
        """
        pass

    @abstractmethod
    def get_company_info(self, symbol: str) -> DataSourceResult:
        """Get company information for a stock symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataSourceResult with company info (name, sector, industry, etc.)
        """
        pass

    @abstractmethod
    def get_historical_data(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> DataSourceResult:
        """Get historical price data for a stock.

        Args:
            symbol: Stock ticker symbol
            period: Data period (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Data interval (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")

        Returns:
            DataSourceResult with historical data (OHLCV)
        """
        pass

    @abstractmethod
    def get_financials(self, symbol: str) -> DataSourceResult:
        """Get financial statements for a company.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataSourceResult with financial data (income statement, balance sheet, cash flow)
        """
        pass

    def health_check(self) -> DataSourceResult:
        """Check if the data source is available and responding.

        Returns:
            DataSourceResult indicating health status
        """
        try:
            # Default implementation: try to get a simple request
            result = self.get_stock_price("AAPL")
            if result.success:
                return DataSourceResult(success=True, data="OK", metadata={"source": self.__class__.__name__})
            else:
                return DataSourceResult(
                    success=False,
                    error=f"Health check failed: {result.error}",
                    metadata={"source": self.__class__.__name__}
                )
        except Exception as e:
            logger.error("Health check failed with exception", exc_info=True)
            return DataSourceResult(
                success=False,
                error=f"Health check exception: {str(e)}",
                metadata={"source": self.__class__.__name__}
            )
