import { useState } from 'react';
import { useAppState } from '@/hooks/useAppState';
import {
  Agent, Plan, SearchResult, PlanStep
} from '@/types';
import {
  Play, Square, CheckCircle, AlertCircle, Loader2, Circle,
  ChevronDown, ChevronRight, ExternalLink, Clock
} from 'lucide-react';

// Inline RunningAgentCard component
function RunningAgentCard({ agent }: { agent: Agent }) {
  const { dispatch } = useAppState();
  const [isStopping, setIsStopping] = useState(false);

  const getStatusIcon = () => {
    switch (agent.status) {
      case 'running': return <Loader2 className="h-4 w-4 animate-spin text-blue-600 dark:text-blue-400" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'stopped': return <Square className="h-4 w-4 text-gray-600 dark:text-gray-400" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />;
      default: return <Play className="h-4 w-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (agent.status) {
      case 'running': return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20';
      case 'completed': return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'stopped': return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800';
      case 'failed': return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20';
      default: return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800';
    }
  };

  const handleStop = async () => {
    setIsStopping(true);
    try {
      dispatch({ type: 'REMOVE_AGENT', payload: agent.id });
    } finally {
      setIsStopping(false);
    }
  };

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`border rounded-lg p-3 ${getStatusColor()}`}>
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {getStatusIcon()}
          <h4 className="font-medium text-gray-900 dark:text-white text-sm truncate">{agent.name}</h4>
        </div>
        <span className="text-xs px-2 py-1 bg-white dark:bg-dark-900 rounded-full capitalize text-gray-600 dark:text-gray-300">
          {agent.status}
        </span>
      </div>
      {agent.task && <p className="text-xs text-gray-600 dark:text-gray-400 mb-2 line-clamp-2">{agent.task}</p>}
      {agent.progress !== undefined && (
        <div className="mb-2">
          <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
            <span>Progress</span>
            <span>{agent.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-dark-700 rounded-full h-1.5">
            <div className="bg-blue-600 h-1.5 rounded-full transition-all" style={{ width: `${agent.progress}%` }}></div>
          </div>
        </div>
      )}
      {agent.started_at && <p className="text-xs text-gray-500 dark:text-gray-400">Started: {formatTime(agent.started_at)}</p>}
      {agent.status === 'running' && (
        <button onClick={handleStop} disabled={isStopping} className="mt-2 w-full py-1.5 px-3 bg-red-100 dark:bg-red-900/30 hover:bg-red-200 dark:hover:bg-red-900/50 disabled:opacity-50 text-red-700 dark:text-red-300 rounded text-xs font-medium transition-colors flex items-center justify-center gap-1">
          {isStopping ? <Loader2 className="h-3 w-3 animate-spin" /> : <Square className="h-3 w-3" />}
          Stop Agent
        </button>
      )}
    </div>
  );
}

