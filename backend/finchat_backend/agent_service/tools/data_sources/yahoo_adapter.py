"""Yahoo Finance data source adapter."""

import logging
from typing import Any, Dict, Optional
import pandas as pd

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False
    logging.getLogger(__name__).warning("yfinance package not installed. YahooFinanceAdapter will not be available.")

from .base import DataSourceAdapter, DataSourceResult

logger = logging.getLogger(__name__)


class YahooFinanceAdapter(DataSourceAdapter):
    """Data source adapter for Yahoo Finance.

    This adapter uses the yfinance library to fetch stock data from Yahoo Finance.
    It implements the DataSourceAdapter interface for real-time and historical
    financial data retrieval.
    """

    def __init__(self, timeout: int = 10, retries: int = 3):
        """Initialize Yahoo Finance adapter.

        Args:
            timeout: Request timeout in seconds
            retries: Number of retry attempts for failed requests
        """
        if not YF_AVAILABLE:
            raise ImportError(
                "yfinance package is required for YahooFinanceAdapter. "
                "Install it with: pip install yfinance"
            )

        self.timeout = timeout
        self.retries = retries
        self._session = None

    def _create_ticker(self, symbol: str):
        """Create a yfinance Ticker object.

        Args:
            symbol: Stock ticker symbol

        Returns:
            yfinance.Ticker object
        """
        # Use session if available, otherwise default
        if self._session:
            return yf.Ticker(symbol, session=self._session)
        return yf.Ticker(symbol)

    def get_stock_price(self, symbol: str) -> DataSourceResult:
        """Get current stock price for a symbol.

        Args:
            symbol: Stock ticker symbol (e.g., "AAPL", "MSFT")

        Returns:
            DataSourceResult with current price, change, and percent change
        """
        try:
            ticker = self._create_ticker(symbol.upper())
            info = ticker.info

            # Extract relevant price data
            current_price = info.get("regularMarketPrice")
            previous_close = info.get("previousClose")
            change = None
            change_percent = None

            if current_price is not None and previous_close is not None:
                change = current_price - previous_close
                change_percent = (change / previous_close) * 100

            data = {
                "symbol": symbol.upper(),
                "price": current_price,
                "previous_close": previous_close,
                "change": change,
                "change_percent": change_percent,
                "currency": info.get("currency", "USD"),
                "exchange": info.get("exchange", "N/A"),
                "timestamp": pd.Timestamp.now().isoformat(),
            }

            logger.info(
                "Stock price retrieved",
                extra={"symbol": symbol, "price": current_price}
            )

            return DataSourceResult(
                success=True,
                data=data,
                metadata={"source": "YahooFinance", "type": "stock_price"}
            )

        except Exception as e:
            logger.error(
                "Failed to get stock price",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True
            )
            return DataSourceResult(
                success=False,
                error=f"Failed to retrieve stock price for {symbol}: {str(e)}",
                metadata={"symbol": symbol, "source": "YahooFinance"}
            )

    def get_company_info(self, symbol: str) -> DataSourceResult:
        """Get company information for a stock symbol.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataSourceResult with company info (name, sector, industry, etc.)
        """
        try:
            ticker = self._create_ticker(symbol.upper())
            info = ticker.info

            # Extract company information
            company_info = {
                "symbol": symbol.upper(),
                "name": info.get("longName", info.get("shortName", "N/A")),
                "sector": info.get("sector", "N/A"),
                "industry": info.get("industry", "N/A"),
                "country": info.get("country", "N/A"),
                "website": info.get("website", "N/A"),
                "market_cap": info.get("marketCap"),
                "employees": info.get("fullTimeEmployees"),
                "description": info.get("longBusinessSummary", "N/A"),
                "exchange": info.get("exchange", "N/A"),
                "currency": info.get("currency", "USD"),
            }

            logger.info(
                "Company info retrieved",
                extra={"symbol": symbol, "name": company_info["name"]}
            )

            return DataSourceResult(
                success=True,
                data=company_info,
                metadata={"source": "YahooFinance", "type": "company_info"}
            )

        except Exception as e:
            logger.error(
                "Failed to get company info",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True
            )
            return DataSourceResult(
                success=False,
                error=f"Failed to retrieve company info for {symbol}: {str(e)}",
                metadata={"symbol": symbol, "source": "YahooFinance"}
            )

    def get_historical_data(
        self, symbol: str, period: str = "1mo", interval: str = "1d"
    ) -> DataSourceResult:
        """Get historical price data for a stock.

        Args:
            symbol: Stock ticker symbol
            period: Data period (e.g., "1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max")
            interval: Data interval (e.g., "1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo")

        Returns:
            DataSourceResult with historical OHLCV data as DataFrame records
        """
        try:
            ticker = self._create_ticker(symbol.upper())

            # Get historical data
            hist = ticker.history(period=period, interval=interval)

            if hist.empty:
                return DataSourceResult(
                    success=False,
                    error=f"No historical data available for {symbol} with period={period}, interval={interval}",
                    metadata={"symbol": symbol, "source": "YahooFinance"}
                )

            # Reset index to include date as column
            hist = hist.reset_index()
            hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

            # Convert to list of dicts for JSON serialization
            data = hist.to_dict(orient="records")

            # Calculate some summary statistics
            summary = {
                "start_date": hist["Date"].iloc[0] if len(hist) > 0 else None,
                "end_date": hist["Date"].iloc[-1] if len(hist) > 0 else None,
                "total_records": len(hist),
                "columns": list(hist.columns),
            }

            logger.info(
                "Historical data retrieved",
                extra={
                    "symbol": symbol,
                    "period": period,
                    "interval": interval,
                    "records": len(hist)
                }
            )

            return DataSourceResult(
                success=True,
                data=data,
                metadata={
                    "source": "YahooFinance",
                    "type": "historical_data",
                    "summary": summary,
                    "period": period,
                    "interval": interval,
                }
            )

        except Exception as e:
            logger.error(
                "Failed to get historical data",
                extra={"symbol": symbol, "period": period, "interval": interval, "error": str(e)},
                exc_info=True
            )
            return DataSourceResult(
                success=False,
                error=f"Failed to retrieve historical data for {symbol}: {str(e)}",
                metadata={
                    "symbol": symbol,
                    "source": "YahooFinance",
                    "period": period,
                    "interval": interval,
                }
            )

    def get_financials(self, symbol: str) -> DataSourceResult:
        """Get financial statements for a company.

        Args:
            symbol: Stock ticker symbol

        Returns:
            DataSourceResult with financial data (income statement, balance sheet, cash flow)
        """
        try:
            ticker = self._create_ticker(symbol.upper())

            # Get financial statements
            income_stmt = ticker.income_stmt
            balance_sheet = ticker.balance_sheet
            cash_flow = ticker.cash_flow

            # Convert DataFrames to dict structures
            def df_to_dict(df):
                if df.empty:
                    return None
                # Transpose to have dates as rows and items as columns
                df_t = df.transpose()
                df_t = df_t.reset_index().rename(columns={"index": "Date"})
                df_t["Date"] = df_t["Date"].dt.strftime("%Y-%m-%d")
                return df_t.to_dict(orient="records")

            financials = {
                "income_statement": df_to_dict(income_stmt),
                "balance_sheet": df_to_dict(balance_sheet),
                "cash_flow": df_to_dict(cash_flow),
                "symbol": symbol.upper(),
            }

            logger.info(
                "Financial data retrieved",
                extra={"symbol": symbol}
            )

            return DataSourceResult(
                success=True,
                data=financials,
                metadata={
                    "source": "YahooFinance",
                    "type": "financial_statements",
                }
            )

        except Exception as e:
            logger.error(
                "Failed to get financials",
                extra={"symbol": symbol, "error": str(e)},
                exc_info=True
            )
            return DataSourceResult(
                success=False,
                error=f"Failed to retrieve financial data for {symbol}: {str(e)}",
                metadata={"symbol": symbol, "source": "YahooFinance"}
            )
