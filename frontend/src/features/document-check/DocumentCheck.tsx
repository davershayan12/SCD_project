import React, { useState, useRef } from 'react';
import { AlertCircle, CheckCircle, FileText, Upload, Loader2, Download, Trash2, Cpu, Globe, BookOpen } from 'lucide-react';

interface Document {
  id: string;
  original_filename: string;
  total_pages: number;
  created_at: string;
}

export function DocumentCheck() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [searchProvider, setSearchProvider] = useState<string>('ddgs');
  const [customUrls, setCustomUrls] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  React.useEffect(() => {
    loadDocs();
  }, []);

  const loadDocs = async () => {
    try {
      const res = await fetch('/api/v1/documents');
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    const file = files[0];
    setIsLoading(true);
    setError(null);

    const fd = new FormData();
    fd.append('file', file);

    try {
      const res = await fetch('/api/v1/documents', { method: 'POST', body: fd });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Upload failed');
      }
      const data = await res.json();
      setSuccessMsg(`Uploaded "${file.name}" successfully.`);
      await loadDocs();
      setSelectedDocId(data.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsLoading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleLoadDemo = async (type: 'web' | 'ai' | 'human') => {
    setIsLoading(true);
    setError(null);
    let sampleText = '';
    let filename = '';

    if (type === 'web') {
      filename = 'demo_web_copied.txt';
      sampleText = 'Plagiarism detection software is software that highlights similarities between documents and existing sources. It is widely used in academia to verify original student submissions and ensure academic integrity across institutions worldwide.';
    } else if (type === 'ai') {
      filename = 'demo_ai_generated.txt';
      sampleText = 'Machine learning models have achieved remarkable success across diverse application domains. However, evaluating their inherent limitations remains critical for deployment in production environments where reliability and safety are paramount.';
    } else {
      filename = 'demo_human_original.txt';
      sampleText = 'During our archival field studies conducted in rural settlements last autumn, we observed distinct patterns of seasonal migration that diverged significantly from historical census models.';
    }

    try {
      const blob = new Blob([sampleText], { type: 'text/plain' });
      const file = new File([blob], filename, { type: 'text/plain' });
      const fd = new FormData();
      fd.append('file', file);

      const res = await fetch('/api/v1/documents', { method: 'POST', body: fd });
      if (res.ok) {
        const data = await res.json();
        await loadDocs();
        setSelectedDocId(data.id);
        setSuccessMsg(`Loaded demo sample: ${filename}`);
      }
    } catch (e) {
      setError('Failed to load demo sample');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunCheck = async () => {
    if (!selectedDocId) {
      setError('Please select or upload a document first.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const urls = customUrls ? customUrls.split('\n').map(u => u.trim()).filter(Boolean) : undefined;
      const res = await fetch('/api/v1/document-check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocId,
          search_provider: searchProvider,
          custom_urls: urls,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Check failed');
      }

      const data = await res.json();
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Check failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 mb-1">
          ResearchRadar — Document Check (Web Search & AI Detection)
        </h1>
        <p className="text-gray-600">
          Search the internet for matching passages and evaluate AI-text likelihood in seconds.
        </p>
      </div>

      {/* Demo Samples Toolbar */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="text-sm text-indigo-900 font-medium">
          ⚡ Quick Demo Mode: Load built-in evaluation samples
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => handleLoadDemo('web')}
            disabled={isLoading}
            className="px-3 py-1.5 bg-white border border-indigo-300 text-indigo-700 text-xs font-semibold rounded hover:bg-indigo-100"
          >
            Load Web-Copied Sample
          </button>
          <button
            onClick={() => handleLoadDemo('ai')}
            disabled={isLoading}
            className="px-3 py-1.5 bg-white border border-indigo-300 text-indigo-700 text-xs font-semibold rounded hover:bg-indigo-100"
          >
            Load AI-Generated Sample
          </button>
          <button
            onClick={() => handleLoadDemo('human')}
            disabled={isLoading}
            className="px-3 py-1.5 bg-white border border-indigo-300 text-indigo-700 text-xs font-semibold rounded hover:bg-indigo-100"
          >
            Load Human Original Sample
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 flex items-center gap-2">
          <AlertCircle className="w-5 h-5" />
          <span>{error}</span>
        </div>
      )}

      {successMsg && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-green-800 flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Input Section */}
      {!result && (
        <div className="bg-white border rounded-lg p-6 space-y-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleUpload}
              accept=".pdf,.txt,.docx"
              className="hidden"
              id="doc-upload"
            />
            <label htmlFor="doc-upload" className="cursor-pointer flex flex-col items-center">
              <Upload className="w-10 h-10 text-gray-400 mb-2" />
              <p className="font-medium text-gray-700">Drop PDF/TXT document here or <span className="text-blue-600 underline">browse</span></p>
            </label>
          </div>

          {/* Document Select */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-2">Select Uploaded Document:</h3>
            <div className="space-y-2 max-h-48 overflow-y-auto">
              {documents.map((doc) => (
                <div
                  key={doc.id}
                  onClick={() => setSelectedDocId(doc.id)}
                  className={`p-3 border rounded-lg cursor-pointer flex items-center justify-between ${
                    selectedDocId === doc.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-gray-500" />
                    <span className="font-medium text-gray-900">{doc.original_filename}</span>
                  </div>
                  <span className="text-xs text-gray-500">{doc.total_pages} page(s)</span>
                </div>
              ))}
            </div>
          </div>

          {/* Search Options */}
          <div className="grid md:grid-cols-2 gap-4 pt-4 border-t">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Web Search Provider:</label>
              <select
                value={searchProvider}
                onChange={(e) => setSearchProvider(e.target.value)}
                className="w-full border rounded-md p-2 text-sm bg-white"
              >
                <option value="ddgs">DuckDuckGo Web Search (Demo)</option>
                <option value="scholarly">Scholarly APIs (arXiv / OpenAlex)</option>
                <option value="none">None (AI Detection only)</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Custom URLs (one per line):</label>
              <textarea
                value={customUrls}
                onChange={(e) => setCustomUrls(e.target.value)}
                placeholder="https://example.com/article"
                rows={2}
                className="w-full border rounded-md p-2 text-sm"
              />
            </div>
          </div>

          <button
            onClick={handleRunCheck}
            disabled={!selectedDocId || isLoading}
            className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Running Web Search & AI Detection (~30-60s)...
              </>
            ) : (
              <>
                <Cpu className="w-5 h-5" />
                Run Document Check
              </>
            )}
          </button>
        </div>
      )}

      {/* Results Section */}
      {result && (
        <div className="space-y-6">
          <div className="flex justify-between items-center bg-white p-4 border rounded-lg">
            <div>
              <h2 className="font-bold text-gray-900 text-lg">Check Results for {result.filename}</h2>
              <p className="text-xs text-gray-500">Status: {result.status} | Corpus: {result.corpus_scope}</p>
            </div>
            <button
              onClick={() => setResult(null)}
              className="px-4 py-2 border rounded-md text-sm font-medium hover:bg-gray-50"
            >
              Check Another Document
            </button>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {/* Panel 1: Web Similarity */}
            <div className="bg-white border rounded-lg p-6 space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b">
                <Globe className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-gray-900">Web Plagiarism Search</h3>
              </div>

              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-2xl font-bold text-gray-900">{result.lexical_similarity_percent}%</p>
                  <p className="text-xs text-gray-500 font-medium">Similarity</p>
                </div>
                <div className="bg-gray-50 p-3 rounded">
                  <p className="text-2xl font-bold text-gray-900">{result.matches.length}</p>
                  <p className="text-xs text-gray-500 font-medium">Matched Passages</p>
                </div>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {result.matches.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-6">No matching web pages found.</p>
                ) : (
                  result.matches.map((m: any, i: number) => (
                    <div key={i} className="p-3 border rounded text-xs space-y-1 bg-yellow-50/40">
                      <p className="font-semibold text-gray-900 truncate">Source: {m.source_title}</p>
                      <a href={m.source_document_id} target="_blank" rel="noreferrer" className="text-blue-600 underline truncate block">{m.source_document_id}</a>
                      <p className="italic text-gray-700">"{m.submitted_text}"</p>
                    </div>
                  ))
                )}
              </div>

              <div className="text-xs bg-gray-50 p-3 rounded border text-gray-600">
                <strong>Diagnostics:</strong> {result.status_diagnostics.queries_run} queries run, {result.status_diagnostics.pages_fetched_ok} pages successfully fetched.
              </div>
            </div>

            {/* Panel 2: AI-Likelihood Detector */}
            <div className="bg-white border rounded-lg p-6 space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b">
                <Cpu className="w-5 h-5 text-indigo-600" />
                <h3 className="font-bold text-gray-900">AI-Text Likelihood Detector</h3>
              </div>

              <div className="text-center bg-indigo-50 p-4 rounded-lg">
                <p className="text-3xl font-extrabold text-indigo-900">{result.ai_detection.overall_score}%</p>
                <p className="text-sm font-semibold text-indigo-700 mt-1">AI-Likelihood Band: {result.ai_detection.overall_likelihood_band}</p>
              </div>

              <div className="space-y-2 max-h-64 overflow-y-auto">
                {result.ai_detection.paragraphs.map((p: any, i: number) => (
                  <div key={i} className="p-3 border rounded text-xs space-y-1 bg-gray-50">
                    <div className="flex justify-between font-medium">
                      <span>Paragraph {p.index + 1} ({p.word_count} words)</span>
                      <span className={p.likelihood_band === 'High' ? 'text-red-600 font-bold' : 'text-gray-600'}>
                        {p.status === 'Assessed' ? `AI Score: ${p.score}% (${p.likelihood_band})` : p.status}
                      </span>
                    </div>
                    <p className="text-gray-700 line-clamp-2">{p.text}</p>
                  </div>
                ))}
              </div>

              <div className="text-xs bg-yellow-50 border border-yellow-200 p-3 rounded text-yellow-800">
                <strong>Caveat:</strong> {result.ai_detection.disclaimer}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DocumentCheck;
