import React, { createContext, useContext, useReducer, useEffect, ReactNode } from 'react';
import type { Session, Message, Agent, Plan, SearchResult } from '@/types';
import * as api from '@/services/api';
import { extractApiErrorMessage } from '@/services/error';

interface AppState {
  // Current session
  currentSessionId: string | null;
  messages: Message[];
  currentDoc: string | null;
  docSource: string | null;

  // Sessions list
  conversationSessions: Session[];

  // Right panel state
  runningAgents: Agent[];
  activePlans: Plan[];
  searchResults: SearchResult[];

  // UI state
  quickAnalysis: boolean;
  showSearch: boolean;
  confirmDeleteCurrent: boolean;

  // Loading states
  isLoading: boolean;
  error: string | null;
}

type Action =
  | { type: 'SET_CURRENT_SESSION'; payload: string | null }
  | { type: 'SET_MESSAGES'; payload: Message[] }
  | { type: 'ADD_MESSAGE'; payload: Message }
  | { type: 'SET_CURRENT_DOC'; payload: string | null }
  | { type: 'SET_DOC_SOURCE'; payload: string | null }
  | { type: 'SET_CONVERSATION_SESSIONS'; payload: Session[] }
  | { type: 'ADD_SESSION'; payload: Session }
  | { type: 'UPDATE_SESSION'; payload: Session }
  | { type: 'REMOVE_SESSION'; payload: string }
  | { type: 'SET_RUNNING_AGENTS'; payload: Agent[] }
  | { type: 'ADD_AGENT'; payload: Agent }
  | { type: 'REMOVE_AGENT'; payload: string }
  | { type: 'SET_ACTIVE_PLANS'; payload: Plan[] }
  | { type: 'ADD_PLAN'; payload: Plan }
  | { type: 'UPDATE_PLAN'; payload: { id: string; updates: Partial<Plan> } }
  | { type: 'SET_SEARCH_RESULTS'; payload: SearchResult[] }
  | { type: 'ADD_SEARCH_RESULT'; payload: SearchResult }
  | { type: 'SET_QUICK_ANALYSIS'; payload: boolean }
  | { type: 'SET_SHOW_SEARCH'; payload: boolean }
  | { type: 'SET_CONFIRM_DELETE_CURRENT'; payload: boolean }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'RESET_STATE' };

const initialState: AppState = {
  currentSessionId: null,
  messages: [],
  currentDoc: null,
  docSource: null,
  conversationSessions: [],
  runningAgents: [],
  activePlans: [],
  searchResults: [],
  quickAnalysis: false,
  showSearch: false,
  confirmDeleteCurrent: false,
  isLoading: false,
  error: null,
};

function appReducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSessionId: action.payload };
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload };
    case 'ADD_MESSAGE':
      return { ...state, messages: [...state.messages, action.payload] };
    case 'SET_CURRENT_DOC':
      return { ...state, currentDoc: action.payload };
    case 'SET_DOC_SOURCE':
      return { ...state, docSource: action.payload };
    case 'SET_CONVERSATION_SESSIONS':
      return { ...state, conversationSessions: action.payload };
    case 'ADD_SESSION':
      return { ...state, conversationSessions: [action.payload, ...state.conversationSessions] };
    case 'UPDATE_SESSION':
      return {
        ...state,
        conversationSessions: state.conversationSessions.map((s) =>
          s.id === action.payload.id ? action.payload : s
        ),
      };
    case 'REMOVE_SESSION':
      return {
        ...state,
        conversationSessions: state.conversationSessions.filter((s) => s.id !== action.payload),
      };
    case 'SET_RUNNING_AGENTS':
      return { ...state, runningAgents: action.payload };
    case 'ADD_AGENT':
      return { ...state, runningAgents: [...state.runningAgents, action.payload] };
    case 'REMOVE_AGENT':
      return {
        ...state,
        runningAgents: state.runningAgents.filter((a) => a.id !== action.payload),
      };
    case 'SET_ACTIVE_PLANS':
      return { ...state, activePlans: action.payload };
    case 'ADD_PLAN':
      return { ...state, activePlans: [...state.activePlans, action.payload] };
    case 'UPDATE_PLAN':
      return {
        ...state,
        activePlans: state.activePlans.map((p) =>
          p.id === action.payload.id ? { ...p, ...action.payload.updates } : p
        ),
      };
    case 'SET_SEARCH_RESULTS':
      return { ...state, searchResults: action.payload };
    case 'ADD_SEARCH_RESULT':
      return { ...state, searchResults: [...state.searchResults, action.payload] };
    case 'SET_QUICK_ANALYSIS':
      return { ...state, quickAnalysis: action.payload };
    case 'SET_SHOW_SEARCH':
      return { ...state, showSearch: action.payload };
    case 'SET_CONFIRM_DELETE_CURRENT':
      return { ...state, confirmDeleteCurrent: action.payload };
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'RESET_STATE':
      return { ...initialState, currentSessionId: null };
    default:
      return state;
  }
}

