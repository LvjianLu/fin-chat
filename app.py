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
import logging
import sys
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

import streamlit as st
import requests

ROOT_DIR = Path(__file__).resolve().parent
FINCHAT_BACKEND_DIR = ROOT_DIR / "backend" / "finchat_backend"
if FINCHAT_BACKEND_DIR.exists():
    sys.path.insert(0, str(FINCHAT_BACKEND_DIR))

# Load environment variables from .env file
load_dotenv()

# Configure logging
from agent_service.utils.logger import get_logger, configure_root_logger

configure_root_logger()
logger = get_logger(__name__)

# Import from agent framework
from agent_service.config import load_settings_from_dict
from agent_service.agent.agent import FinChat
from agent_service.agent.llm.openrouter import OpenRouterLLM
from agent_service.agent.memory import ConversationMemory
from agent_service.agent.tools import (
    SearchTool,
    FinAnalysisTool,
)
from agent_service.utils.file_utils import ensure_data_directory
from agent_service.utils.validators import validate_api_key

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
if "finchat" not in st.session_state:
    st.session_state.finchat = None
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
        raise

def api_list_sessions():
    """Fetch all sessions from backend (both in-memory and persisted)."""
    return api_request("GET", "/api/v1/sessions")

def api_list_persisted_sessions():
    """Fetch all persisted sessions from backend."""
    return api_request("GET", "/api/v1/persisted-sessions")

def api_save_session(session_id: str):
    """Save a session to disk via backend."""
    return api_request("POST", f"/api/v1/sessions/{session_id}/persist")

def api_load_persisted_session(session_id: str):
    """Load a persisted session into memory via backend."""
    return api_request("POST", f"/api/v1/persisted-sessions/{session_id}/load")

def api_delete_persisted_session(session_id: str):
    """Delete a persisted session."""
    return api_request("DELETE", f"/api/v1/persisted-sessions/{session_id}")

def api_get_session_detail(session_id: str):
    """Get detailed info for a specific session."""
    return api_request("GET", f"/api/v1/sessions/{session_id}")


def api_sync_session(
    session_id: str,
    messages: List[Dict[str, str]],
    doc_source: Optional[str] = None,
    document_content: Optional[str] = None,
    persist: bool = True,
):
    """Sync the current local session state into the backend."""
    payload = {
        "messages": messages,
        "doc_source": doc_source,
        "document_content": document_content,
        "persist": persist,
    }
    return api_request("PUT", f"/api/v1/sessions/{session_id}", json=payload)

# ------------------ Session Management Functions ------------------

def refresh_sessions_from_backend():
    """Refresh the session list from the backend."""
    try:
        sessions = api_list_sessions()
        st.session_state.conversation_sessions = sessions
    except Exception as e:
        st.error(f"Failed to fetch sessions: {e}")


