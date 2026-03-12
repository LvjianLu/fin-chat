"""Tests for agent framework components."""

import pytest
from unittest.mock import Mock, patch, MagicMock

from agent_service.agent.llm.openrouter import OpenRouterLLM
from agent_service.agent.memory import ConversationMemory
from agent_service.tools import (
    SearchTool,
    FinAnalysisTool,
    ToolResult,
)
from agent_service.agent import FinChat
from agent_service.config import Settings, load_settings_from_dict
from agent_service.models import (
    SearchResult,
)


class TestOpenRouterLLM:
    """Test OpenRouterLLM provider."""

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_init_with_valid_settings(self, mock_client_class, test_settings):
        """Test LLM initialization with valid settings."""
        mock_client = Mock()
        mock_client_class.return_value = mock_client

        llm = OpenRouterLLM(test_settings)
        assert llm.model == test_settings.openrouter_model
        assert llm.is_available() is True
        mock_client_class.assert_called_once()

    @patch("agent_service.agent.llm.openrouter.OpenRouterClient")
    def test_chat_delegates_to_client(self, mock_client_class, test_settings):
        """Test chat method calls client.chat."""
        mock_client = Mock()
        mock_client.chat.return_value = "Test response"
        mock_client_class.return_value = mock_client

        llm = OpenRouterLLM(test_settings)
        messages = [{"role": "user", "content": "Hello"}]
        response = llm.chat(messages)
        assert response == "Test response"
        mock_client.chat.assert_called_once_with(messages)


