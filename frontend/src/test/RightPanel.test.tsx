/// <reference types="jest" />
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import RightPanel from '../components/RightPanel';
import { AppProvider } from '../hooks/useAppState';

// Mock the API to avoid import.meta issues
jest.mock('@/services/api', () => ({
  healthCheck: jest.fn().mockResolvedValue({ status: 'ok' }),
  listSessions: jest.fn().mockResolvedValue([]),
  createSession: jest.fn(),
  getSessionDetail: jest.fn(),
}));

const renderWithProvider = (component: React.ReactNode) => {
  return render(<AppProvider>{component}</AppProvider>);
};

describe('RightPanel Component', () => {
  it('renders Agent Monitor header', async () => {
    renderWithProvider(<RightPanel />);

    await waitFor(() => {
      expect(screen.getByText('Agent Monitor')).toBeInTheDocument();
    });
  });

  it('shows empty state for running agents', async () => {
    renderWithProvider(<RightPanel />);

    await waitFor(() => {
      expect(screen.getByText('No agents running')).toBeInTheDocument();
    });
  });

  it('shows empty state for active plans', async () => {
    renderWithProvider(<RightPanel />);

    await waitFor(() => {
      expect(screen.getByText('No active plans')).toBeInTheDocument();
    });
  });

  it('shows empty state for search results', async () => {
    renderWithProvider(<RightPanel />);

    await waitFor(() => {
      expect(screen.getByText('No recent searches')).toBeInTheDocument();
    });
  });
});