interface AppContextType {
  state: AppState;
  dispatch: React.Dispatch<Action>;
  // Session actions
  refreshSessions: () => Promise<void>;
  startNewSession: () => Promise<void>;
  switchToSession: (sessionId: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;
  deleteCurrentSession: () => Promise<void>;
  // Message actions
  sendMessage: (content: string) => Promise<void>;
  clearHistory: () => Promise<void>;
  // Document actions
  uploadDocument: (file: File) => Promise<void>;
  clearDocument: () => Promise<void>;
  analyzeDocument: () => Promise<void>;
  searchDocument: (query: string) => Promise<string>;
  autoSave: () => Promise<void>;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// Generate unique IDs
function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // Load sessions on mount
  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      await api.healthCheck();
      await refreshSessions();

      // Load most recent session or create new
      if (state.conversationSessions.length > 0) {
        const mostRecent = state.conversationSessions[0];
        await switchToSession(mostRecent.id);
      } else {
        await startNewSession();
      }
    } catch (error) {
      console.error('Failed to initialize app:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Backend unavailable. Please start the backend server.' });
    }
  };

  const refreshSessions = async () => {
    try {
      const sessions = await api.listSessions();
      dispatch({ type: 'SET_CONVERSATION_SESSIONS', payload: sessions });
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const startNewSession = async () => {
    // Save current session if it has messages
    if (state.currentSessionId && state.messages.length > 0) {
      try {
        await autoSave();
      } catch (error) {
        console.warn('Auto-save before new session failed:', error);
      }
    }

    try {
      const newSession = await api.createSession();
      dispatch({ type: 'SET_CURRENT_SESSION', payload: newSession.id });
      dispatch({ type: 'SET_MESSAGES', payload: [] });
      dispatch({ type: 'SET_CURRENT_DOC', payload: null });
      dispatch({ type: 'SET_DOC_SOURCE', payload: null });
      dispatch({ type: 'ADD_SESSION', payload: newSession });
      await refreshSessions();
    } catch (error) {
      console.error('Failed to create session:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to create new session' });
    }
  };

  const switchToSession = async (sessionId: string) => {
    // Save current session before switching
    if (state.currentSessionId && state.messages.length > 0) {
      try {
        await autoSave();
      } catch (error) {
        console.warn('Auto-save before session switch failed:', error);
      }
    }

    try {
      const session = await api.getSessionDetail(sessionId);
      dispatch({ type: 'SET_CURRENT_SESSION', payload: sessionId });
      dispatch({
        type: 'SET_MESSAGES',
        payload: session.messages || [],
      });
      dispatch({ type: 'SET_CURRENT_DOC', payload: session.document_content || null });
      dispatch({ type: 'SET_DOC_SOURCE', payload: session.doc_source || null });
      await refreshSessions();
    } catch (error) {
      console.error('Failed to load session:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to load session' });
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      await api.deleteSession(sessionId);
      try {
        await api.deletePersistedSession(sessionId);
      } catch {
        // Ignore if not persisted
      }
      dispatch({ type: 'REMOVE_SESSION', payload: sessionId });

      if (state.currentSessionId === sessionId) {
        if (state.conversationSessions.length > 0) {
          const nextSession = state.conversationSessions.find((s) => s.id !== sessionId);
          if (nextSession) {
            await switchToSession(nextSession.id);
          } else {
            await startNewSession();
          }
        } else {
          await startNewSession();
        }
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to delete session' });
    }
  };

  const deleteCurrentSession = async () => {
    if (!state.currentSessionId) return;
    await deleteSession(state.currentSessionId);
  };

  const sendMessage = async (content: string) => {
    if (!state.currentSessionId) {
      dispatch({
        type: 'ADD_MESSAGE',
        payload: {
          id: generateId(),
          role: 'assistant',
          content: 'Error: No active session. Please create or reload a session and try again.',
          timestamp: new Date(),
        },
      });
      return;
    }

    const userMessage: Message = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    dispatch({ type: 'ADD_MESSAGE', payload: userMessage });
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await api.sendChatMessage(state.currentSessionId!, content);
      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });
      await autoSave();
    } catch (error: unknown) {
      const errorMessage = extractApiErrorMessage(error);
      const errorMsg: Message = {
        id: generateId(),
        role: 'assistant',
        content: `Error: ${errorMessage}`,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: errorMsg });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const clearHistory = async () => {
    if (!state.currentSessionId) return;
    try {
      await api.clearSessionHistory(state.currentSessionId);
      dispatch({ type: 'SET_MESSAGES', payload: [] });
      await refreshSessions();
    } catch (error) {
      console.error('Failed to clear history:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to clear chat history' });
    }
  };

  const uploadDocument = async (file: File) => {
    if (!state.currentSessionId) {
      dispatch({ type: 'SET_ERROR', payload: 'No active session' });
      return;
    }
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      await api.uploadDocument(state.currentSessionId, file);
      dispatch({ type: 'SET_DOC_SOURCE', payload: file.name });
      // After upload, reload session to get document content
      const session = await api.getSessionDetail(state.currentSessionId);
      dispatch({ type: 'SET_CURRENT_DOC', payload: session.document_content || null });
      dispatch({ type: 'SET_MESSAGES', payload: session.messages || state.messages });
      await autoSave();
    } catch (error: unknown) {
      const errorMessage = extractApiErrorMessage(error);
      dispatch({ type: 'SET_ERROR', payload: errorMessage });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  };

  const clearDocument = async () => {
    if (!state.currentSessionId) return;
    try {
      await api.clearDocument(state.currentSessionId);
      dispatch({ type: 'SET_CURRENT_DOC', payload: null });
      dispatch({ type: 'SET_DOC_SOURCE', payload: null });
      await refreshSessions();
    } catch (error) {
      console.error('Failed to clear document:', error);
      dispatch({ type: 'SET_ERROR', payload: 'Failed to clear document' });
    }
  };

  const analyzeDocument = async () => {
    if (!state.currentSessionId) return;
    dispatch({ type: 'SET_LOADING', payload: true });
    try {
      const response = await api.analyzeDocument(state.currentSessionId);
      const assistantMessage: Message = {
        id: generateId(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
      };
      dispatch({ type: 'ADD_MESSAGE', payload: assistantMessage });
      await autoSave();
    } catch (error: unknown) {
      const errorMessage = extractApiErrorMessage(error);
      dispatch({
        type: 'ADD_MESSAGE',
        payload: {
          id: generateId(),
          role: 'assistant',
          content: `Analysis error: ${errorMessage}`,
          timestamp: new Date(),
        },
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
      dispatch({ type: 'SET_QUICK_ANALYSIS', payload: false });
    }
  };

  const searchDocument = async (query: string): Promise<string> => {
    if (!state.currentSessionId) {
      throw new Error('No active session');
    }
    try {
      const response = await api.searchDocument(state.currentSessionId, query);
      return response.result;
    } catch (error: unknown) {
      const errorMessage = extractApiErrorMessage(error);
      throw new Error(errorMessage);
    }
  };

  const autoSave = async () => {
    if (!state.currentSessionId) return;
    try {
      await api.updateSessionState(
        state.currentSessionId,
        state.messages,
        state.docSource || undefined,
        state.currentDoc || undefined,
        true
      );
    } catch (error) {
      console.warn('Auto-save failed:', error);
    }
  };

  const value: AppContextType = {
    state,
    dispatch,
    refreshSessions,
    startNewSession,
    switchToSession,
    deleteSession,
    deleteCurrentSession,
    sendMessage,
    clearHistory,
    uploadDocument,
    clearDocument,
    analyzeDocument,
    searchDocument,
    autoSave,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
}

export function useAppState() {
  const context = useContext(AppContext);
  if (context === undefined) {
    throw new Error('useAppState must be used within an AppProvider');
  }
  return context;
}
