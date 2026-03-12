import { useState } from 'react';
import { useAppState } from '@/hooks/useAppState';
import { formatDistanceToNow } from '@/utils/date';
import { Plus, RefreshCw, Loader2 } from 'lucide-react';

function ConversationHistory() {
  const {
    state,
    startNewSession,
    switchToSession,
    deleteSession,
    refreshSessions,
  } = useAppState();

  const { conversationSessions, currentSessionId } = state;
  const [isCreating, setIsCreating] = useState(false);

  const handleNewChat = async () => {
    setIsCreating(true);
    try {
      await startNewSession();
    } finally {
      setIsCreating(false);
    }
  };

  const handleLoadSession = async (sessionId: string) => {
    await switchToSession(sessionId);
  };

  const handleDeleteSession = async (sessionId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (window.confirm('Delete this conversation? This cannot be undone.')) {
      await deleteSession(sessionId);
    }
  };

  const handleRefresh = async () => {
    await refreshSessions();
  };

  const formatTitle = (title: string, maxLength: number = 30) => {
    if (!title || title.trim() === '') return 'Untitled';
    if (title.length > maxLength) return title.substring(0, maxLength) + '...';
    return title;
  };

  const formatTime = (timestamp: Date) => {
    try {
      return formatDistanceToNow(new Date(timestamp));
    } catch {
      return 'Unknown';
    }
  };

  const getPreview = (messages: any[]) => {
    if (!messages || messages.length === 0) return '*No messages*';
    const lastThree = messages.slice(-3);
    return lastThree
      .map((msg) => {
        const prefix = msg.role === 'user' ? '👤' : '🤖';
        const content = msg.content.substring(0, 80);
        return `${prefix} ${content}${msg.content.length > 80 ? '...' : ''}`;
      })
      .join('\n');
  };

  if (conversationSessions.length === 0 && !state.isLoading) {
    return (
      <div className="p-4 space-y-4">
        <button
          onClick={handleNewChat}
          disabled={isCreating || state.isLoading}
          className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors shadow-sm"
        >
          {isCreating ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Plus className="w-4 h-4" />
          )}
          New Chat
        </button>

        <button
          onClick={handleRefresh}
          disabled={state.isLoading}
          className="w-full py-2 px-4 bg-gray-100 dark:bg-dark-800 hover:bg-gray-200 dark:hover:bg-dark-700 disabled:opacity-50 text-gray-700 dark:text-gray-300 rounded-lg flex items-center justify-center gap-2 transition-colors text-sm"
        >
          {state.isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <RefreshCw className="w-4 h-4" />
          )}
          Refresh
        </button>

        <p className="text-gray-500 dark:text-gray-400 text-center text-sm">No conversation history</p>
      </div>
    );
  }

  return (
    <div className="p-4 space-y-4">
      {/* New Chat Button */}
      <button
        onClick={handleNewChat}
        disabled={isCreating || state.isLoading}
        className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors shadow-sm"
      >
        {isCreating ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <Plus className="w-4 h-4" />
        )}
        New Chat
      </button>

      {/* Refresh Button */}
      <button
        onClick={handleRefresh}
        disabled={state.isLoading}
        className="w-full py-2 px-4 bg-gray-100 dark:bg-dark-800 hover:bg-gray-200 dark:hover:bg-dark-700 disabled:opacity-50 text-gray-700 dark:text-gray-300 rounded-lg flex items-center justify-center gap-2 transition-colors text-sm"
      >
        {state.isLoading ? (
          <Loader2 className="w-4 h-4 animate-spin" />
        ) : (
          <RefreshCw className="w-4 h-4" />
        )}
        Refresh
      </button>

      {/* Sessions List */}
      <div className="space-y-2">
        {conversationSessions.map((session) => {
          const isCurrent = session.id === currentSessionId;
          const isPersisted = session.persisted;

          return (
            <div
              key={session.id}
              className={`border rounded-lg p-3 cursor-pointer transition-all ${
                isCurrent
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-sm'
                  : 'border-gray-200 dark:border-dark-700 hover:border-gray-300 dark:hover:border-dark-600'
              }`}
              onClick={() => handleLoadSession(session.id)}
            >
              {/* Title and time */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-medium text-gray-900 dark:text-white text-sm truncate flex-1">
                  {formatTitle(session.title)}
                  {isCurrent && (
                    <span className="ml-2 text-xs bg-blue-600 text-white px-1.5 py-0.5 rounded">Active</span>
                  )}
                </h3>
                <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                  {formatTime(session.timestamp)}
                </span>
              </div>

              {/* Metadata */}
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
                <span>{session.message_count} msgs</span>
                <span>•</span>
                <span>{isPersisted ? '✅ Saved' : '🔄 Unsaved'}</span>
              </div>

              {/* Document source */}
              {session.doc_source && (
                <p className="text-xs text-gray-600 dark:text-gray-300 mb-2 truncate">
                  📄 {session.doc_source}
                </p>
              )}

              {/* Preview */}
              {session.messages && session.messages.length > 0 && (
                <div className="text-xs text-gray-600 dark:text-gray-300 mb-3 whitespace-pre-wrap bg-gray-50 dark:bg-dark-800 p-2 rounded">
                  {getPreview(session.messages)}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex gap-2">
                {!isCurrent && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLoadSession(session.id);
                    }}
                    className="flex-1 py-1.5 px-3 bg-blue-100 dark:bg-blue-900/30 hover:bg-blue-200 dark:hover:bg-blue-900/50 text-blue-700 dark:text-blue-300 text-xs font-medium rounded transition-colors"
                  >
                    Load
                  </button>
                )}
                <button
                  onClick={(e) => handleDeleteSession(session.id, e)}
                  className={`py-1.5 px-3 ${
                    isCurrent
                      ? 'bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 text-red-700 dark:text-red-300'
                      : 'bg-gray-100 dark:bg-dark-800 hover:bg-gray-200 dark:hover:bg-dark-700 text-gray-700 dark:text-gray-300'
                  } text-xs font-medium rounded transition-colors`}
                >
                  Delete
                </button>
              </div>

              {/* Unsaved warning */}
              {isCurrent && !isPersisted && state.messages.length > 0 && (
                <p className="text-xs text-amber-600 dark:text-amber-400 mt-2">
                  ⚠️ Unsaved - will auto-save
                </p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ConversationHistory;