def build_local_finchat(
    messages: Optional[List[Dict[str, str]]] = None,
    document_content: Optional[str] = None,
    doc_source: Optional[str] = None,
):
    """Build a local FinChat runtime and optionally hydrate it."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.warning("OPENROUTER_API_KEY not found in environment")
        return None

    model = os.getenv("OPENROUTER_MODEL", "stepfun/step-3.5-flash:free")
    validated_key = validate_api_key(api_key)
    settings = load_settings_from_dict(
        {
            "openrouter_api_key": validated_key,
            "openrouter_model": model,
        }
    )

    llm = OpenRouterLLM(settings)
    memory = ConversationMemory()
    if document_content:
        memory.set_document(document_content, doc_source or "Restored document")
    for message in messages or []:
        memory.add_message(message["role"], message["content"])

    tools = [
        SearchTool(memory),
        FinAnalysisTool(llm),
    ]
    return FinChat(tools=tools, llm=llm, memory=memory)


def hydrate_local_session(detail: Dict[str, Any]) -> None:
    """Restore Streamlit state and local agent from a backend session."""
    messages = detail.get("messages", [])
    document_content = detail.get("document_content")
    doc_source = detail.get("doc_source")

    st.session_state.messages = messages
    st.session_state.doc_source = doc_source
    st.session_state.current_doc = document_content
    st.session_state.finchat = build_local_finchat(
        messages=messages,
        document_content=document_content,
        doc_source=doc_source,
    )

def sync_current_session_to_backend():
    """Save current session to backend persistence."""
    if not st.session_state.current_session_id:
        return False
    try:
        result = api_sync_session(
            st.session_state.current_session_id,
            messages=st.session_state.messages,
            doc_source=st.session_state.doc_source,
            document_content=st.session_state.current_doc,
            persist=True,
        )
        logger.info(f"Auto-saved session {st.session_state.current_session_id}")
        # Optimistically update persisted flag in local sessions list
        for sess in st.session_state.conversation_sessions:
            if sess["id"] == st.session_state.current_session_id:
                sess["persisted"] = True
                sess["message_count"] = len(st.session_state.messages)
                sess["doc_source"] = st.session_state.doc_source
                if st.session_state.messages:
                    first_user_msg = next(
                        (
                            msg["content"]
                            for msg in st.session_state.messages
                            if msg["role"] == "user"
                        ),
                        "New Chat",
                    )
                    sess["title"] = (
                        first_user_msg[:30] + "..."
                        if len(first_user_msg) > 30
                        else first_user_msg
                    )
                break
        return True
    except Exception as e:
        logger.warning(f"Auto-save failed: {e}")
        return False

def load_session_from_backend(session_id: str):
    """Load a saved session into current workspace."""
    try:
        result = api_load_persisted_session(session_id)
        # Refresh session list
        refresh_sessions_from_backend()
        # Set current session
        st.session_state.current_session_id = session_id
        detail = api_get_session_detail(session_id)
        hydrate_local_session(detail)
        st.rerun()
        return True
    except Exception as e:
        st.error(f"Failed to load session: {e}")
        return False

def start_new_session():
    """Start a new conversation session."""
    # Save current session first if it has messages
    if st.session_state.current_session_id and st.session_state.messages:
        sync_current_session_to_backend()

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
        sync_current_session_to_backend()

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
        success = sync_current_session_to_backend()
        if success:
            logger.debug(f"Auto-saved session {st.session_state.current_session_id}")

# ------------------ Initialization ------------------

def init_finchat_from_env() -> None:
    """Initialize the FinChat agent from environment variables."""
    if st.session_state.finchat is not None:
        return

    try:
        st.session_state.finchat = build_local_finchat()
        logger.info("FinChat initialized from environment")
    except Exception as e:
        logger.error("FinChat initialization from env failed", exc_info=True)
        st.session_state.finchat = None

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

        # Try to auto-initialize from .env
        init_finchat_from_env()

        if not st.session_state.finchat:
            st.warning(
                "⚠️ **Configuration Required**\\n\\n"
                "The chatbot is not configured. Please set the following environment variables:\\n\\n"
                "- `OPENROUTER_API_KEY`: Your OpenRouter API key\\n"
                "- `OPENROUTER_MODEL` (optional): Model to use (default: stepfun/step-3.5-flash:free)\\n\\n"
                "You can set these in a `.env` file in the project root."
            )
            st.info("Once configured, restart the app to load the settings.")
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
                    or st.session_state.finchat is None
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

    if not st.session_state.finchat:
        st.warning("⚠️ FinChat not initialized")
        return

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
                content = process_uploaded_file(uploaded_file)
                if content:
                    st.session_state.current_doc = content
                    st.session_state.doc_source = (
                        f"Uploaded: {uploaded_file.name}"
                    )
                    try:
                        st.session_state.finchat.load_document(
                            content, f"Uploaded file: {uploaded_file.name}"
                        )
                        st.success(
                            f"Loaded {uploaded_file.name} ({len(content):,} chars)"
                        )
                        # Save session after loading doc
                        if st.session_state.current_session_id:
                            sync_current_session_to_backend()
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to load document: {e}")

    # Clear document button
    if st.session_state.finchat and st.session_state.finchat.has_document():
        st.divider()
        if st.button(
            "🗑️ Clear Doc", type="secondary", use_container_width=True, key="clear_doc_btn"
        ):
            try:
                st.session_state.finchat.clear_document()
                st.session_state.current_doc = None
                st.session_state.doc_source = None
                # Also clear from current session
                if st.session_state.current_session_id:
                    sync_current_session_to_backend()
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
                        result = st.session_state.finchat.search_document(
                            search_query
                        )
                        st.text_area("Results", result.format_results(), height=200)
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
            if not st.session_state.finchat.has_document():
                st.warning("Quick analysis requires a loaded document.")
                st.session_state.quick_analysis = False
            else:
                with st.chat_message("assistant"):
                    with st.spinner("Analyzing financials..."):
                        try:
                            response = st.session_state.finchat.analyze_financials()
                            st.markdown(response)
                            st.session_state.messages.append(
                                {"role": "assistant", "content": response}
                            )
                        except Exception as e:
                            st.error(f"Analysis error: {e}")
                            logger.error("Quick analysis failed", exc_info=True)
                st.session_state.quick_analysis = False

        # Welcome message for first-time users
        if not st.session_state.messages and not st.session_state.finchat.has_document():
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
            # Clear current session's messages in place
            st.session_state.messages.clear()
            # Also clear agent memory
            if st.session_state.finchat:
                try:
                    st.session_state.finchat.memory.clear_history()
                except:
                    pass
            # Save cleared session
            if st.session_state.current_session_id:
                sync_current_session_to_backend()
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
                        response = st.session_state.finchat.chat(prompt)
                        st.markdown(response)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": response}
                        )
                    except Exception as e:
                        st.error(f"Error: {e}")
                        logger.error("Chat error", exc_info=True)

        # Auto-save after message
        auto_save_after_message()

        # Auto-rerun to update UI
        st.rerun()

def process_uploaded_file(uploaded_file):
    """Process uploaded file and extract text."""
    try:
        if uploaded_file.type == "text/plain" or uploaded_file.name.endswith(".txt"):
            content = str(uploaded_file.read(), "utf-8")
        elif uploaded_file.name.endswith(".pdf"):
            import PyPDF2
            import pdfplumber

            # Try PyPDF2 first, fallback to pdfplumber
            try:
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                content = ""
                for page in pdf_reader.pages:
                    content += page.extract_text() + "\n"
            except:
                with pdfplumber.open(uploaded_file) as pdf:
                    content = ""
                    for page in pdf.pages:
                        content += page.extract_text() + "\n"
        elif uploaded_file.name.endswith((".htm", "html")):
            from bs4 import BeautifulSoup

            content = str(uploaded_file.read(), "utf-8")
            soup = BeautifulSoup(content, "lxml")
            content = soup.get_text()
            content = " ".join(content.split())
        else:
            st.error("Unsupported file type")
            return None

        return content
    except Exception as e:
        st.error(f"Error processing file: {e}")
        logger.error(
            "File processing error", exc_info=True, extra={"file": uploaded_file.name}
        )
        return None


if __name__ == "__main__":
    main()
