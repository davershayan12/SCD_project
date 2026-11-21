import React, { useState, useRef } from 'react';
import { AlertCircle, CheckCircle, FileText, Upload, Loader2, Download, Trash2, Eye, ArrowLeft, BookOpen } from 'lucide-react';

// Types
interface PlagiarismMatch {
  match_type: 'exact' | 'near-exact';
  submitted_page: number;
  submitted_span: [number, number];
  source_document_id: string;
  source_title: string;
  source_page: number;
  similarity: number;
  submitted_text: string;
  source_text: string;
}

interface PlagiarismReport {
  report_id: string;
  document_id: string;
  status: 'completed' | 'pending' | 'failed';
  corpus_scope: string;
  parameters: {
    k: number;
    w: number;
    min_tokens: number;
    excluded: string[];
  };
  eligible_word_count: number;
  matched_word_count: number;
  lexical_similarity_percent: number;
  largest_single_source_percent: number;
  matches: PlagiarismMatch[];
  disclaimer: string;
  created_at: string;
}

interface Document {
  id: string;
  original_filename: string;
  total_pages: number;
  created_at: string;
}

interface PageDetail {
  page_number: number;
  char_count: number;
  text_preview: string;
}

interface DocumentDetail {
  id: string;
  original_filename: string;
  pages: PageDetail[];
}

// Constants
const CORPUS_DISCLAIMER = 'This checker only compares against documents you have uploaded. It does not search the internet, paywalled journals, or Turnitin\'s private corpus.';

