"""Application-wide constants and patterns."""

# Ticker symbol validation (1-5 uppercase letters)
SUPPORTED_TICKER_PATTERN = r"^[A-Z]{1,5}$"

# Supported filing types
SUPPORTED_FILING_TYPES = ("10-K", "10-Q", "8-K")

# File upload limits
MAX_UPLOAD_SIZE_MB = 50
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
SUPPORTED_UPLOAD_EXTENSIONS = {"txt", "pdf", "htm", "html", "json", "csv"}

# Document processing
DOCUMENT_TRUNCATION_LIMIT = 100_000  # characters
CONVERSATION_HISTORY_MAX_EXCHANGES = 10  # Keep last 10 exchanges (20 messages)
MAX_TOKENS_PER_RESPONSE = 100000

# Default model settings
DEFAULT_MODEL = "stepfun/step-3.5-flash:free"
DEFAULT_TEMPERATURE = 0.3

# API endpoints
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Logging
DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Data directory
DEFAULT_DATA_DIR = "./data"

# Section patterns for SEC filings
SECTION_PATTERNS = {
    "business_overview": r"(?:ITEM\s*1\.?\s*BUSINESS|BUSINESS\s*OVERVIEW)",
    "risk_factors": r"(?:ITEM\s*1A\.?\s*RISK\s*FACTORS|RISK\s*FACTORS)",
    "financial_statements": r"(?:ITEM\s*8\.?\s*FINANCIAL\s*STATEMENTS|FINANCIAL\s*STATEMENTS\s*AND\s*SUPPLEMENTARY\s*DATA)",
    "managements_discussion": r"(?:ITEM\s*7\.?\s*MANAGEMENT'?S\s*DISCUSSION|MANAGEMENT'?S\s*DISCUSSION\s*AND\s*ANALYSIS)",
    "income_statement": r"(?:CONSOLIDATED\s*STATEMENTS\s*OF\s*INCOME|STATEMENTS\s*OF\s*OPERATIONS)",
    "balance_sheet": r"(?:CONSOLIDATED\s*BALANCE\s*SHEETS|BALANCE\s*SHEETS)",
    "cash_flow": r"(?:CONSOLIDATED\s*STATEMENTS\s*OF\s*CASH\s*FLOWS|STATEMENTS\s*OF\s*CASH\s*FLOWS)",
}
