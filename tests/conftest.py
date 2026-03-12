"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Add project packages to Python path for imports
sys.path.insert(0, str(PROJECT_ROOT / "backend"))
sys.path.insert(0, str(PROJECT_ROOT / "backend" / "finchat_backend"))

import pytest
from agent_service.config import Settings, load_settings_from_dict


@pytest.fixture
def test_settings():
    """Provide test settings with dummy API key."""
    return load_settings_from_dict(
        {
            "openrouter_api_key": "sk-or-test1234567890",
            "openrouter_model": "stepfun/step-3.5-flash:free",
            "log_level": "DEBUG",
            "data_dir": "./test_data",
            "max_document_size": 10000,
        }
    )


@pytest.fixture
def sample_document():
    """Provide a sample financial document for testing."""
    return """
    AAPL Annual Report 2023

    Revenue: $383.29 billion
    Net Income: $96.99 billion
    Total Assets: $352.58 billion
    Total Liabilities: $290.44 billion

    The company's revenue increased by 2.8% year-over-year.
    Gross margin was 44.5%, operating margin 30.2%.

    Key risk factors include supply chain disruptions and
    regulatory changes in international markets.
    """


@pytest.fixture
def short_document():
    """Provide a short document for testing."""
    return "Revenue was $100 million. Net income reached $50 million."


@pytest.fixture
def mock_openrouter_response():
    """Mock OpenRouter API response."""

    class MockChoice:
        def __init__(self, content):
            self.message = type("obj", (object,), {"content": content})()

    class MockResponse:
        def __init__(self, content):
            self.choices = [MockChoice(content)]
            self.usage = type(
                "obj",
                (object,),
                {"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150},
            )()

    return MockResponse("This is a test response from the chatbot.")
