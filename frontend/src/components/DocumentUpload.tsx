import { useRef, useState } from 'react';
import { useAppState } from '@/hooks/useAppState';
import { Upload, FileText, X, Loader2, AlertCircle } from 'lucide-react';

function DocumentUpload() {
  const { state, dispatch, uploadDocument, clearDocument } = useAppState();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setSelectedFile(file);
    setUploadError(null);
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    setUploadError(null);
    try {
      await uploadDocument(selectedFile);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error: any) {
      setUploadError(error.message || 'Failed to upload document');
    }
  };

  const handleClear = async () => {
    try {
      await clearDocument();
    } catch (error: any) {
      setUploadError(error.message || 'Failed to clear document');
    }
  };

  const isUploadDisabled = !selectedFile || state.isLoading;

  return (
    <div className="p-4 space-y-4">
      {/* File Input */}
      <div
        className="border-2 border-dashed border-gray-300 dark:border-dark-600 rounded-lg p-6 text-center hover:border-blue-500 dark:hover:border-blue-500 transition-colors cursor-pointer"
        onClick={() => fileInputRef.current?.click()}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".txt,.pdf,.htm,.html"
          onChange={handleFileChange}
          className="hidden"
        />
        <Upload className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500" />
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
          Click to upload a document
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Supports: TXT, PDF, HTM, HTML
        </p>
      </div>

      {/* Selected File */}
      {selectedFile && (
        <div className="border border-gray-200 dark:border-dark-700 rounded-lg p-3 bg-gray-50 dark:bg-dark-800">
          <div className="flex items-center gap-3">
            <FileText className="h-8 w-8 text-blue-600 dark:text-blue-400 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {selectedFile.name}
              </p>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                {(selectedFile.size / 1024).toFixed(1)} KB
              </p>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedFile(null);
                if (fileInputRef.current) fileInputRef.current.value = '';
              }}
              className="p-1 hover:bg-gray-200 dark:hover:bg-dark-700 rounded"
            >
              <X className="h-4 w-4 text-gray-500 dark:text-gray-400" />
            </button>
          </div>

          {/* Upload Button */}
          <button
            onClick={handleUpload}
            disabled={isUploadDisabled}
            className="mt-3 w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-800 text-white rounded-lg font-medium flex items-center justify-center gap-2 transition-colors"
          >
            {state.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Load Document
          </button>
        </div>
      )}

      {/* Upload Error */}
      {uploadError && (
        <div className="border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-900/20 rounded-lg p-3 flex items-start gap-2">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <p className="text-sm text-red-700 dark:text-red-300">{uploadError}</p>
        </div>
      )}

      {/* Current Document */}
      {state.currentDoc && state.docSource && (
        <div className="border border-green-200 dark:border-green-900 bg-green-50 dark:bg-green-900/20 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-medium text-green-800 dark:text-green-300 flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Current Document
            </h4>
            <button
              onClick={handleClear}
              disabled={state.isLoading}
              className="text-sm text-red-600 dark:text-red-400 hover:underline disabled:opacity-50"
            >
              Clear
            </button>
          </div>
          <p className="text-sm text-green-700 dark:text-green-300 mb-1">
            {state.docSource}
          </p>
          <p className="text-xs text-green-600 dark:text-green-400">
            {state.currentDoc.length.toLocaleString()} characters
          </p>
        </div>
      )}

      {/* Quick Actions */}
      {state.currentDoc && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">Quick Actions</h4>
          <button
            onClick={() => dispatch({ type: 'SET_QUICK_ANALYSIS', payload: true })}
            disabled={state.isLoading}
            className="w-full py-2 px-4 bg-purple-100 dark:bg-purple-900/30 hover:bg-purple-200 dark:hover:bg-purple-900/50 disabled:opacity-50 text-purple-700 dark:text-purple-300 rounded-lg font-medium transition-colors flex items-center justify-center gap-2"
          >
            📈 Analyze Financials
          </button>
          <div className="space-y-2">
            <input
              type="text"
              placeholder="Search in document..."
              className="w-full px-3 py-2 border border-gray-300 dark:border-dark-600 rounded-lg bg-white dark:bg-dark-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  dispatch({ type: 'SET_SHOW_SEARCH', payload: true });
                }
              }}
            />
            <button
              onClick={() => dispatch({ type: 'SET_SHOW_SEARCH', payload: true })}
              disabled={state.isLoading}
              className="w-full py-2 px-4 bg-green-100 dark:bg-green-900/30 hover:bg-green-200 dark:hover:bg-green-900/50 disabled:opacity-50 text-green-700 dark:text-green-300 rounded-lg font-medium transition-colors"
            >
              🔍 Search Document
            </button>
          </div>
        </div>
      )}

      {/* Search Input (shown when showSearch is true) */}
      {state.showSearch && (
        <div className="border border-gray-200 dark:border-dark-700 rounded-lg p-3 bg-gray-50 dark:bg-dark-800">
          <SearchDocument onClose={() => dispatch({ type: 'SET_SHOW_SEARCH', payload: false })} />
        </div>
      )}
    </div>
  );
}

function SearchDocument({ onClose }: { onClose: () => void }) {
  const { searchDocument } = useAppState();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setIsSearching(true);
    setError(null);
    try {
      const searchResult = await searchDocument(query);
      setResult(searchResult);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsSearching(false);
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="font-medium text-gray-900 dark:text-white text-sm">Document Search</h4>
        <button
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
        >
          ✕
        </button>
      </div>
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter search query..."
          className="flex-1 px-3 py-2 border border-gray-300 dark:border-dark-600 rounded bg-white dark:bg-dark-700 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !isSearching) {
              handleSearch();
            }
          }}
        />
        <button
          onClick={handleSearch}
          disabled={isSearching || !query.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 dark:disabled:bg-blue-800 text-white rounded text-sm font-medium transition-colors"
        >
          {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Search'}
        </button>
      </div>
      {error && (
        <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
      )}
      {result && (
        <div className="max-h-48 overflow-y-auto">
          <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap p-3 bg-white dark:bg-dark-900 rounded border border-gray-200 dark:border-dark-700">
            {result}
          </pre>
        </div>
      )}
    </div>
  );
}

export default DocumentUpload;