class TestConversationMemory:
    """Test ConversationMemory."""

    def test_add_and_get_history(self):
        """Test adding messages and retrieving history."""
        memory = ConversationMemory(max_history=2)
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")
        memory.add_message("user", "How are you?")
        memory.add_message("assistant", "I'm fine")

        history = memory.get_history()
        assert len(history) == 4
        # Should keep last 2 exchanges = 4 messages
        memory._trim_history()
        history = memory.get_history()
        assert len(history) == 4
        assert history[0].content == "Hello"

    def test_set_and_get_document(self):
        """Test loading a document."""
        memory = ConversationMemory()
        memory.set_document("Sample text", "Test Source")
        assert memory.has_document() is True
        assert memory.get_document_context() == "Sample text"
        meta = memory.get_document_metadata()
        assert meta is not None
        assert meta.source_name == "Test Source"
        assert meta.character_count == 11

    def test_clear_document(self):
        """Test clearing document."""
        memory = ConversationMemory()
        memory.set_document("Text", "Source")
        memory.clear_document()
        assert memory.has_document() is False
        assert memory.get_document_metadata() is None

    def test_load_document_clears_history(self):
        """Test that loading a new document clears history."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")
        memory.set_document("Document", "Source")
        assert len(memory.get_history()) == 0

    def test_set_empty_document_raises(self):
        """Test that setting empty document raises error."""
        memory = ConversationMemory()
        with pytest.raises(ValueError):
            memory.set_document("", "Source")


class TestDocumentSearchTool:
    """Test DocumentSearchTool."""

    def test_search_requires_document(self):
        """Test search fails without document."""
        memory = ConversationMemory()
        tool = SearchTool(memory)
        result = tool.execute(query="test")
        assert result.success is False
        assert "No document loaded" in result.error

    def test_search_finds_matches(self):
        """Test search finds expected matches."""
        memory = ConversationMemory()
        doc = "Revenue was $100 million. Net income reached $50 million."
        memory.set_document(doc, "Test")
        tool = SearchTool(memory)
        result = tool.execute(query="revenue")
        assert result.success is True
        assert isinstance(result.data, SearchResult)
        assert result.data.query == "revenue"
        assert result.data.total_matches > 0

    def test_search_no_matches(self):
        """Test search with no matches returns empty result."""
        memory = ConversationMemory()
        doc = "Revenue was $100 million."
        memory.set_document(doc, "Test")
        tool = SearchTool(memory)
        result = tool.execute(query="nonexistent")
        assert result.success is True
        assert result.data.total_matches == 0


class TestFinancialAnalysisTool:
    """Test FinancialAnalysisTool."""

    def test_execute_requires_document_context(self, test_settings):
        """Test that analysis fails without document context."""
        with patch("agent_service.agent.llm.openrouter.OpenAI"):
            llm = OpenRouterLLM(test_settings)
            tool = FinAnalysisTool(llm)
            result = tool.execute()
            assert result.success is False
            assert "Document context is required" in result.error

    def test_execute_calls_llm_with_document(self, test_settings):
        """Test that analysis calls LLM with document context."""
        with patch("agent_service.agent.llm.openrouter.OpenAI") as mock_openai:
            llm = OpenRouterLLM(test_settings)
            mock_llm_chat = Mock(return_value="Analysis report")
            llm.chat = mock_llm_chat

            tool = FinAnalysisTool(llm)
            doc = "Sample financial document data."
            result = tool.execute(document_context=doc)

            assert result.success is True
            assert result.data == "Analysis report"
            # Check that LLM was called with expected messages structure
            args = mock_llm_chat.call_args[0][0]
            assert any("Document Context:" in msg["content"] for msg in args)


class TestFinChat:
    """Test FinChat."""

    def test_init_requires_components(self):
        """Test agent initializes with required components."""
        mock_llm = Mock()
        mock_memory = Mock()
        agent = FinChat(llm=mock_llm, memory=mock_memory)
        assert agent.llm is mock_llm
        assert agent.memory is mock_memory

    def test_run_uses_llm_and_updates_memory(self):
        """Test run method calls LLM and adds messages."""
        mock_llm = Mock()
        mock_llm.chat.return_value = "Response"
        mock_llm.model = "test-model"
        mock_memory = Mock()
        mock_memory.get_document_context.return_value = ""
        mock_memory.get_history.return_value = []
        mock_memory.has_document.return_value = False

        agent = FinChat(llm=mock_llm, memory=mock_memory)
        response = agent.run("Hello")

        assert response == "Response"
        mock_llm.chat.assert_called_once()
        assert mock_memory.add_message.call_count == 2

    def test_load_document_truncates(self):
        """Test that long documents are truncated."""
        mock_llm = Mock()
        mock_client = Mock()
        mock_client.settings = Mock(max_document_size=10)
        mock_llm.client = mock_client
        mock_llm.model = "test"
        mock_memory = Mock()
        mock_memory.set_document = Mock()
        agent = FinChat(llm=mock_llm, memory=mock_memory)
        long_text = "0123456789ABC"  # length 13
        agent.load_document(long_text, "Test")
        truncated = mock_memory.set_document.call_args[0][0]
        # Should be truncated to 10 characters plus "..."
        assert truncated == "0123456789..."

    def test_search_document_uses_tool(self):
        """Test search_document uses tool if available."""
        mock_tool = Mock()
        mock_tool.execute.return_value = ToolResult(success=True, data=SearchResult(
            query="test", matches=[], total_matches=0, displayed_matches=0
        ))
        mock_llm = Mock()
        mock_llm.model = "test"
        mock_memory = Mock()
        mock_memory.has_document.return_value = True
        agent = FinChat(llm=mock_llm, memory=mock_memory, tools=[mock_tool])
        result = agent.search_document("test")
        assert isinstance(result, SearchResult)

    def test_analyze_financials_uses_tool(self):
        """Test analyze_financials uses tool if available."""
        mock_tool = Mock()
        mock_tool.execute.return_value = ToolResult(success=True, data="Analysis")
        mock_llm = Mock()
        mock_llm.model = "test"
        mock_memory = Mock()
        mock_memory.has_document.return_value = True
        mock_memory.get_document_context.return_value = "Doc"
        agent = FinChat(llm=mock_llm, memory=mock_memory, tools=[mock_tool])
        result = agent.analyze_financials()
        assert result == "Analysis"
        mock_tool.execute.assert_called_once_with(document_context="Doc")

    def test_has_document_delegates(self):
        """Test has_document delegates to memory."""
        mock_llm = Mock()
        mock_llm.model = "test"
        mock_memory = Mock()
        mock_memory.has_document.return_value = True
        agent = FinChat(llm=mock_llm, memory=mock_memory)
        assert agent.has_document() is True

    def test_chat_alias(self):
        """Test chat method is alias for run."""
        mock_llm = Mock()
        mock_llm.chat.return_value = "Response"
        mock_llm.model = "test"
        mock_memory = Mock()
        mock_memory.get_document_context.return_value = ""
        mock_memory.get_history.return_value = []
        mock_memory.add_message = Mock()
        mock_memory.has_document.return_value = False
        agent = FinChat(llm=mock_llm, memory=mock_memory)
        response = agent.chat("Hello")
        assert response == "Response"
        # run should have been called (through chat alias)
        mock_llm.chat.assert_called_once()


# Additional tests for Edge cases can be added
