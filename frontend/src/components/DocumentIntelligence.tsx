import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import {
  FileText, Upload, Clock, CheckCircle2, XCircle,
  Loader2, Trash2, RefreshCw, Eye, Search, Scale,
  Activity, BarChart3, FileWarning, FileScan, AlertCircle
} from 'lucide-react';
import DocumentUpload from './DocumentUpload';
import AppNavbar from './common/AppNavbar';
import apiClient, { getErrorMessage } from '../api/client';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ElementType }> = {
  UPLOADED:         { label: 'Uploaded',        color: 'text-slate-400',  bg: 'bg-slate-800/80',   icon: Clock },
  VALIDATING:       { label: 'Validating',       color: 'text-blue-400',   bg: 'bg-blue-900/30',    icon: Loader2 },
  EXTRACTING:       { label: 'Extracting',       color: 'text-amber-400',  bg: 'bg-amber-900/30',   icon: Activity },
  OCR_CHECK:        { label: 'OCR Check',        color: 'text-purple-400', bg: 'bg-purple-900/30',  icon: FileScan },
  OCR_REQUIRED:     { label: 'OCR Required',     color: 'text-orange-400', bg: 'bg-orange-900/30',  icon: FileWarning },
  PARSING:          { label: 'Parsing',          color: 'text-cyan-400',   bg: 'bg-cyan-900/30',    icon: Loader2 },
  STRUCTURING:      { label: 'Structuring',      color: 'text-indigo-400', bg: 'bg-indigo-900/30',  icon: BarChart3 },
  CHUNKING:         { label: 'Chunking',         color: 'text-teal-400',   bg: 'bg-teal-900/30',    icon: Loader2 },
  EMBEDDING:        { label: 'Embedding',        color: 'text-sky-400',    bg: 'bg-sky-900/30',     icon: Loader2 },
  INDEXING:         { label: 'Indexing',         color: 'text-violet-400', bg: 'bg-violet-900/30',  icon: Loader2 },
  CITATION_EXTRACT: { label: 'Citations',        color: 'text-pink-400',   bg: 'bg-pink-900/30',    icon: Loader2 },
  ANALYZING:        { label: 'Analyzing',        color: 'text-yellow-400', bg: 'bg-yellow-900/30',  icon: Loader2 },
  READY:            { label: 'Ready',            color: 'text-emerald-400',bg: 'bg-emerald-900/30', icon: CheckCircle2 },
  FAILED:           { label: 'Failed',           color: 'text-red-400',    bg: 'bg-red-900/30',     icon: XCircle },
};

const IN_PROGRESS_STATUSES = new Set([
  'UPLOADED', 'VALIDATING', 'EXTRACTING', 'OCR_CHECK', 'PARSING',
  'STRUCTURING', 'CHUNKING', 'EMBEDDING', 'INDEXING', 'CITATION_EXTRACT',
  'TIMELINE_EXTRACT', 'ANALYZING',
]);

interface DocumentItem {
  id: number;
  title: string;
  original_filename?: string;
  document_type?: string;
  status: string;
  page_count?: number;
  file_size_bytes?: number;
  version_number?: number;
  uploaded_at?: string;
  case_id?: number;
  case_name?: string;
  progress?: number;
  current_stage?: string;
}

function StatusPill({ status, progress, currentStage }: { status: string; progress?: number; currentStage?: string }) {
  const cfg = STATUS_CONFIG[status] || STATUS_CONFIG['UPLOADED'];
  const Icon = cfg.icon;
  const isActive = IN_PROGRESS_STATUSES.has(status);

  return (
    <div className="flex flex-col gap-1">
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.color} ${cfg.bg} border border-current/20`}>
        <Icon size={11} className={isActive ? 'animate-spin' : ''} />
        {cfg.label}
      </div>
      {isActive && progress !== undefined && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-blue-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: `${Math.round(progress)}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
          <span className="text-[10px] text-slate-500 font-mono">{Math.round(progress)}%</span>
        </div>
      )}
      {isActive && currentStage && (
        <span className="text-[10px] text-slate-500 truncate max-w-[180px]">{currentStage}</span>
      )}
    </div>
  );
}

