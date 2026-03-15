import axios from 'axios';
import type {
  Session,
  Message,
  UploadResponse,
  ChatResponse,
  AnalyzeResponse,
  SearchResponse,
  HealthCheck,
} from '@/types';
export { extractApiErrorMessage } from './error';

const getApiBaseUrl = (): string => {
  // Vite development/build uses import.meta.env
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  // Fallback for other environments (tests, etc.)
  if (typeof process !== 'undefined' && process.env?.VITE_API_BASE_URL) {
    return process.env.VITE_API_BASE_URL;
  }
  return 'http://localhost:8000';
};

const API_BASE_URL = getApiBaseUrl();

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request/Response interceptors for logging and error handling
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(
        `API Error: ${error.response.status} - ${JSON.stringify(error.response.data)}`
      );
    } else if (error.request) {
      console.error('API Error: No response received');
    } else {
      console.error('API Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// Health check
export async function healthCheck(): Promise<HealthCheck> {
  const response = await api.get<HealthCheck>('/api/health');
  return response.data;
}

// Session management
export async function listSessions(): Promise<Session[]> {
  const response = await api.get<Session[]>('/api/v1/sessions');
  return response.data;
}

export async function createSession(): Promise<Session> {
  const response = await api.post<Session>('/api/v1/sessions');
  return response.data;
}

export async function getSessionDetail(sessionId: string): Promise<Session> {
  const response = await api.get<Session>(`/api/v1/sessions/${sessionId}`);
  return response.data;
}

export async function updateSessionState(
  sessionId: string,
  messages: Message[],
  docSource?: string,
  documentContent?: string,
  persist: boolean = true
): Promise<Session> {
  const response = await api.put<Session>(`/api/v1/sessions/${sessionId}`, {
    messages,
    doc_source: docSource,
    document_content: documentContent,
    persist,
  });
  return response.data;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await api.delete(`/api/v1/sessions/${sessionId}`);
}

export async function resetSession(sessionId: string): Promise<void> {
  await api.post(`/api/v1/sessions/${sessionId}/reset`);
}

export async function listPersistedSessions(): Promise<Session[]> {
  const response = await api.get<Session[]>('/api/v1/persisted-sessions');
  return response.data;
}

export async function persistSession(sessionId: string): Promise<{ status: string }> {
  const response = await api.post(`/api/v1/sessions/${sessionId}/persist`);
  return response.data;
}

export async function loadPersistedSession(sessionId: string): Promise<{ status: string }> {
  const response = await api.post(`/api/v1/persisted-sessions/${sessionId}/load`);
  return response.data;
}

export async function deletePersistedSession(sessionId: string): Promise<void> {
  await api.delete(`/api/v1/persisted-sessions/${sessionId}`);
}

// Chat functionality
export async function sendChatMessage(
  sessionId: string,
  message: string
): Promise<ChatResponse> {
  const response = await api.post<ChatResponse>('/api/v1/chat', {
    session_id: sessionId,
    message,
  });
  return response.data;
}

export async function analyzeDocument(sessionId: string): Promise<AnalyzeResponse> {
  const response = await api.post<AnalyzeResponse>(`/api/v1/sessions/${sessionId}/analyze`);
  return response.data;
}

export async function searchDocument(
  sessionId: string,
  query: string
): Promise<SearchResponse> {
  const response = await api.post<SearchResponse>(
    `/api/v1/sessions/${sessionId}/search`,
    { query }
  );
  return response.data;
}

export async function getSessionHistory(sessionId: string): Promise<{ messages: Message[] }> {
  const response = await api.get(`/api/v1/sessions/${sessionId}/history`);
  return response.data;
}

export async function clearSessionHistory(sessionId: string): Promise<void> {
  await api.delete(`/api/v1/sessions/${sessionId}/history`);
}

// File upload
export async function uploadDocument(
  sessionId: string,
  file: File
): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('session_id', sessionId);
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/api/v1/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
}

export async function clearDocument(sessionId: string): Promise<void> {
  await api.delete(`/api/v1/sessions/${sessionId}/document`);
}

export default api;
