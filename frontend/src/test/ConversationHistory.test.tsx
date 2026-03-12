/// <reference types="jest" />
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import ConversationHistory from '../components/ConversationHistory';
import { AppProvider } from '../hooks/useAppState';

// Mock the API
jest.mock('@/services/api', () => ({
  healthCheck: jest.fn(),
  listSessions: jest.fn(),
  createSession: jest.fn(),
  getSessionDetail: jest.fn(),
  deleteSession: jest.fn(),
  deletePersistedSession: jest.fn(),
}));

import * as api from '../services/api';

const mockSessions = [
  {
    id: 'session-1',
    title: 'Test Session 1',
    message_count: 5,
    timestamp: new Date().toISOString(),
    persisted: true,
    messages: [
      { id: 'm1', role: 'user', content: 'Hello', timestamp: new Date() },
      { id: 'm2', role: 'assistant', content: 'Hi there!', timestamp: new Date() },
    ],
  },
  {
    id: 'session-2',
    title: 'Test Session 2',
    message_count: 3,
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    persisted: false,
    messages: [],
  },
];

const renderWithProvider = (component: React.ReactNode) => {
  return render(<AppProvider>{component}</AppProvider>);
};

describe('ConversationHistory Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('displays list of sessions', async () => {
    (api.listSessions as any).mockResolvedValue(mockSessions);
    renderWithProvider(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText(/Test Session 1/)).toBeInTheDocument();
      expect(screen.getByText(/Test Session 2/)).toBeInTheDocument();
    });
  });

  it('has New Chat button', async () => {
    (api.listSessions as any).mockResolvedValue([]);
    renderWithProvider(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('New Chat')).toBeInTheDocument();
    });
  });

  it('has Refresh button', async () => {
    (api.listSessions as any).mockResolvedValue([]);
    renderWithProvider(<ConversationHistory />);

    await waitFor(() => {
      expect(screen.getByText('Refresh')).toBeInTheDocument();
    });
  });
});
