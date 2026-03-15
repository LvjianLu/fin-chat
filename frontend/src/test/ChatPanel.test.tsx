/// <reference types="jest" />
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ChatPanel from '../components/ChatPanel';
import { AppProvider } from '../hooks/useAppState';

jest.mock('@/services/api', () => ({
  healthCheck: jest.fn(),
  listSessions: jest.fn().mockResolvedValue([]),
  createSession: jest.fn().mockResolvedValue({
    id: 'session-1',
    title: 'New Chat',
    message_count: 0,
    timestamp: new Date().toISOString(),
    persisted: false,
  }),
  getSessionDetail: jest.fn().mockResolvedValue({
    id: 'session-1',
    messages: [],
    document_content: null,
    doc_source: null,
  }),
  updateSessionState: jest.fn(),
  sendChatMessage: jest.fn(),
  clearSessionHistory: jest.fn(),
  analyzeDocument: jest.fn(),
}));

const renderWithProvider = (component: React.ReactNode) => {
  return render(<AppProvider>{component}</AppProvider>);
};

describe('ChatPanel Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders welcome message when no messages', async () => {
    renderWithProvider(<ChatPanel />);

    await waitFor(() => {
      expect(screen.getByText(/Welcome to FinChat/i)).toBeInTheDocument();
    });
  });

  it('has a chat input', async () => {
    renderWithProvider(<ChatPanel />);

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/Type your message/i)).toBeInTheDocument();
    });
  });
});
