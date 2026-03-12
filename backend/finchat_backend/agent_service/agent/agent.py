"""Agent base class and FinChat implementation."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .llm import LLMProvider
from .memory import ConversationMemory
from ..core.analyzer import FinDataExtractor
from ..models import DocumentMetadata, SearchResult
from ..constants import CONVERSATION_HISTORY_MAX_EXCHANGES

if TYPE_CHECKING:
    from ..tools.base import Tool
    from ..tools.executor import ToolExecutor

logger = logging.getLogger(__name__)

class Agent(ABC):
    """Abstract base class for agents."""

    @abstractmethod
    def run(self, user_input: str) -> str:
        """Process user input and return response.

        Args:
            user_input: User's question or message

        Returns:
            Agent's response text
        """
        pass

    @abstractmethod
    def load_document(self, text: str, source: str) -> str:
        """Load a document into the agent's context.

        Args:
            text: Document content
            source: Document source name

        Returns:
            Success message
        """
        pass

    @abstractmethod
    def clear_document(self) -> str:
        """Clear the current document context.

        Returns:
            Confirmation message
        """
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check if agent is ready to process queries.

        Returns:
            True if agent is ready, False otherwise
        """
        pass


class FinChat(Agent):
    """Financial analysis chat agent with LLM, memory, and tools.

    This agent specializes in analyzing financial statements and SEC filings.
    It uses an LLM provider for reasoning, maintains conversation memory,
    and can utilize various tools for document operations.
    """

    SYSTEM_PROMPT = """You are a financial analyst assistant specializing in SEC filings and financial statement analysis.

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
- Identify key risks from risk factors section
- Summarize business overview if relevant

Format responses with clear sections and bullet points when appropriate.

Tool usage:
- You have access to tools such as:
  - get_market_data: retrieve real-time and recent market data for a given stock symbol (e.g., BABA, AAPL), including current price and recent closing prices.
  - get_financial_statements: retrieve structured financial statements (income statement, balance sheet, cash flow) for a given stock symbol.
- When the user asks about stock prices, closing prices, market performance, or similar real-time market data, call the get_market_data tool with an appropriate symbol.
- When the user asks for detailed financial statements or historical financial metrics, call the get_financial_statements tool.
- After receiving tool results, always summarize and explain the data in clear natural language for the user."""

    def __init__(
        self,
        llm: LLMProvider,
        memory: ConversationMemory,
        tools: Optional[List["Tool"]] = None,
        executor: Optional["ToolExecutor"] = None,
        enable_tool_calling: bool = True,
    ) -> None:
        """Initialize the financial agent.

        Args:
            llm: LLM provider for generating responses
            memory: Conversation memory manager
            tools: Optional list of tools the agent can use (legacy)
            executor: Optional ToolExecutor for unified tool execution
            enable_tool_calling: Whether to enable automatic tool calling
        """
        self.llm = llm
        self.memory = memory
        self.tools = {tool.name: tool for tool in (tools or [])}
        self.executor = executor
        self.enable_tool_calling = enable_tool_calling
        logger.info(
            "FinChat initialized",
            extra={
                "tools": list(self.tools.keys()),
                "model": llm.model,
                "has_executor": executor is not None,
                "enable_tool_calling": enable_tool_calling,
            },
        )

    def run(self, user_input: str) -> str:
        """Process user input and generate response using ReAct pattern.

        This method implements a reasoning-acting loop if tool calling is enabled:
        1. Ask LLM with tools available (if enabled and tools exist)
        2. If tool calls are requested, execute them and observe results
        3. Feed observations back to LLM for final answer

        If tool calling is disabled or fails, falls back to simple chat.

        Args:
            user_input: User's question or message

        Returns:
            Generated response from the LLM

        Raises:
            Exception: If LLM call fails
        """
        # Build initial messages
        messages = self._build_messages(user_input)

        # Check if we should attempt tool calling
        available_tools = list(self.tools.values())
        if not (self.enable_tool_calling and available_tools):
            # Tool calling disabled or no tools - simple chat
            response = self.llm.chat(messages)
            self.memory.add_message("user", user_input)
            self.memory.add_message("assistant", response)
            return response

        # Prepare tool schemas for function calling
        tool_schemas = [tool.to_openai_function() for tool in available_tools]

        # Step 1: Initial LLM call with tools
        try:
            llm_response = self.llm.chat(messages, tools=tool_schemas, tool_choice="auto")
        except Exception as e:
            logger.warning(
                "Tool call attempt failed, falling back to simple chat",
                exc_info=True
            )
            # Fallback to simple chat on tool call failure (e.g., model doesn't support tools)
            response = self.llm.chat(messages)
            self.memory.add_message("user", user_input)
            self.memory.add_message("assistant", response)
            return response

        # Check if response contains OpenAI-style function tool calls
        if isinstance(llm_response, dict) and "tool_calls" in llm_response:
            # We have tool calls to execute
            content = llm_response.get("content", "")
            tool_calls = llm_response["tool_calls"]

            # Add assistant message with tool calls to conversation
            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        }
                    } for tc in tool_calls
                ]
            messages.append(assistant_msg)

            # Execute each tool call
            for tool_call in tool_calls:
                tool_name = tool_call["function"]["name"]
                tool_args_str = tool_call["function"]["arguments"]

                logger.info(
                    "Executing tool",
                    extra={"tool": tool_name, "arguments": tool_args_str}
                )

                try:
                    # Parse arguments
                    import json

                    tool_args = json.loads(tool_args_str)
                    result_content = self._execute_tool(tool_name, tool_args)

                    # Add tool response message
                    messages.append({
                        "role": "tool",
                        "content": result_content,
                        "tool_call_id": tool_call["id"],
                        "name": tool_name
                    })

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse tool arguments: {e}", exc_info=True)
                    messages.append({
                        "role": "tool",
                        "content": f"Error: Invalid arguments for tool {tool_name}",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name
                    })
                except Exception as e:
                    logger.error(f"Tool execution failed: {e}", exc_info=True)
                    messages.append({
                        "role": "tool",
                        "content": f"Error: Tool execution failed: {e}",
                        "tool_call_id": tool_call["id"],
                        "name": tool_name
                    })

            # Step 2: Second LLM call with tool results to get final answer
            try:
                final_response = self.llm.chat(messages)
            except Exception as e:
                logger.error("Final LLM call failed", exc_info=True)
                raise

            # Save to memory
            self.memory.add_message("user", user_input)
            self.memory.add_message("assistant", final_response)

            return final_response

        # Check for XML-style <tool_call> markup in plain-text responses
        if isinstance(llm_response, str) and "<tool_call>" in llm_response:
            response_text = llm_response

            # Parse function name
            func_match = re.search(
                r"<function\s*=\s*([a-zA-Z0-9_\-]+)\s*>", response_text
            )
            if not func_match:
                # If parsing fails, treat as normal answer
                self.memory.add_message("user", user_input)
                self.memory.add_message("assistant", response_text)
                return response_text

            tool_name = func_match.group(1)

            # Parse parameters: <parameter=key> value </parameter>
            params: Dict[str, Any] = {}
            for param_match in re.finditer(
                r"<parameter\s*=\s*([a-zA-Z0-9_\-]+)\s*>(.*?)</parameter>",
                response_text,
                flags=re.DOTALL,
            ):
                key = param_match.group(1)
                value = param_match.group(2).strip()
                params[key] = value

            logger.info(
                "Parsed XML-style tool call",
                extra={"tool": tool_name, "params": params},
            )

            # Add the assistant message that requested the tool
            messages.append({"role": "assistant", "content": response_text})

            # Execute tool via unified executor when available
            try:
                result_content = self._execute_tool(tool_name, params)
                success = not str(result_content).startswith("Error:")
            except Exception as e:
                success = False
                result_content = f"Tool execution failed: {e}"
                logger.error(
                    "XML-style tool execution raised exception",
                    exc_info=True,
                    extra={"tool": tool_name},
                )

            # Append tool result as additional assistant context for the final answer
            tool_context = (
                f"Tool '{tool_name}' was called with parameters {params}.\n"
                f"Execution {'succeeded' if success else 'failed'} with result:\n{result_content}"
            )
            messages.append({"role": "assistant", "content": tool_context})

            # Final LLM call combining original prompt and tool result
            try:
                final_response = self.llm.chat(messages)
            except Exception:
                logger.error("Final LLM call after XML-style tool execution failed", exc_info=True)
                # Fallback to returning the tool context if LLM fails
                final_response = str(tool_context)

            self.memory.add_message("user", user_input)
            self.memory.add_message("assistant", final_response)
            return final_response

        # No tool calls, just normal response
        response = llm_response if isinstance(llm_response, str) else str(llm_response)
        self.memory.add_message("user", user_input)
        self.memory.add_message("assistant", response)
        return response

    def load_document(self, text: str, source: str) -> str:
        """Load a document into context.

        Args:
            text: Document content
            source: Source name for metadata

        Returns:
            Success message with character count

        Raises:
            DocumentError: If document loading fails
        """
        if not text:
            from ..models import DocumentError
            raise DocumentError("Cannot load empty document")

        try:
            # Truncate if too long
            max_size = self.llm.client.settings.max_document_size
            if len(text) > max_size:
                logger.warning(
                    "Document truncated",
                    extra={
                        "original_length": len(text),
                        "truncated_length": max_size,
                    },
                )
                text = text[:max_size] + "..."

            self.memory.set_document(text, source)
            doc_meta = self.memory.get_document_metadata()
            logger.info(
                "Document loaded successfully",
                extra={
                    "source": source,
                    "character_count": len(text),
                    "truncated": len(text) < len(text),
                },
            )

            if doc_meta:
                return f"Loaded {source} successfully. Document contains {len(text):,} characters. You can now ask questions about it."
            return f"Loaded {source} successfully"

        except Exception as e:
            logger.error("Document loading failed", exc_info=True)
            from ..models import DocumentError
            raise DocumentError(f"Failed to load document: {e}") from e

    def clear_document(self) -> str:
        """Clear document context and history.

        Returns:
            Confirmation message
        """
        self.memory.clear_document()
        return "Document cleared"

    def is_ready(self) -> bool:
        """Check if agent is ready.

        Agent is ready when LLM is available and a document is loaded.

        Returns:
            True if ready, False otherwise
        """
        return self.llm.is_available() and self.memory.has_document()

    def get_document_metadata(self) -> Optional[DocumentMetadata]:
        """Get metadata for the loaded document.

        Returns:
            DocumentMetadata if document loaded, None otherwise
        """
        return self.memory.get_document_metadata()

    def has_document(self) -> bool:
        """Check if a document is loaded.

        Returns:
            True if a document is loaded, False otherwise
        """
        return self.memory.has_document()

    def chat(self, message: str) -> str:
        """Send a message and get a response (alias for run).

        Args:
            message: User's question/message

        Returns:
            Assistant's response text
        """
        return self.run(message)

    def search_document(self, query: str) -> SearchResult:
        """Search for terms in the loaded document.

        Args:
            query: Search query string

        Returns:
            SearchResult with matches

        Raises:
            DocumentError: If no document is loaded
        """
        # Try using ToolExecutor first if available
        if self.executor:
            result = self.executor.execute("search_document", query=query)
            if result.success:
                return result.data
            # If not found or fails, fall through to legacy method
            if not result.success and "not found" not in result.error.lower():
                from ..models import DocumentError
                raise DocumentError(result.error or "Search failed via executor")

        # Legacy: direct tool execution
        if "search_document" in self.tools:
            result = self.tools["search_document"].execute(query=query)
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Search failed")
            return result.data
        if len(self.tools) == 1:
            result = next(iter(self.tools.values())).execute(query=query)
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Search failed")
            return result.data
        else:
            # Fallback implementation if tool not provided
            if not self.memory.has_document():
                from ..models import DocumentError
                raise DocumentError("No document loaded")
            extractor = FinDataExtractor()
            matches = extractor.extract_numbers_with_context(
                self.memory.get_document_context(), query
            )
            return SearchResult(
                query=query,
                matches=matches,
                total_matches=len(matches),
                displayed_matches=min(len(matches), 5),
            )

    def analyze_financials(self) -> str:
        """Generate a financial analysis of the loaded document.

        Returns:
            Analysis text

        Raises:
            DocumentError: If no document is loaded
        """
        if not self.memory.has_document():
            from ..models import DocumentError
            raise DocumentError("No document loaded. Please load a financial statement first.")

        # Try using ToolExecutor first if available
        if self.executor:
            result = self.executor.execute(
                "analyze_financials",
                document_context=self.memory.get_document_context()
            )
            if result.success:
                return result.data
            # If not found or fails, fall through to legacy method
            if not result.success and "not found" not in result.error.lower():
                from ..models import DocumentError
                raise DocumentError(result.error or "Analysis failed via executor")

        # Legacy: direct tool execution
        if "analyze_financials" in self.tools:
            result = self.tools["analyze_financials"].execute(
                document_context=self.memory.get_document_context()
            )
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Analysis failed")
            return result.data
        if len(self.tools) == 1:
            result = next(iter(self.tools.values())).execute(
                document_context=self.memory.get_document_context()
            )
            if not result.success:
                from ..models import DocumentError
                raise DocumentError(result.error or "Analysis failed")
            return result.data
        else:
            # Fallback: use LLM directly with analysis prompt
            analysis_prompt = """Please provide a concise financial analysis summary including:
1. Key revenue figures and trends
2. Profitability metrics (net income, margins)
3. Balance sheet highlights (total assets, liabilities)
4. Cash flow status
5. Notable risk factors
6. Overall financial health assessment

Format as bullet points with specific numbers where available."""
            return self.run(analysis_prompt)

    def _build_messages(self, user_message: str) -> List[dict[str, str]]:
        """Build complete message list for the LLM API.

        Args:
            user_message: Current user message

        Returns:
            List of message dictionaries with 'role' and 'content'
        """
        messages = [{"role": "system", "content": self.SYSTEM_PROMPT}]

        # Add document context if available
        if self.memory.get_document_context():
            doc_msg = {
                "role": "system",
                "content": f"Document Context:\n\n{self.memory.get_document_context()}\n\nUse this document to answer user questions.",
            }
            messages.append(doc_msg)

        # Add conversation history
        history = self.memory.get_history(limit=CONVERSATION_HISTORY_MAX_EXCHANGES)
        if not isinstance(history, list):
            history = []
        for msg in history:
            messages.append(msg.to_dict())

        # Add current user message as user role
        messages.append({"role": "user", "content": user_message})
        return messages

    def _execute_tool(self, tool_name: str, params: Dict[str, Any]) -> str:
        """Execute a tool through the unified executor interface."""
        if self.executor:
            result = self.executor.execute(tool_name, **params)
            if result.success:
                result_content = str(result.data)
                logger.info(
                    "Tool execution via executor successful",
                    extra={"tool": tool_name, "result_size": len(result_content)},
                )
                return result_content

            logger.warning(
                "Tool execution via executor failed",
                extra={"tool": tool_name, "error": result.error},
            )
            return f"Error: {result.error}"

        if tool_name in self.tools:
            tool_result = self.tools[tool_name].execute(**params)
            if tool_result.success:
                result_content = str(tool_result.data)
                logger.info(
                    "Tool execution successful",
                    extra={"tool": tool_name, "result_size": len(result_content)},
                )
                return result_content

            logger.warning(
                "Tool execution failed",
                extra={"tool": tool_name, "error": tool_result.error},
            )
            return f"Error: {tool_result.error}"

        logger.warning(
            "Tool not available for execution",
            extra={"tool": tool_name},
        )
        return f"Error: Tool '{tool_name}' not found"
