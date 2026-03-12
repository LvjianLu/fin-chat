"""Input validation utilities."""

import os
import re
from pathlib import Path
from typing import Any

from ..constants import (
    MAX_UPLOAD_SIZE_BYTES,
    SUPPORTED_UPLOAD_EXTENSIONS,
    SUPPORTED_TICKER_PATTERN,
)
from ..models import ValidationError


def validate_ticker(ticker: str) -> str:
    """Validate and normalize ticker symbol.

    Args:
        ticker: Stock ticker symbol (case insensitive)

    Returns:
        Normalized uppercase ticker

    Raises:
        ValidationError: If ticker is invalid
    """
    if not ticker:
        raise ValidationError("Invalid ticker: value cannot be empty")

    ticker_clean = ticker.strip().upper()

    if not re.match(SUPPORTED_TICKER_PATTERN, ticker_clean):
        raise ValidationError(
            f"Invalid ticker: {ticker}. "
            f"Ticker must be 1-5 uppercase letters (e.g., AAPL, MSFT)."
        )

    return ticker_clean


def validate_file_upload(uploaded_file: Any) -> bool:
    """Validate uploaded file type and size.

    Args:
        uploaded_file: File-like object with name and size attributes

    Returns:
        True if validation passes

    Raises:
        ValidationError: If file is invalid
    """
    # Check file exists
    if not uploaded_file:
        raise ValidationError("No file provided")

    # Check file name
    if not hasattr(uploaded_file, "name"):
        raise ValidationError("File must have a name attribute")

    # Get file extension
    name = uploaded_file.name
    ext = name.split(".")[-1].lower() if "." in name else ""

    if ext not in SUPPORTED_UPLOAD_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type: {ext}. "
            f"Supported: {', '.join(sorted(SUPPORTED_UPLOAD_EXTENSIONS))}"
        )

    # Check file size if available
    file_size = getattr(uploaded_file, "size", None)
    if isinstance(file_size, (int, float)) and not isinstance(file_size, bool):
        if file_size > MAX_UPLOAD_SIZE_BYTES:
            max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
            raise ValidationError(
                f"File too large: {file_size / (1024*1024):.1f}MB. "
                f"Maximum size: {max_mb}MB"
            )
    elif hasattr(uploaded_file, "seek") and hasattr(uploaded_file, "tell"):
        # For file-like objects without size, try to determine
        try:
            current_pos = uploaded_file.tell()
            uploaded_file.seek(0, os.SEEK_END)
            size = uploaded_file.tell()
            uploaded_file.seek(current_pos)

            if (
                isinstance(size, (int, float))
                and not isinstance(size, bool)
                and size > MAX_UPLOAD_SIZE_BYTES
            ):
                max_mb = MAX_UPLOAD_SIZE_BYTES / (1024 * 1024)
                raise ValidationError(
                    f"File too large: {size / (1024*1024):.1f}MB. "
                    f"Maximum size: {max_mb}MB"
                )
        except (OSError, AttributeError):
            # Can't determine size, just skip check
            pass

    return True


def validate_api_key(api_key: str) -> str:
    """Validate OpenRouter API key format.

    Args:
        api_key: API key to validate

    Returns:
        Validated API key

    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError("API key cannot be empty")

    api_key = api_key.strip()
    if not api_key.startswith("sk-or-"):
        raise ValidationError(
            "Invalid OpenRouter API key format. Keys start with 'sk-or-'"
        )

    if len(api_key) < 10:
        raise ValidationError("API key is too short")

    return api_key


def validate_filing_type(filing_type: str) -> str:
    """Validate SEC filing type.

    Args:
        filing_type: Filing type string

    Returns:
        Validated filing type

    Raises:
        ValidationError: If filing type is invalid
    """
    valid_types = {"10-K", "10-Q", "8-K"}
    filing_upper = filing_type.upper()

    if filing_upper not in valid_types:
        raise ValidationError(
            f"Unsupported filing type: {filing_type}. "
            f"Supported: {', '.join(sorted(valid_types))}"
        )

    return filing_upper


def validate_email(email: str) -> str:
    """Validate email address format (simple validation).

    Args:
        email: Email address to validate

    Returns:
        Validated email

    Raises:
        ValidationError: If email is invalid
    """
    if not email:
        raise ValidationError("Invalid email: value cannot be empty")

    # Simple email validation
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, email):
        raise ValidationError(f"Invalid email format: {email}")

    return email


def validate_positive_int(
    value: int, name: str = "value", min_val: int = 1, max_val: int = 100
) -> int:
    """Validate a positive integer within range.

    Args:
        value: Integer to validate
        name: Parameter name for error messages
        min_val: Minimum allowed value
        max_val: Maximum allowed value

    Returns:
        Validated integer

    Raises:
        ValidationError: If value is invalid
    """
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")

    if value < min_val or value > max_val:
        raise ValidationError(
            f"{name} must be between {min_val} and {max_val}, got {value}"
        )

    return value
