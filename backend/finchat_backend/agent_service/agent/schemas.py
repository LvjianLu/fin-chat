"""Pydantic schemas for tool input/output validation."""

from pydantic import BaseModel, Field


class SearchInput(BaseModel):
    """Input schema for document search tool."""

    query: str = Field(..., description="Search query text")


class AnalysisInput(BaseModel):
    """Input schema for financial analysis tool.

    Note: This tool takes no parameters, but we use a schema for consistency.
    """

    pass


class SECDownloadInput(BaseModel):
    """Input schema for SEC filing download tool."""

    ticker: str = Field(
        ...,
        pattern=r"^[A-Z]{1,5}$",
        description="Stock ticker symbol (1-5 uppercase letters)",
    )
    filing_type: str = Field(
        "10-K",
        description="Filing type: 10-K, 10-Q, or 8-K",
    )
    count: int = Field(
        1,
        ge=1,
        le=5,
        description="Number of filings to download (1-5)",
    )
