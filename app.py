"""
SEC Financial Chatbot - Streamlit Frontend with Session Persistence

Layout:
- Left: Conversation history + Document upload
- Center: Chat interface (works with or without documents)
- Right: Running agents, plans, web search results

Configuration: API key and model are read from .env file only.
Settings UI in the frontend only for API base URL override.
"""

import datetime
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

import streamlit as st
import requests

ROOT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = ROOT_DIR / "backend"
# Add backend so `finchat_backend` can be imported as a package.
if BACKEND_DIR.exists() and str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Load environment variables from .env file
load_dotenv()

# Configure logging
from finchat_backend.agent_service.utils.logger import get_logger, configure_root_logger

configure_root_logger()
logger = get_logger(__name__)

from finchat_backend.agent_service.utils.file_utils import ensure_data_directory

# Page configuration
st.set_page_config(
    page_title="Financial Statement Chatbot", page_icon="📊", layout="wide"
)

# Custom CSS for better layout
st.markdown("""
<style>
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .stColumn > div {
        height: 100%;
    }
    .persisted-indicator {
        color: #10b981;
        font-size: 0.8em;
    }
    .not-persisted-indicator {
        color: #ef4444;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

# Backend API configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_doc" not in st.session_state:
    st.session_state.current_doc = None
if "doc_source" not in st.session_state:
    st.session_state.doc_source = None
if "running_agents" not in st.session_state:
    st.session_state.running_agents = []
if "active_plans" not in st.session_state:
    st.session_state.active_plans = []
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "conversation_sessions" not in st.session_state:
    st.session_state.conversation_sessions = []
if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = None

# ------------------ Backend API Client Functions ------------------

def api_request(method: str, endpoint: str, **kwargs):
    """Make an API request to the backend."""
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API request failed: {method} {url} - {e}")
        response = getattr(e, "response", None)
        if response is not None:
            try:
                payload = response.json()
                detail = payload.get("detail")
                if detail:
                    raise RuntimeError(detail) from e
            except ValueError:
                pass
        raise


def format_chat_error_message(error: Exception) -> str:
    """Convert backend/chat errors into a user-facing assistant message."""
    message = str(error).strip()
    if not message:
        return "暂时无法完成这次请求，请稍后重试。"

    return (
        "暂时无法完成这次请求。\n\n"
        f"原因：{message}\n\n"
        "如果这是配置问题，请检查后端服务和 `.env` 中的 `OPENROUTER_API_KEY`。"
    )


def api_health():
    """Check whether the backend is reachable."""
    return api_request("GET", "/api/health")

def api_list_sessions():
    """Fetch all sessions from backend (both in-memory and persisted)."""
    return api_request("GET", "/api/v1/sessions")

def api_save_session(session_id: str):
    """Save a session to disk via backend."""
    return api_request("POST", f"/api/v1/sessions/{session_id}/persist")

def api_delete_persisted_session(session_id: str):
    """Delete a persisted session."""
    return api_request("DELETE", f"/api/v1/persisted-sessions/{session_id}")

def api_get_session_detail(session_id: str):
    """Get detailed info for a specific session."""
    return api_request("GET", f"/api/v1/sessions/{session_id}")


def api_chat(session_id: str, message: str):
    """Send a chat message through the backend session runtime."""
    return api_request(
        "POST",
        "/api/v1/chat",
        json={"session_id": session_id, "message": message},
    )


def api_upload_document(session_id: str, uploaded_file):
    """Upload a document through the backend."""
    file_bytes = uploaded_file.getvalue()
    return api_request(
        "POST",
        "/api/v1/upload",
        data={"session_id": session_id},
        files={
            "file": (
                uploaded_file.name,
                file_bytes,
                uploaded_file.type or "application/octet-stream",
            )
        },
    )


def api_clear_document(session_id: str):
    """Clear the current document from the backend session."""
    return api_request("DELETE", f"/api/v1/sessions/{session_id}/document")


def api_clear_history(session_id: str):
    """Clear chat history for the current backend session."""
    return api_request("DELETE", f"/api/v1/sessions/{session_id}/history")


def api_analyze_document(session_id: str):
    """Run financial analysis for the current backend session."""
    return api_request("POST", f"/api/v1/sessions/{session_id}/analyze")


def api_search_document(session_id: str, query: str):
    """Search the current backend session document."""
    return api_request(
        "POST",
        f"/api/v1/sessions/{session_id}/search",
        json={"query": query},
    )


# ------------------ Session Management Functions ------------------

def refresh_sessions_from_backend():
    """Refresh the session list from the backend."""
    try:
        sessions = api_list_sessions()
        st.session_state.conversation_sessions = sessions
    except Exception as e:
        st.error(f"Failed to fetch sessions: {e}")


def hydrate_local_session(detail: Dict[str, Any]) -> None:
    """Restore Streamlit state from a backend session."""
    messages = detail.get("messages", [])
    document_content = detail.get("document_content")
    doc_source = detail.get("doc_source")

    st.session_state.messages = messages
    st.session_state.doc_source = doc_source
    st.session_state.current_doc = document_content

def start_new_session():
    """Start a new conversation session."""
    # Save current session first if it has messages
    if st.session_state.current_session_id and st.session_state.messages:
        try:
            api_save_session(st.session_state.current_session_id)
        except Exception as e:
            logger.warning(f"Auto-save before new session failed: {e}")

    # Create a new session via backend
    try:
        new_sess = api_request("POST", "/api/v1/sessions")
        session_id = new_sess["id"]
    except Exception as e:
        st.error(f"Failed to create new session: {e}")
        return

    st.session_state.current_session_id = session_id
    st.session_state.messages = []
    st.session_state.current_doc = None
    st.session_state.doc_source = None
    # Refresh the session list
    refresh_sessions_from_backend()
    st.rerun()

def switch_to_session(session_id: str):
    """Switch to a different session."""
    # Save current session before switching
    if st.session_state.current_session_id and st.session_state.messages:
        try:
            api_save_session(st.session_state.current_session_id)
        except Exception as e:
            logger.warning(f"Auto-save before session switch failed: {e}")

    try:
        detail = api_get_session_detail(session_id)
        st.session_state.current_session_id = session_id
        hydrate_local_session(detail)
        st.rerun()
    except Exception as e:
        st.error(f"Failed to load session: {e}")

def delete_current_session():
    """Delete the current session."""
    if not st.session_state.current_session_id:
        return

    session_id = st.session_state.current_session_id
    try:
        api_request("DELETE", f"/api/v1/sessions/{session_id}")
        # Also try to delete from persistence
        try:
            api_delete_persisted_session(session_id)
        except:
            pass
    except Exception as e:
        st.error(f"Failed to delete session: {e}")
        return

    # Clear current
    st.session_state.current_session_id = None
    st.session_state.messages = []
    st.session_state.current_doc = None
    st.session_state.doc_source = None
    # Refresh sessions
    refresh_sessions_from_backend()
    # Start new session
    start_new_session()

def auto_save_after_message():
    """Automatically save session after each message exchange."""
    if st.session_state.current_session_id:
        try:
            api_save_session(st.session_state.current_session_id)
            logger.debug(f"Auto-saved session {st.session_state.current_session_id}")
        except Exception as e:
            logger.warning(f"Auto-save failed: {e}")

def load_most_recent_session_or_create_new():
    """On first startup, load most recent persisted session or create new."""
    if st.session_state.conversation_sessions:
        # Pick the most recent session (first in list, sorted by backend)
        most_recent = st.session_state.conversation_sessions[0]
        session_id = most_recent["id"]
        try:
            detail = api_get_session_detail(session_id)
            st.session_state.current_session_id = session_id
            hydrate_local_session(detail)
            logger.info(f"Auto-loaded session: {session_id}")
            return
        except Exception as e:
            logger.warning(f"Failed to load most recent session: {e}")
            # Fall through to create new

    # No sessions available or load failed, create a new one
    start_new_session()

def ensure_fresh_sessions():
    """Ensure we have fresh session data from backend."""
    refresh_sessions_from_backend()

# ------------------ Main Application ------------------

def main():
    """Main application entry point."""
    try:
        ensure_data_directory()

        try:
            api_health()
        except Exception as e:
            st.warning(
                "⚠️ Backend unavailable. Start the FastAPI backend and verify its environment configuration."
            )
            st.info(f"Backend check failed: {e}")
            return

        # Always refresh sessions list from backend to keep UI up-to-date
        refresh_sessions_from_backend()

        # If no current session, load most recent persisted or create new
        if st.session_state.current_session_id is None:
            load_most_recent_session_or_create_new()

        # Ensure we have current messages loaded
        if st.session_state.current_session_id:
            try:
                detail = api_get_session_detail(st.session_state.current_session_id)
                if (
                    not st.session_state.messages
                    or (
                        st.session_state.current_doc is None
                        and detail.get("document_content") is not None
                    )
                ):
                    hydrate_local_session(detail)
            except Exception as e:
                logger.warning(f"Could not sync current session: {e}")

        # Create main layout with columns
        col_left, col_mid, col_right = st.columns([1, 2, 1])

        with col_left:
            render_conversation_history()
            st.divider()
            render_upload_section()

        with col_mid:
            render_chat_interface()

        with col_right:
            render_right_panel()

    except Exception as e:
        logger.error("Application error", exc_info=True)
        st.error(f"An unexpected error occurred: {e}")

    # Footer
    st.divider()
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.caption(
            "Powered by OpenRouter | Data stored locally | Sessions auto-saved"
        )

# ------------------ UI Rendering Functions ------------------

def render_conversation_history():
    """Render conversation history panel with sessions."""
    st.subheader("💬 History")

    # Show loading indicator if needed
    if not st.session_state.conversation_sessions:
        if st.button("🔄 Refresh", key="refresh_sessions_btn"):
            ensure_fresh_sessions()
            st.rerun()
        st.info("No conversation history.")
        return

    # New conversation button
    if st.button("➕ New Chat", use_container_width=True, type="primary", key="new_chat_btn"):
        if st.session_state.messages:
            # Check if current session is persisted
            current_sess = next((s for s in st.session_state.conversation_sessions if s["id"] == st.session_state.current_session_id), None)
            is_persisted = current_sess.get("persisted", False) if current_sess else False
            if not is_persisted:
                st.info("Current session will be saved before starting new chat.")
        start_new_session()
        st.rerun()

    # Display conversation sessions
    st.markdown("---")
    for session in st.session_state.conversation_sessions:
        session_id = session["id"]
        is_current = session_id == st.session_state.current_session_id
        is_persisted = session.get("persisted", False)

        # Create a title from the session
        title = session.get("title", "Untitled")
        if len(title) > 30:
            title = title[:30] + "..."

        # Format timestamp
        if isinstance(session.get("timestamp"), str):
            try:
                dt = datetime.datetime.fromisoformat(session["timestamp"])
                time_str = dt.strftime("%m/%d %H:%M")
            except:
                time_str = "Unknown"
        else:
            time_str = session.get("timestamp", datetime.datetime.now()).strftime("%m/%d %H:%M") if session.get("timestamp") else "Now"

        # Create expandable session card
        status_icon = "✅" if is_persisted else "🔄"
        current_marker = "🟢" if is_current else "  "
        label = f"{current_marker} {title}"
        expander_title = f"{label} · {time_str} · {session.get('message_count', 0)} msgs {status_icon}"

        with st.expander(expander_title, expanded=is_current):
            if session.get("doc_source"):
                st.caption(f"📄 {session['doc_source']}")

            # Show message preview
            msgs = session.get("messages", [])
            if msgs:
                st.markdown("**Preview:**")
                for msg in msgs[-3:]:  # Show last 3 messages
                    role_icon = "👤" if msg["role"] == "user" else "🤖"
                    content = msg["content"][:80] + ("..." if len(msg["content"]) > 80 else "")
                    st.markdown(f"{role_icon} {content}")
            else:
                st.markdown("*No messages*")

            # Action buttons
            col_load, col_delete = st.columns(2)
            with col_load:
                if not is_current:
                    if st.button(f"📂 Load", key=f"load_{session_id}", use_container_width=True):
                        switch_to_session(session_id)
                        st.rerun()
                else:
                    st.markdown("*Currently active*")

            with col_delete:
                if st.button(f"🗑️ Delete", key=f"delete_{session_id}", use_container_width=True):
                    if is_current:
                        # Need to switch to another session or create new
                        st.session_state.confirm_delete_current = True
                    else:
                        # Delete remote session
                        try:
                            api_request("DELETE", f"/api/v1/sessions/{session_id}")
                            try:
                                api_delete_persisted_session(session_id)
                            except:
                                pass
                            st.success(f"Deleted session")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {e}")

            # Show persistence status
            if is_current and not is_persisted and st.session_state.messages:
                st.caption("⚠️ Not saved to disk. Will auto-save on next action.")
            elif is_persisted:
                st.caption("✅ Saved to disk")

            # Handle delete confirmation for current session
            if is_current and st.session_state.get("confirm_delete_current"):
                st.warning("⚠️ Delete current session? This cannot be undone.")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("Yes, Delete", type="primary", key=f"confirm_del_yes_{session_id}"):
                        delete_current_session()
                        st.session_state.confirm_delete_current = False
                        st.rerun()
                with col_no:
                    if st.button("Cancel", key=f"confirm_del_no_{session_id}"):
                        st.session_state.confirm_delete_current = False
                        st.rerun()

def render_upload_section():
    """Render document upload section (only file upload, no SEC download)."""
    st.subheader("📁 Upload")

    # Upload section only
    uploaded_file = st.file_uploader(
        "Upload financial document",
        type=["txt", "pdf", "htm", "html"],
        help="Supports .txt, .pdf, .htm, .html files",
    )

    if uploaded_file is not None:
        if st.button(
            "📥 Load Document", type="primary", use_container_width=True, key="load_doc_btn"
        ):
            with st.spinner("Processing document..."):
                try:
                    api_upload_document(st.session_state.current_session_id, uploaded_file)
                    detail = api_get_session_detail(st.session_state.current_session_id)
                    hydrate_local_session(detail)
                    st.success(
                        f"Loaded {uploaded_file.name} ({len(st.session_state.current_doc or ''):,} chars)"
                    )
                    auto_save_after_message()
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to load document: {e}")

    # Clear document button
    if st.session_state.current_doc:
        st.divider()
        if st.button(
            "🗑️ Clear Doc", type="secondary", use_container_width=True, key="clear_doc_btn"
        ):
            try:
                api_clear_document(st.session_state.current_session_id)
                detail = api_get_session_detail(st.session_state.current_session_id)
                hydrate_local_session(detail)
                st.rerun()
            except Exception as e:
                st.error(f"Error clearing document: {e}")

    # Document info
    if st.session_state.doc_source:
        st.divider()
        st.subheader("📊 Current")
        st.info(st.session_state.doc_source)
        st.write(f"Size: {len(st.session_state.current_doc):,} chars")

        # Quick action buttons
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📈 Analysis", use_container_width=True, key="analysis_btn"):
                st.session_state.quick_analysis = True
                st.rerun()
        with col2:
            if st.button("🔍 Search", use_container_width=True, key="search_btn"):
                st.session_state.show_search = True
                st.rerun()

        # Search functionality
        if st.session_state.get("show_search", False):
            search_query = st.text_input("Search in doc", key="search_input")
            if search_query and st.button("Search", key="exec_search_btn"):
                with st.spinner("Searching..."):
                    try:
                        result = api_search_document(
                            st.session_state.current_session_id,
                            search_query,
                        )
                        st.text_area("Results", result["result"], height=200)
                    except Exception as e:
                        st.error(f"Search error: {e}")

def render_right_panel():
    """Render right panel with running agents, plans, and search results."""
    st.subheader("🤖 Agents")

    # Running agents section
    if st.session_state.running_agents:
        for agent in st.session_state.running_agents:
            with st.expander(f"Agent: {agent.get('name', 'Unknown')}", expanded=True):
                st.write(f"Status: {agent.get('status', 'idle')}")
                st.write(f"Task: {agent.get('task', 'N/A')}")
                agent_key = f"stop_{agent.get('name', 'Unknown')}_{id(agent)}"
                if st.button(f"Stop {agent.get('name')}", key=agent_key):
                    st.session_state.running_agents.remove(agent)
                    st.rerun()
    else:
        st.info("No agents running.")

    st.divider()

    st.subheader("📋 Plans")

    # Plans section
    if st.session_state.active_plans:
        for plan in st.session_state.active_plans:
            with st.expander(f"Plan: {plan.get('name', 'Untitled')}", expanded=False):
                st.write(f"Status: {plan.get('status', 'pending')}")
                steps = plan.get('steps', [])
                if steps:
                    st.write("Steps:")
                    for i, step in enumerate(steps, 1):
                        st.write(f"{i}. {step}")
                plan_key = f"complete_{plan.get('name', 'Untitled')}_{id(plan)}"
                if st.button(f"Complete {plan.get('name')}", key=plan_key):
                    plan['status'] = 'completed'
                    st.rerun()
    else:
        st.info("No active plans.")

    st.divider()

    st.subheader("🔍 Search Results")

    # Web search results section
    if st.session_state.search_results:
        for result in st.session_state.search_results[-5:]:  # Show last 5
            with st.expander(f"Query: {result.get('query', 'Unknown')}", expanded=False):
                st.write(f"Time: {result.get('time', 'N/A')}")
                results_list = result.get('results', [])
                if results_list:
                    for r in results_list[:3]:  # Show top 3 results per query
                        st.markdown(f"- [{r.get('title', 'No title')}]({r.get('url', '#')})")
                        st.caption(r.get('snippet', '')[:100] + "...")
    else:
        st.info("No recent searches.")

def render_chat_interface():
    """Render the main chat interface."""
    st.title("📊 FinChat")

    # Messages container (scrollable)
    message_container = st.container()

    # Display chat messages in container
    with message_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Quick analysis feature (only if document loaded)
        if st.session_state.get("quick_analysis", False):
            if not st.session_state.current_doc:
                st.warning("Quick analysis requires a loaded document.")
                st.session_state.quick_analysis = False
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing financials..."):
                        try:
                            response = api_analyze_document(
                                st.session_state.current_session_id
                            )["response"]
                            st.markdown(response)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": response}
                            )
                        except Exception as e:
                            st.error(f"Analysis error: {e}")
                            logger.error("Quick analysis failed", exc_info=True)
                st.session_state.quick_analysis = False

        # Welcome message for first-time users
        if not st.session_state.messages and not st.session_state.current_doc:
            with st.chat_message("assistant"):
                st.info(
                    "👋 Hello! I'm your financial analysis assistant. You can upload a financial document to analyze, or just ask me general financial questions."
                )

    # Bottom input bar with divider
    st.markdown("---")
    st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

    # Create columns for input and clear button
    col_input, col_btn = st.columns([4, 1])

    with col_input:
        prompt = st.chat_input(
            "Type your message...",
            key="chat_input_main"
        )

    with col_btn:
        st.write("")  # Vertical spacing
        st.write("")
        if st.button("🗑️ Clear", use_container_width=True, type="secondary", key="clear_chat_btn"):
            if st.session_state.current_session_id:
                try:
                    api_clear_history(st.session_state.current_session_id)
                    detail = api_get_session_detail(st.session_state.current_session_id)
                    hydrate_local_session(detail)
                except Exception as e:
                    st.error(f"Failed to clear chat: {e}")
            st.rerun()

    if prompt:
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with message_container:
            with st.chat_message("user"):
                st.markdown(prompt)

        # Generate response
        with message_container:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    try:
                        response = api_chat(
                            st.session_state.current_session_id,
                            prompt,
                        )["response"]
                        st.markdown(response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )
                    except Exception as e:
                        error_message = format_chat_error_message(e)
                        st.markdown(error_message)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": error_message}
                        )
                        logger.error("Chat error", exc_info=True)

        # Auto-save after message
        auto_save_after_message()

        # Auto-rerun to update UI
        st.rerun()


if __name__ == "__main__":
    main()