function formatFileSize(bytes?: number): string {
  if (!bytes) return '—';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function DocumentIntelligence() {
  const navigate = useNavigate();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await apiClient.get<DocumentItem[]>('/api/documents');
      setDocuments(res.data || []);
    } catch (err: unknown) {
      setError(getErrorMessage(err, 'Failed to fetch document catalog.'));
    } finally {
      setLoading(false);
    }
  }, []);

  const pollStatus = useCallback(async () => {
    const inProgress = documents.filter((d) => IN_PROGRESS_STATUSES.has(d.status));
    if (inProgress.length === 0) return;

    const updates = await Promise.allSettled(
      inProgress.map((doc) => apiClient.get(`/api/documents/${doc.id}/status`))
    );

    setDocuments((prev) =>
      prev.map((doc) => {
        const idx = inProgress.findIndex((d) => d.id === doc.id);
        if (idx === -1) return doc;
        const result = updates[idx];
        if (result.status === 'fulfilled') {
          const data = result.value.data;
          return {
            ...doc,
            status: data.status,
            progress: data.progress,
            current_stage: data.current_stage,
            page_count: data.total_pages || doc.page_count,
          };
        }
        return doc;
      })
    );
  }, [documents]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    const hasActive = documents.some((d) => IN_PROGRESS_STATUSES.has(d.status));
    if (hasActive && !pollRef.current) {
      pollRef.current = setInterval(pollStatus, 3000);
    } else if (!hasActive && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
      fetchDocuments();
    }
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [documents, pollStatus, fetchDocuments]);

  const handleDelete = async (id: number) => {
    if (!window.confirm('Delete this document and all its data? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await apiClient.delete(`/api/documents/${id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Could not delete document.'));
    } finally {
      setDeletingId(null);
    }
  };

  const handleRetry = async (id: number) => {
    setRetryingId(id);
    try {
      await apiClient.post(`/api/documents/${id}/retry`, {});
      setDocuments((prev) =>
        prev.map((d) => (d.id === id ? { ...d, status: 'UPLOADED', progress: 0 } : d))
      );
    } catch (err: unknown) {
      alert(getErrorMessage(err, 'Could not retry processing.'));
    } finally {
      setRetryingId(null);
    }
  };

  const handleOpenDocument = (id: number) => {
    navigate(`/documents/${id}`);
  };

  const handleUploadComplete = () => {
    setShowUpload(false);
    fetchDocuments();
  };

  const filtered = documents.filter((d) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      d.title?.toLowerCase().includes(q) ||
      d.case_name?.toLowerCase().includes(q) ||
      d.document_type?.toLowerCase().includes(q)
    );
  });

  const stats = {
    total: documents.length,
    ready: documents.filter((d) => d.status === 'READY').length,
    processing: documents.filter((d) => IN_PROGRESS_STATUSES.has(d.status)).length,
    failed: documents.filter((d) => d.status === 'FAILED').length,
  };

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 font-sans flex flex-col">
      <AppNavbar />

      <div className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <h1 className="text-2xl md:text-3xl font-serif font-bold text-white flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 flex items-center justify-center shadow-lg shadow-blue-500/20">
                <FileText size={18} className="text-white" />
              </div>
              <span>Document Intelligence & Ingestion</span>
            </h1>
            <p className="text-slate-400 mt-1 text-xs">
              Upload, parse, chunk, embed, and extract structured legal intelligence from transcripts and pleadings.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium text-xs transition-all shadow-md shadow-blue-500/20"
          >
            <Upload size={15} />
            <span>Upload Document</span>
          </button>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle size={16} className="text-rose-400 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Ingested', value: stats.total, color: 'text-slate-200', icon: FileText },
            { label: 'Ready & Indexed', value: stats.ready, color: 'text-emerald-400', icon: CheckCircle2 },
            { label: 'In Pipeline', value: stats.processing, color: 'text-blue-400', icon: Activity },
            { label: 'Failed Processing', value: stats.failed, color: 'text-rose-400', icon: XCircle },
          ].map(({ label, value, color, icon: Icon }) => (
            <div key={label} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-slate-500 text-[10px] font-bold uppercase tracking-wider">{label}</span>
                <Icon size={14} className={color} />
              </div>
              <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
            </div>
          ))}
        </div>

        {/* Search Bar */}
        <div className="relative mb-6">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search documents by title, case name, or file type..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-2.5 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
          />
        </div>

        {/* Document Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="grid grid-cols-[2.5fr_1.5fr_0.8fr_1.5fr_1fr_1.2fr] px-6 py-3 border-b border-slate-800 text-[10px] font-bold text-slate-500 uppercase tracking-wider">
            <span>Document</span>
            <span>Pipeline Status</span>
            <span>Pages</span>
            <span>Case Relation</span>
            <span>Uploaded</span>
            <span className="text-right">Actions</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20 text-slate-400 gap-3">
              <Loader2 size={24} className="animate-spin text-blue-500" />
              <span className="text-xs">Loading document intelligence records...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
              <FileText size={48} className="mb-4 opacity-20 text-blue-400" />
              {searchQuery ? (
                <p className="text-sm">No documents match "{searchQuery}".</p>
              ) : (
                <>
                  <p className="text-base font-semibold text-slate-300 mb-1">No documents in catalog</p>
                  <p className="text-xs text-slate-500 mb-4">
                    Upload your first primary transcript, ruling, or pleading to begin extraction.
                  </p>
                  <button
                    type="button"
                    onClick={() => setShowUpload(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold shadow transition-colors"
                  >
                    <Upload size={14} />
                    <span>Upload Document</span>
                  </button>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              {filtered.map((doc) => (
                <div
                  key={doc.id}
                  className="grid grid-cols-[2.5fr_1.5fr_0.8fr_1.5fr_1fr_1.2fr] px-6 py-4 hover:bg-slate-850/50 transition-colors items-center text-xs"
                >
                  <div className="flex items-center gap-3 min-w-0 pr-4">
                    <div
                      className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
                        doc.document_type === 'pdf'
                          ? 'bg-red-500/10 text-red-400 border border-red-500/20'
                          : doc.document_type === 'docx'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      <FileText size={15} />
                    </div>
                    <div className="min-w-0">
                      <p
                        onClick={() => handleOpenDocument(doc.id)}
                        className="font-semibold text-slate-200 hover:text-blue-400 cursor-pointer truncate"
                      >
                        {doc.title}
                      </p>
                      <p className="text-[10px] text-slate-500 truncate mt-0.5">
                        {doc.original_filename}
                        {doc.version_number && doc.version_number > 1 && (
                          <span className="ml-1.5 px-1 rounded bg-slate-800 text-slate-400 font-mono">
                            v{doc.version_number}
                          </span>
                        )}
                        {doc.file_size_bytes && (
                          <span className="ml-1.5 font-mono">{formatFileSize(doc.file_size_bytes)}</span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div>
                    <StatusPill
                      status={doc.status}
                      progress={doc.progress}
                      currentStage={doc.current_stage}
                    />
                  </div>

                  <div className="font-mono text-slate-400">
                    {doc.page_count ? doc.page_count : '—'}
                  </div>

                  <div className="min-w-0 pr-2">
                    {doc.case_name ? (
                      <div className="flex items-center gap-1.5 text-slate-300 truncate">
                        <Scale size={12} className="text-blue-400 shrink-0" />
                        <span className="truncate">{doc.case_name}</span>
                      </div>
                    ) : (
                      <span className="text-slate-600">Unlinked</span>
                    )}
                  </div>

                  <div className="text-slate-500 font-mono text-[11px]">
                    {formatDate(doc.uploaded_at)}
                  </div>

                  <div className="flex items-center gap-1.5 justify-end">
                    <button
                      type="button"
                      onClick={() => handleOpenDocument(doc.id)}
                      className="px-2.5 py-1 text-xs bg-slate-800 hover:bg-slate-750 text-slate-300 rounded-md transition-colors flex items-center gap-1"
                    >
                      <Eye size={12} />
                      <span>Open</span>
                    </button>

                    {doc.status === 'FAILED' && (
                      <button
                        type="button"
                        onClick={() => handleRetry(doc.id)}
                        disabled={retryingId === doc.id}
                        className="px-2.5 py-1 text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 rounded-md transition-colors disabled:opacity-50 flex items-center gap-1"
                      >
                        <RefreshCw size={12} className={retryingId === doc.id ? 'animate-spin' : ''} />
                        <span>Retry</span>
                      </button>
                    )}

                    <button
                      type="button"
                      onClick={() => handleDelete(doc.id)}
                      disabled={deletingId === doc.id}
                      className="p-1.5 text-slate-500 hover:text-rose-400 hover:bg-rose-500/10 rounded-md transition-colors disabled:opacity-50"
                      title="Delete document"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Trash2 size={13} />
                      )}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <AnimatePresence>
        {showUpload && (
          <DocumentUpload
            onClose={() => setShowUpload(false)}
            onComplete={handleUploadComplete}
          />
        )}
      </AnimatePresence>
    </div>
  );
}