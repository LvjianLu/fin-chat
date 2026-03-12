import { useState } from 'react';
import { useAppState } from '@/hooks/useAppState';
import ConversationHistory from './ConversationHistory';
import DocumentUpload from './DocumentUpload';

function LeftPanel() {
  const {} = useAppState();
  const [activeTab, setActiveTab] = useState<'history' | 'upload'>('history');

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-dark-700">
        <h1 className="text-xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <span className="text-2xl">📊</span>
          FinChat
        </h1>
      </div>

      {/* Tab Navigation */}
      <div className="flex border-b border-gray-200 dark:border-dark-700">
        <button
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'history'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
          onClick={() => setActiveTab('history')}
        >
          💬 History
        </button>
        <button
          className={`flex-1 py-3 px-4 text-sm font-medium transition-colors ${
            activeTab === 'upload'
              ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50 dark:bg-blue-900/20'
              : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'
          }`}
          onClick={() => setActiveTab('upload')}
        >
          📁 Upload
        </button>
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto">
        {activeTab === 'history' && <ConversationHistory />}
        {activeTab === 'upload' && <DocumentUpload />}
      </div>
    </div>
  );
}

export default LeftPanel;
