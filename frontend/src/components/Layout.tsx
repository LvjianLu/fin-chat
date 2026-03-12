import { useAppState } from '@/hooks/useAppState';
import LeftPanel from '@/components/LeftPanel';
import ChatPanel from '@/components/ChatPanel';
import RightPanel from '@/components/RightPanel';
import ErrorBoundary from './ErrorBoundary';

function Layout() {
  const {} = useAppState();

  return (
    <ErrorBoundary>
      <div className="flex h-screen w-full bg-gray-50 dark:bg-dark-950">
        {/* Left Panel - Conversation History & Upload */}
        <aside className="w-80 flex-shrink-0 border-r border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-900 overflow-hidden flex flex-col">
          <LeftPanel />
        </aside>

        {/* Center Panel - Chat Interface */}
        <main className="flex-1 flex flex-col overflow-hidden bg-white dark:bg-dark-900">
          <ChatPanel />
        </main>

        {/* Right Panel - Agents, Plans, Results */}
        <aside className="w-80 flex-shrink-0 border-l border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-900 overflow-hidden flex flex-col">
          <RightPanel />
        </aside>
      </div>
    </ErrorBoundary>
  );
}

export default Layout;
