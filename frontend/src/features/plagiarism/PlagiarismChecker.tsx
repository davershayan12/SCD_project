import React, { useState, useRef } from 'react';
import { AlertCircle, CheckCircle, FileText, Upload, Loader2, Download, Trash2 } from 'lucide-react';

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

// Constants
const CORPUS_DISCLAIMER = 'This checker only compares against documents you have uploaded. It does not search the internet, paywalled journals, or Turnitin\'s private corpus.';

const MATCH_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  exact: { label: 'Exact text match', color: 'bg-red-100 text-red-800 border-red-200' },
  'near-exact': { label: 'Near-exact match', color: 'bg-yellow-100 text-yellow-800 border-yellow-200' },
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
          const report = await response.json();
          setReport(report);
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
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">
          ResearchRadar — Plagiarism & Similarity Checker
        </h1>
        <p className="text-gray-600">
          Upload documents, build your corpus, and run transparent lexical similarity checks.
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

      {/* Step 2: Result */}
      {step === 'result' && report && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Similarity Report
            </h2>

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
                Parameters: k={report.parameters.k}, w={report.parameters.w}, min_tokens={report.parameters.min_tokens}
              </p>
              <p className="text-xs text-gray-500">
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

          {/* Matches List */}
          {report.matches.length > 0 ? (
            <div className="bg-white border border-gray-200 rounded-lg p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">
                Detected Matches ({report.matches.length})
              </h3>

              <div className="space-y-4">
                {report.matches.map((match, index) => (
                  <MatchCard key={index} match={match} />
                ))}
              </div>
            </div>
          ) : (
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
              <CheckCircle className="w-12 h-12 text-green-600 mx-auto mb-3" />
              <h3 className="text-lg font-medium text-green-900 mb-1">
                No Matches Found
              </h3>
              <p className="text-green-700">
                Your document did not contain any significant similarities with
                other documents in your corpus.
              </p>
            </div>
          )}

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
              Download Report
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

// Component: Match Card
function MatchCard({ match }: { match: PlagiarismMatch }) {
  const [expanded, setExpanded] = useState(false);
  const typeStyle = MATCH_TYPE_LABELS[match.match_type] || MATCH_TYPE_LABELS.exact;

  return (
    <div className={`border rounded-lg overflow-hidden ${typeStyle.color}`}>
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-3 flex items-center justify-between text-left"
      >
        <div>
          <span className="inline-block px-2 py-0.5 text-xs font-medium rounded border">
            {typeStyle.label}
          </span>
          <span className="ml-3 text-sm text-gray-700">
            Source: <strong>{match.source_title}</strong> (page {match.source_page})
          </span>
          <span className="ml-2 text-sm text-gray-500">
            Similarity: {(match.similarity * 100).toFixed(0)}%
          </span>
        </div>
        <span className="text-sm text-gray-500">
          {expanded ? 'Hide' : 'Show'} details
        </span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 border-t border-current/20">
          <div className="grid md:grid-cols-2 gap-4 mt-4">
            <div>
              <p className="text-xs font-medium uppercase text-gray-600 mb-2">
                Submitted Document
              </p>
              <p className="text-sm bg-white/50 p-3 rounded border border-current/10">
                {match.submitted_text}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Page {match.submitted_page}, tokens {match.submitted_span[0]}-{match.submitted_span[1]}
              </p>
            </div>
            <div>
              <p className="text-xs font-medium uppercase text-gray-600 mb-2">
                Source Document
              </p>
              <p className="text-sm bg-white/50 p-3 rounded border border-current/10">
                {match.source_text}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                Page {match.source_page}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default PlagiarismChecker;