const MATCH_TYPE_LABELS: Record<string, { label: string; color: string; badge: string }> = {
  exact: { label: 'Exact match (Red highlight)', color: 'bg-red-50 border-red-200 text-red-900', badge: 'bg-red-100 text-red-800 border-red-200' },
  'near-exact': { label: 'Near-exact match (Yellow highlight)', color: 'bg-yellow-50 border-yellow-200 text-yellow-900', badge: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
};

// Component: Plagiarism Checker Main
export function PlagiarismChecker() {
  const [step, setStep] = useState<'select' | 'check' | 'result'>('select');
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [includeReferences, setIncludeReferences] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [report, setReport] = useState<PlagiarismReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Full document text state
  const [submittedDocDetail, setSubmittedDocDetail] = useState<DocumentDetail | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<PlagiarismMatch | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load documents on mount
  React.useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    try {
      const response = await fetch('/api/v1/documents');
      if (response.ok) {
        const data = await response.json();
        setDocuments(data.documents || []);
      }
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
  };

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    setIsUploading(true);
    setError(null);
    setSuccessMessage(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('/api/v1/documents', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Upload failed');
      }

      const data = await response.json();
      setSuccessMessage(`Successfully uploaded "${file.name}"`);
      await loadDocuments();
      setSelectedDocId(data.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleDeleteDocument = async (docId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this document?')) return;

    try {
      const response = await fetch(`/api/v1/documents/${docId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        if (selectedDocId === docId) setSelectedDocId('');
        await loadDocuments();
      } else {
        const errData = await response.json();
        setError(errData.detail || 'Failed to delete document');
      }
    } catch (err) {
      setError('Failed to delete document');
    }
  };

  const handleCheck = async () => {
    if (!selectedDocId) {
      setError('Please select or upload a document to check');
      return;
    }

    setIsChecking(true);
    setError(null);

    try {
      const response = await fetch('/api/v1/plagiarism/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          document_id: selectedDocId,
          include_references: includeReferences,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Check failed');
      }

      const data = await response.json();
      await pollReport(data.report_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsChecking(false);
    }
  };

  const pollReport = async (reportId: string) => {
    let attempts = 0;
    const maxAttempts = 30;

    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`/api/v1/plagiarism/reports/${reportId}`);
        if (response.ok) {
          const reportData = await response.json();
          setReport(reportData);

          // Fetch full submitted document text (all pages)
          const subDocRes = await fetch(`/api/v1/documents/${reportData.document_id}`);
          if (subDocRes.ok) {
            const subDoc = await subDocRes.json();
            setSubmittedDocDetail(subDoc);
          }

          setStep('result');
          return;
        }
      } catch (err) {
        console.error('Polling error:', err);
      }

      await new Promise(resolve => setTimeout(resolve, 1000));
      attempts++;
    }

    setError('Report generation timed out. Please try again.');
  };

  const handleReset = () => {
    setStep('select');
    setReport(null);
    setError(null);
    setSuccessMessage(null);
    setSelectedMatch(null);
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          ResearchRadar — Plagiarism & Similarity Checker
        </h1>
        <p className="text-gray-600">
          Inspect your checked document with Word-style inline text highlighting.
        </p>
      </div>

      {/* Corpus Scope Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <div className="flex items-start gap-3">
          <FileText className="w-5 h-5 text-blue-600 mt-0.5" />
          <div>
            <h3 className="font-medium text-blue-900">Corpus Scope</h3>
            <p className="text-sm text-blue-700 mt-1">
              {CORPUS_DISCLAIMER}
            </p>
          </div>
        </div>
      </div>

      {/* Error & Success Alerts */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 text-red-800">
            <AlertCircle className="w-5 h-5" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-center gap-2 text-green-800">
            <CheckCircle className="w-5 h-5" />
            <span>{successMessage}</span>
          </div>
        </div>
      )}

      {/* Step 1: Select Document */}
      {step === 'select' && (
        <div className="space-y-6">
          {/* Upload Dropzone */}
          <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileUpload}
              accept=".pdf,.txt"
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center">
              {isUploading ? (
                <>
                  <Loader2 className="w-12 h-12 text-blue-600 animate-spin mb-3" />
                  <p className="text-lg font-medium text-gray-700">Processing and extracting text...</p>
                </>
              ) : (
                <>
                  <Upload className="w-12 h-12 text-gray-400 mb-3" />
                  <p className="text-lg font-medium text-gray-700">
                    Drop your PDF or TXT file here, or <span className="text-blue-600 underline">browse</span>
                  </p>
                  <p className="text-sm text-gray-500 mt-1">
                    Supports text-based PDF and TXT files up to 50MB
                  </p>
                </>
              )}
            </label>
          </div>

          {/* Document Selection List */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Your Uploaded Corpus ({documents.length} documents)
            </h2>

            {documents.length === 0 ? (
              <div className="text-center py-6 text-gray-500">
                <p>No documents uploaded yet. Upload a document above to get started.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {documents.map((doc) => (
                  <div
                    key={doc.id}
                    onClick={() => setSelectedDocId(doc.id)}
                    className={`flex items-center p-4 border rounded-lg cursor-pointer transition-colors ${
                      selectedDocId === doc.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <FileText className="w-5 h-5 text-gray-400 mr-3" />
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">
                        {doc.original_filename}
                      </p>
                      <p className="text-sm text-gray-500">
                        {doc.total_pages} page(s) • Uploaded{' '}
                        {new Date(doc.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {selectedDocId === doc.id && (
                      <span className="text-xs bg-blue-100 text-blue-800 font-medium px-2.5 py-1 rounded mr-3">
                        Selected for Check
                      </span>
                    )}
                    <button
                      onClick={(e) => handleDeleteDocument(doc.id, e)}
                      className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete document"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Options */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Analysis Options
            </h2>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={includeReferences}
                onChange={(e) => setIncludeReferences(e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-700">
                Include references section in check
              </span>
            </label>

            <p className="text-xs text-gray-500 mt-2 ml-6">
              Unchecking this will exclude references from similarity analysis.
            </p>
          </div>

          {/* Action */}
          <button
            onClick={handleCheck}
            disabled={!selectedDocId || isChecking || documents.length === 0}
            className="w-full py-3 px-4 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed flex items-center justify-center gap-2 shadow"
          >
            {isChecking ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Analyzing Document...
              </>
            ) : (
              <>
                <Upload className="w-5 h-5" />
                Run Similarity Check against Corpus
              </>
            )}
          </button>
        </div>
      )}

      {/* Step 2: Result with Full Document Word-Style Highlighter */}
      {step === 'result' && report && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-medium text-gray-900">
                Similarity Report & Full Document Highlighter
              </h2>
              <button
                onClick={handleReset}
                className="text-sm text-blue-600 hover:underline flex items-center gap-1"
              >
                <ArrowLeft className="w-4 h-4" /> Back to Uploads
              </button>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <MetricCard
                label="Similarity"
                value={`${report.lexical_similarity_percent.toFixed(1)}%`}
                description="of document"
              />
              <MetricCard
                label="Matched Words"
                value={report.matched_word_count.toLocaleString()}
                description={`of ${report.eligible_word_count.toLocaleString()}`}
              />
              <MetricCard
                label="Matches Found"
                value={report.matches.length.toString()}
                description="in corpus"
              />
              <MetricCard
                label="Largest Source"
                value={`${report.largest_single_source_percent.toFixed(1)}%`}
                description="from one source"
              />
            </div>

            {/* Formula Notice */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <p className="text-sm text-gray-600">
                <strong>Formula:</strong> Similarity % = (Matched tokens / Eligible tokens) × 100
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Corpus: {report.corpus_scope}
              </p>
            </div>

            {/* Disclaimer */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <p className="text-sm text-yellow-800">
                <strong>Important:</strong> {report.disclaimer}
              </p>
            </div>
          </div>

          {/* Full Document Word-Style Highlighter Viewer */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Full Document Text with All Highlights */}
            <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6 flex flex-col h-[700px]">
              <div className="flex justify-between items-center mb-4 pb-3 border-b">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-blue-600" />
                  Full Checked Document (Word-Style Inline Highlights)
                </h3>
                <span className="text-xs bg-yellow-100 text-yellow-800 px-2.5 py-1 rounded font-medium">
                  Yellow = Near-exact • Red = Exact match
                </span>
              </div>

              {/* Full Document Content (All Pages Combined) with Inline Highlights */}
              <div className="flex-1 bg-gray-50 border rounded-lg p-6 overflow-y-auto font-serif text-gray-800 text-sm leading-relaxed whitespace-pre-wrap shadow-inner">
                {submittedDocDetail ? (
                  submittedDocDetail.pages.map((page) => {
                    const pageMatches = report.matches.filter(m => m.submitted_page === page.page_number);
                    return (
                      <div key={page.page_number} className="mb-8 pb-6 border-b border-gray-200 last:border-b-0">
                        <div className="text-xs font-sans font-semibold text-gray-400 mb-2 uppercase tracking-wide">
                          --- Page {page.page_number} ---
                        </div>
                        <PlagiarismHighlighter
                          text={page.text_preview}
                          matches={pageMatches}
                          selectedMatch={selectedMatch}
                          onSelectMatch={setSelectedMatch}
                        />
                      </div>
                    );
                  })
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-400">
                    <Loader2 className="w-6 h-6 animate-spin mr-2" /> Loading full document text...
                  </div>
                )}
              </div>
              <p className="text-xs text-gray-500 mt-3 text-center">
                💡 Click any highlighted passage to view source attribution in the sidebar.
              </p>
            </div>

            {/* Right Col: Match List & Source Attribution Sidebar */}
            <div className="bg-white border border-gray-200 rounded-lg p-6 flex flex-col h-[700px]">
              <h3 className="font-semibold text-gray-900 mb-3 pb-3 border-b flex items-center justify-between">
                <span>Matched Passages</span>
                <span className="text-xs bg-gray-100 text-gray-700 px-2.5 py-1 rounded-full font-medium">
                  {report.matches.length} total
                </span>
              </h3>

              <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                {report.matches.length === 0 ? (
                  <p className="text-sm text-gray-500 text-center py-8">No similarity matches detected.</p>
                ) : (
                  report.matches.map((match, idx) => {
                    const isSelected = selectedMatch === match;
                    const typeStyle = MATCH_TYPE_LABELS[match.match_type] || MATCH_TYPE_LABELS.exact;

                    return (
                      <div
                        key={idx}
                        onClick={() => setSelectedMatch(match)}
                        className={`p-3 border rounded-lg cursor-pointer transition-all text-left ${
                          isSelected ? 'border-blue-500 bg-blue-50 shadow-sm' : 'border-gray-200 hover:bg-gray-50'
                        }`}
                      >
                        <div className="flex items-center justify-between mb-1.5">
                          <span className={`px-2 py-0.5 text-xs font-medium rounded border ${typeStyle.badge}`}>
                            {match.match_type} (p. {match.submitted_page})
                          </span>
                          <span className="text-xs font-semibold text-gray-700">
                            {(match.similarity * 100).toFixed(0)}% sim
                          </span>
                        </div>
                        <p className="text-xs font-medium text-gray-900 mb-1">
                          Source: {match.source_title} (p. {match.source_page})
                        </p>
                        <p className="text-xs text-gray-600 bg-white p-2 rounded border line-clamp-2 italic">
                          "{match.submitted_text}"
                        </p>
                      </div>
                    );
                  })
                )}
              </div>

              {/* Selected Match Details Box */}
              {selectedMatch && (
                <div className="mt-4 pt-3 border-t bg-blue-50/50 p-3 rounded-lg text-xs">
                  <p className="font-semibold text-blue-900 mb-1">Source Excerpt ({selectedMatch.source_title}):</p>
                  <p className="text-gray-700 italic bg-white p-2 rounded border line-clamp-4">
                    "{selectedMatch.source_text}"
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-4">
            <button
              onClick={handleReset}
              className="flex-1 py-3 px-4 border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50"
            >
              Check Another Document
            </button>
            <button
              onClick={() => {
                const blob = new Blob([JSON.stringify(report, null, 2)], {
                  type: 'application/json',
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `plagiarism-report-${report.report_id}.json`;
                a.click();
              }}
              className="flex-1 py-3 px-4 bg-gray-900 text-white font-medium rounded-lg hover:bg-gray-800 flex items-center justify-center gap-2"
            >
              <Download className="w-5 h-5" />
              Download Report JSON
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Component: Metric Card
function MetricCard({
  label,
  value,
  description,
}: {
  label: string;
  value: string;
  description: string;
}) {
  return (
    <div className="text-center p-4 bg-gray-50 rounded-lg">
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm font-medium text-gray-700">{label}</p>
      <p className="text-xs text-gray-500">{description}</p>
    </div>
  );
}

// Component: Word-Style Inline Plagiarism Highlighter
function PlagiarismHighlighter({
  text,
  matches,
  selectedMatch,
  onSelectMatch,
}: {
  text: string;
  matches: PlagiarismMatch[];
  selectedMatch: PlagiarismMatch | null;
  onSelectMatch: (m: PlagiarismMatch) => void;
}) {
  if (!matches || matches.length === 0) {
    return <span>{text}</span>;
  }

  const validMatches = matches.filter(m => m.submitted_text && text.includes(m.submitted_text));
  if (validMatches.length === 0) {
    return <span>{text}</span>;
  }

  // Sort matches by appearance in text
  const sorted = [...validMatches].sort((a, b) => {
    return text.indexOf(a.submitted_text) - text.indexOf(b.submitted_text);
  });

  let lastIndex = 0;
  const elements: React.ReactNode[] = [];

  sorted.forEach((match, idx) => {
    const snippet = match.submitted_text;
    const index = text.indexOf(snippet, lastIndex);

    if (index !== -1) {
      if (index > lastIndex) {
        elements.push(<span key={`text-${idx}`}>{text.substring(lastIndex, index)}</span>);
      }

      const isSelected = selectedMatch === match;
      const highlightColor = match.match_type === 'exact'
        ? (isSelected ? 'bg-red-500 text-white ring-2 ring-red-700 font-bold shadow-md' : 'bg-red-300 text-red-950 hover:bg-red-400 font-medium')
        : (isSelected ? 'bg-yellow-400 text-gray-900 ring-2 ring-yellow-600 font-bold shadow-md' : 'bg-yellow-200 text-yellow-950 hover:bg-yellow-300 font-medium');

      elements.push(
        <mark
          key={`match-${idx}`}
          onClick={() => onSelectMatch(match)}
          className={`cursor-pointer px-1 py-0.5 rounded transition-all ${highlightColor}`}
          title={`Match: ${match.match_type} (${(match.similarity * 100).toFixed(0)}% similarity with ${match.source_title})`}
        >
          {snippet}
        </mark>
      );

      lastIndex = index + snippet.length;
    }
  });

  if (lastIndex < text.length) {
    elements.push(<span key="text-end">{text.substring(lastIndex)}</span>);
  }

  return <>{elements}</>;
}

export default PlagiarismChecker;