// Inline PlanCard component
function PlanCard({ plan }: { plan: Plan }) {
  const { dispatch } = useAppState();
  const [isExpanded, setIsExpanded] = useState(true);
  const [isCompleting, setIsCompleting] = useState(false);

  const getStatusColor = () => {
    switch (plan.status) {
      case 'running': return 'border-blue-200 dark:border-blue-800 bg-blue-50 dark:bg-blue-900/20';
      case 'completed': return 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20';
      case 'failed': return 'border-red-200 dark:border-red-800 bg-red-50 dark:bg-red-900/20';
      default: return 'border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800';
    }
  };

  const getStatusIcon = () => {
    switch (plan.status) {
      case 'running': return <Loader2 className="h-4 w-4 animate-spin text-blue-600 dark:text-blue-400" />;
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />;
      case 'failed': return <AlertCircle className="h-4 w-4 text-red-600 dark:text-red-400" />;
      default: return <Circle className="h-4 w-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  const getStepIcon = (stepStatus: string) => {
    switch (stepStatus) {
      case 'completed': return <CheckCircle className="h-3 w-3 text-green-600 dark:text-green-400" />;
      case 'running': return <Loader2 className="h-3 w-3 animate-spin text-blue-600 dark:text-blue-400" />;
      case 'failed': return <AlertCircle className="h-3 w-3 text-red-600 dark:text-red-400" />;
      default: return <Circle className="h-3 w-3 text-gray-400 dark:text-gray-500" />;
    }
  };

  const handleComplete = async () => {
    setIsCompleting(true);
    try {
      dispatch({ type: 'UPDATE_PLAN', payload: { id: plan.id, updates: { status: 'completed' } } });
    } finally {
      setIsCompleting(false);
    }
  };

  const completedSteps = plan.steps.filter((s) => s.status === 'completed').length;
  const totalSteps = plan.steps.length;

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`border rounded-lg overflow-hidden ${getStatusColor()}`}>
      <div className="p-3 cursor-pointer flex items-center justify-between gap-2" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {isExpanded ? <ChevronDown className="h-4 w-4 text-gray-500 dark:text-gray-400 flex-shrink-0" /> : <ChevronRight className="h-4 w-4 text-gray-500 dark:text-gray-400 flex-shrink-0" />}
          {getStatusIcon()}
          <h4 className="font-medium text-gray-900 dark:text-white text-sm truncate">{plan.name}</h4>
        </div>
        <span className="text-xs px-2 py-1 bg-white dark:bg-dark-900 rounded-full capitalize text-gray-600 dark:text-gray-300">{plan.status}</span>
      </div>
      {totalSteps > 0 && plan.status !== 'completed' && (
        <div className="px-3 pb-2">
          <div className="flex items-center justify-between text-xs text-gray-600 dark:text-gray-400 mb-1">
            <span>Progress</span>
            <span>{completedSteps}/{totalSteps} steps</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-dark-700 rounded-full h-1.5">
            <div className="bg-blue-600 dark:bg-blue-500 h-1.5 rounded-full transition-all" style={{ width: `${(completedSteps / totalSteps) * 100}%` }}></div>
          </div>
        </div>
      )}
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-dark-700 p-3 bg-white dark:bg-dark-900/50">
          {plan.steps.length > 0 && (
            <div className="space-y-2 mb-3">
              {plan.steps.map((step: PlanStep, index: number) => (
                <div key={step.id} className="flex items-start gap-2">
                  <div className="mt-0.5">{getStepIcon(step.status)}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-gray-700 dark:text-gray-300">
                      <span className="font-medium">Step {index + 1}:</span> {step.description}
                    </p>
                    {step.result && (
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 pl-4 border-l-2 border-gray-200 dark:border-dark-700">
                        {step.result.substring(0, 150)}{step.result.length > 150 && '...'}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
          <div className="text-xs text-gray-500 dark:text-gray-400 mb-3">Created: {formatDate(plan.created_at)}</div>
          {plan.status === 'running' && (
            <button onClick={(e) => { e.stopPropagation(); handleComplete(); }} disabled={isCompleting} className="w-full py-1.5 px-3 bg-green-100 dark:bg-green-900/30 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50 text-green-700 dark:text-green-300 rounded text-xs font-medium transition-colors flex items-center justify-center gap-1">
              {isCompleting ? <Loader2 className="h-3 w-3 animate-spin" /> : <CheckCircle className="h-3 w-3" />}
              Mark Complete
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Inline SearchResultCard component
function SearchResultCard({ result }: { result: SearchResult }) {
  const [isExpanded, setIsExpanded] = useState(true);

  const formatTime = (date: Date) => {
    return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="border border-gray-200 dark:border-dark-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-dark-800">
      <div className="p-3 cursor-pointer flex items-center gap-2 hover:bg-gray-100 dark:hover:bg-dark-700 transition-colors" onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? <ChevronDown className="h-4 w-4 text-gray-500 dark:text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-500 dark:text-gray-400" />}
        <span className="font-medium text-gray-900 dark:text-white text-sm truncate flex-1">{result.query}</span>
        <span className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-1"><Clock className="h-3 w-3" />{formatTime(result.time)}</span>
      </div>
      {isExpanded && (
        <div className="border-t border-gray-200 dark:border-dark-700 p-3 bg-white dark:bg-dark-900/50">
          {result.results.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">No results found</p>
          ) : (
            <div className="space-y-3">
              {result.results.map((r, idx) => (
                <div key={idx} className="group">
                  <a href={r.url} target="_blank" rel="noopener noreferrer" className="flex items-start gap-2 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    <h5 className="text-sm font-medium text-blue-600 dark:text-blue-400 flex-1 line-clamp-2 group-hover:underline">{r.title}</h5>
                    <ExternalLink className="h-3 w-3 mt-1 flex-shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                  </a>
                  <p className="text-xs text-gray-600 dark:text-gray-400 mt-1 line-clamp-3">{r.snippet}</p>
                  <p className="text-xs text-gray-500 dark:text-gray-500 mt-1 truncate">{r.url}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Main RightPanel component
function RightPanel() {
  const { state } = useAppState();
  const { runningAgents, activePlans, searchResults } = state;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 dark:border-dark-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Agent Monitor</h2>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        {/* Running Agents */}
        <section>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            Running Agents ({runningAgents.length})
          </h3>
          {runningAgents.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">No agents running</p>
          ) : (
            <div className="space-y-2">{runningAgents.map((agent) => <RunningAgentCard key={agent.id} agent={agent} />)}</div>
          )}
        </section>

        {/* Active Plans */}
        <section>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">📋 Active Plans ({activePlans.length})</h3>
          {activePlans.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">No active plans</p>
          ) : (
            <div className="space-y-3">{activePlans.map((plan) => <PlanCard key={plan.id} plan={plan} />)}</div>
          )}
        </section>

        {/* Search Results */}
        <section>
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">🔍 Search Results ({searchResults.length})</h3>
          {searchResults.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">No recent searches</p>
          ) : (
            <div className="space-y-2">{searchResults.slice(-5).reverse().map((result) => <SearchResultCard key={result.id} result={result} />)}</div>
          )}
        </section>
      </div>
    </div>
  );
}

export default RightPanel;
