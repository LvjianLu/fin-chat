export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export interface Session {
  id: string;
  title: string;
  message_count: number;
  timestamp: Date;
  doc_source?: string;
  persisted: boolean;
  messages?: Message[];
  document_content?: string;
}

export interface Agent {
  id: string;
  name: string;
  status: 'running' | 'idle' | 'stopped' | 'completed' | 'failed';
  task?: string;
  progress?: number;
  started_at?: Date;
}

export interface Plan {
  id: string;
  name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  steps: PlanStep[];
  created_at: Date;
}

export interface PlanStep {
  id: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  result?: string;
}

export interface SearchResult {
  id: string;
  query: string;
  time: Date;
  results: WebSearchResult[];
}

export interface WebSearchResult {
  title: string;
  url: string;
  snippet: string;
}

export interface UploadResponse {
  success: boolean;
  message: string;
  session_id: string;
  char_count: number;
}

export interface ChatResponse {
  response: string;
  session_id: string;
}

export interface AnalyzeResponse {
  response: string;
  session_id: string;
}

export interface SearchResponse {
  result: string;
  session_id: string;
}

export interface HealthCheck {
  status: string;
  service: string;
}
