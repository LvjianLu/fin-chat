import { useRef, useEffect } from 'react';
import { useAppState } from '@/hooks/useAppState';
import { Send, Loader2, Trash2 } from 'lucide-react';

function ChatPanel() {
  const {
    state,
    sendMessage,
    clearHistory,
    analyzeDocument,
  } = useAppState();

  const { messages, currentDoc, docSource, isLoading, quickAnalysis } = state;
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    if (messagesEndRef.current && typeof messagesEndRef.current.scrollIntoView === 'function') {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  // Handle quick analysis
  useEffect(() => {
    if (quickAnalysis) {
      analyzeDocument();
    }
  }, [quickAnalysis]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const input = chatInputRef.current;
    if (!input || !input.value.trim() || isLoading) return;

    const message = input.value.trim();
    input.value = '';
    await sendMessage(message);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleClearChat = async () => {
    if (window.confirm('Clear chat history? This cannot be undone.')) {
      await clearHistory();
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-dark-700 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Chat</h2>
          {docSource && (
            <p className="text-sm text-gray-600 dark:text-gray-400 flex items-center gap-1 mt-1">
              <span className="text-blue-600 dark:text-blue-400">📄</span>
              {docSource}
            </p>
          )}
        </div>
        {messages.length > 0 && (
          <button
            onClick={handleClearChat}
            disabled={isLoading}
            className="flex items-center gap-2 px-3 py-1.5 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 disabled:opacity-50 text-red-700 dark:text-red-300 rounded-lg text-sm font-medium transition-colors"
          >
            <Trash2 className="h-4 w-4" />
            Clear Chat
          </button>
        )}
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="max-w-md text-center p-8">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Welcome to FinChat
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                Upload a financial document to get started, or just ask me any financial
                questions. I can help analyze financial statements, explain concepts, and
                more.
              </p>
              {currentDoc && (
                <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <p className="text-sm text-blue-800 dark:text-blue-300">
                    <strong>Document loaded:</strong> {docSource}
                  </p>
                  <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
                    {currentDoc.length.toLocaleString()} characters
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg px-4 py-3 ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 dark:bg-dark-800 text-gray-900 dark:text-white'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                <p
                  className={`text-xs mt-2 ${
                    message.role === 'user'
                      ? 'text-blue-200'
                      : 'text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {new Date(message.timestamp).toLocaleTimeString([], {
                    hour: '2-digit',
                    minute: '2-digit',
                  })}
                </p>
              </div>
            </div>
          ))
        )}

        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[70%] rounded-lg px-4 py-3 bg-gray-100 dark:bg-dark-800">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                <span className="text-gray-600 dark:text-gray-300">Analyzing...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 dark:border-dark-700 bg-white dark:bg-dark-900">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <textarea
            ref={chatInputRef}
            placeholder="Type your message... (Shift+Enter for new line)"
            className="flex-1 px-4 py-3 border border-gray-300 dark:border-dark-600 rounded-lg bg-gray-50 dark:bg-dark-800 text-gray-900 dark:text-white resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
            rows={2}
            disabled={isLoading}
            onKeyDown={handleKeyDown}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-800 text-white rounded-lg flex items-center justify-center transition-colors self-end"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </button>
        </form>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-2 text-center">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  );
}

export default ChatPanel;
