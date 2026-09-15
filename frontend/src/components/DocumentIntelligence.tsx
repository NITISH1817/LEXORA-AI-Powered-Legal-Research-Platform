import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Upload, Clock, CheckCircle2, XCircle, AlertTriangle,
  Loader2, ChevronRight, Trash2, RefreshCw, Eye, Search, Scale,
  Activity, BarChart3, FileWarning, FileScan
} from 'lucide-react';
import axios from 'axios';
import DocumentUpload from './DocumentUpload';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: "Bearer $token" } : {};
};

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ElementType; pulse?: boolean }> = {
  UPLOADED:           { label: 'Uploaded',        color: 'text-slate-400',  bg: 'bg-slate-800',   icon: Clock,          pulse: false },
  VALIDATING:         { label: 'Validating',       color: 'text-blue-400',   bg: 'bg-blue-900/30', icon: Loader2,        pulse: true  },
  EXTRACTING:         { label: 'Extracting',       color: 'text-amber-400',  bg: 'bg-amber-900/30',icon: Activity,       pulse: true  },
  OCR_CHECK:          { label: 'OCR Check',        color: 'text-purple-400', bg: 'bg-purple-900/30',icon: FileScan,      pulse: true  },
  OCR_REQUIRED:       { label: 'OCR Required',     color: 'text-orange-400', bg: 'bg-orange-900/30',icon: FileWarning,   pulse: false },
  PARSING:            { label: 'Parsing',          color: 'text-cyan-400',   bg: 'bg-cyan-900/30', icon: Loader2,        pulse: true  },
  STRUCTURING:        { label: 'Structuring',      color: 'text-indigo-400', bg: 'bg-indigo-900/30',icon: BarChart3,     pulse: true  },
  CHUNKING:           { label: 'Chunking',         color: 'text-teal-400',   bg: 'bg-teal-900/30', icon: Loader2,        pulse: true  },
  EMBEDDING:          { label: 'Embedding',        color: 'text-sky-400',    bg: 'bg-sky-900/30',  icon: Loader2,        pulse: true  },
  INDEXING:           { label: 'Indexing',         color: 'text-violet-400', bg: 'bg-violet-900/30',icon: Loader2,       pulse: true  },
  CITATION_EXTRACT:   { label: 'Citations',        color: 'text-pink-400',   bg: 'bg-pink-900/30', icon: Loader2,        pulse: true  },
  ANALYZING:          { label: 'Analyzing',        color: 'text-yellow-400', bg: 'bg-yellow-900/30',icon: Loader2,       pulse: true  },
  READY:              { label: 'Ready',            color: 'text-emerald-400',bg: 'bg-emerald-900/30',icon: CheckCircle2, pulse: false },
  FAILED:             { label: 'Failed',           color: 'text-red-400',    bg: 'bg-red-900/30',  icon: XCircle,        pulse: false },
};

const IN_PROGRESS_STATUSES = new Set([
  'UPLOADED','VALIDATING','EXTRACTING','OCR_CHECK','PARSING',
  'STRUCTURING','CHUNKING','EMBEDDING','INDEXING','CITATION_EXTRACT',
  'TIMELINE_EXTRACT','ANALYZING'
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
      <div className={"inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold $cfg.color $cfg.bg border border-current/20"}>
        <Icon size={11} className={isActive ? 'animate-spin' : ''} />
        {cfg.label}
      </div>
      {isActive && progress !== undefined && (
        <div className="flex items-center gap-2">
          <div className="flex-1 h-1 bg-slate-800 rounded-full overflow-hidden">
            <motion.div
              className="h-full bg-gradient-to-r from-blue-500 to-violet-500 rounded-full"
              initial={{ width: 0 }}
              animate={{ width: "%" }}
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
  if (bytes < 1024) return "${bytes} B";
  if (bytes < 1024 * 1024) return "${(bytes / 1024).toFixed(1)} KB";
  return "${(bytes / (1024 * 1024)).toFixed(1)} MB";
}

function formatDate(dateStr?: string): string {
  if (!dateStr) return '—';
  const d = new Date(dateStr);
  const now = new Date();
  const diff = now.getTime() - d.getTime();
  if (diff < 60000) return 'Just now';
  if (diff < 3600000) return "${Math.floor(diff / 60000)}m ago";
  if (diff < 86400000) return "${Math.floor(diff / 3600000)}h ago";
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export default function DocumentIntelligence() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingId, setDeletingId] = useState<number | null>(null);
  const [retryingId, setRetryingId] = useState<number | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchDocuments = useCallback(async () => {
    try {
      const res = await axios.get("${API_URL}/api/documents", {
        headers: getAuthHeader()
      });
      setDocuments(res.data);
    } catch (err) {
      console.error('Failed to fetch documents', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const pollStatus = useCallback(async () => {
    const inProgress = documents.filter(d => IN_PROGRESS_STATUSES.has(d.status));
    if (inProgress.length === 0) return;

    const updates = await Promise.allSettled(
      inProgress.map(doc =>
        axios.get("${API_URL}/api/documents//status", {
          headers: getAuthHeader()
        })
      )
    );

    setDocuments(prev => prev.map((doc, i) => {
      const idx = inProgress.findIndex(d => d.id === doc.id);
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
    }));
  }, [documents]);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    const hasActive = documents.some(d => IN_PROGRESS_STATUSES.has(d.status));
    if (hasActive && !pollRef.current) {
      pollRef.current = setInterval(pollStatus, 3000);
    } else if (!hasActive && pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
      fetchDocuments();
    }
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [documents, pollStatus, fetchDocuments]);

  const handleDelete = async (id: number) => {
    if (!confirm('Delete this document and all its data? This cannot be undone.')) return;
    setDeletingId(id);
    try {
      await axios.delete("${API_URL}/api/documents/", {
        headers: getAuthHeader()
      });
      setDocuments(prev => prev.filter(d => d.id !== id));
    } catch {
      alert('Could not delete document.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleRetry = async (id: number) => {
    setRetryingId(id);
    try {
      await axios.post("${API_URL}/api/documents//retry", {}, {
        headers: getAuthHeader()
      });
      setDocuments(prev => prev.map(d =>
        d.id === id ? { ...d, status: 'UPLOADED', progress: 0 } : d
      ));
    } catch {
      alert('Could not retry processing.');
    } finally {
      setRetryingId(null);
    }
  };

  const handleOpenDocument = (id: number) => {
    window.location.href = "/documents/";
  };

  const handleUploadComplete = () => {
    setShowUpload(false);
    fetchDocuments();
  };

  const filtered = documents.filter(d => {
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
    ready: documents.filter(d => d.status === 'READY').length,
    processing: documents.filter(d => IN_PROGRESS_STATUSES.has(d.status)).length,
    failed: documents.filter(d => d.status === 'FAILED').length,
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 font-['Inter',sans-serif]">
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-violet-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <button
                onClick={() => window.location.href = '/'}
                className="text-slate-500 hover:text-slate-300 text-sm transition-colors"
              >
                ← Research Workspace
              </button>
            </div>
            <h1 className="text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 flex items-center justify-center">
                <FileText size={18} />
              </div>
              Document Intelligence
            </h1>
            <p className="text-slate-400 mt-1 text-sm">
              Upload, process, and analyze legal documents with AI-powered extraction
            </p>
          </div>
          <button
            onClick={() => setShowUpload(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-lg font-semibold text-sm transition-all shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 hover:scale-105"
          >
            <Upload size={16} />
            Upload Document
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total', value: stats.total, color: 'text-slate-300', icon: FileText },
            { label: 'Ready', value: stats.ready, color: 'text-emerald-400', icon: CheckCircle2 },
            { label: 'Processing', value: stats.processing, color: 'text-blue-400', icon: Activity },
            { label: 'Failed', value: stats.failed, color: 'text-red-400', icon: XCircle },
          ].map(({ label, value, color, icon: Icon }) => (
            <div key={label} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 backdrop-blur-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500 text-xs font-medium uppercase tracking-wider">{label}</span>
                <Icon size={14} className={color} />
              </div>
              <div className={"text-2xl font-bold $color"}>{value}</div>
            </div>
          ))}
        </div>

        <div className="relative mb-6">
          <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            placeholder="Search documents by name, case, or type..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            className="w-full pl-11 pr-4 py-3 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 text-sm focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all"
          />
        </div>

        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden backdrop-blur-sm">
          <div className="grid grid-cols-[2.5fr_1.5fr_0.8fr_1.5fr_1fr_1.2fr] px-6 py-3 border-b border-slate-800 text-xs font-semibold text-slate-500 uppercase tracking-wider">
            <span>Document</span>
            <span>Status</span>
            <span>Pages</span>
            <span>Case</span>
            <span>Uploaded</span>
            <span className="text-right">Actions</span>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 size={24} className="animate-spin text-blue-400" />
              <span className="ml-3 text-slate-400">Loading documents...</span>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500">
              <FileText size={48} className="mb-4 opacity-30" />
              {searchQuery ? (
                <p>No documents match your search.</p>
              ) : (
                <>
                  <p className="text-base font-medium mb-2">No documents yet</p>
                  <p className="text-sm">Upload your first legal document to get started</p>
                  <button
                    onClick={() => setShowUpload(true)}
                    className="mt-4 flex items-center gap-2 px-4 py-2 bg-blue-600/20 border border-blue-500/30 text-blue-400 rounded-lg text-sm hover:bg-blue-600/30 transition-colors"
                  >
                    <Upload size={14} />
                    Upload Document
                  </button>
                </>
              )}
            </div>
          ) : (
            <AnimatePresence>
              {filtered.map((doc, idx) => (
                <motion.div
                  key={doc.id}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  transition={{ delay: idx * 0.03 }}
                  className="grid grid-cols-[2.5fr_1.5fr_0.8fr_1.5fr_1fr_1.2fr] px-6 py-4 border-b border-slate-800/50 hover:bg-slate-800/20 transition-colors items-center"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className={"w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 $
                      doc.document_type === 'pdf' ? 'bg-red-500/10 text-red-400' :
                      doc.document_type === 'docx' ? 'bg-blue-500/10 text-blue-400' :
                      'bg-slate-700 text-slate-400'
                    "}>
                      <FileText size={14} />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-slate-200 truncate">{doc.title}</p>
                      <p className="text-xs text-slate-500 truncate">
                        {doc.original_filename}
                        {doc.version_number && doc.version_number > 1 && (
                          <span className="ml-2 px-1.5 py-0.5 bg-slate-700 rounded text-slate-400">v{doc.version_number}</span>
                        )}
                        {doc.file_size_bytes && (
                          <span className="ml-2">{formatFileSize(doc.file_size_bytes)}</span>
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

                  <div className="text-sm text-slate-400">
                    {doc.page_count ? "${doc.page_count}" : '—'}
                  </div>

                  <div className="min-w-0">
                    {doc.case_name ? (
                      <div className="flex items-center gap-1.5 text-xs text-slate-400 truncate">
                        <Scale size={11} className="text-blue-400 flex-shrink-0" />
                        <span className="truncate">{doc.case_name}</span>
                      </div>
                    ) : (
                      <span className="text-slate-600 text-xs">No case linked</span>
                    )}
                  </div>

                  <div className="text-xs text-slate-500">
                    {formatDate(doc.uploaded_at)}
                  </div>

                  <div className="flex items-center gap-1.5 justify-end">
                    <button
                      onClick={() => handleOpenDocument(doc.id)}
                      className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
                    >
                      <Eye size={12} />
                      Open
                    </button>

                    {doc.status === 'FAILED' && (
                      <button
                        onClick={() => handleRetry(doc.id)}
                        disabled={retryingId === doc.id}
                        className="flex items-center gap-1.5 px-3 py-1.5 text-xs bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <RefreshCw size={12} className={retryingId === doc.id ? 'animate-spin' : ''} />
                        Retry
                      </button>
                    )}

                    <button
                      onClick={() => handleDelete(doc.id)}
                      disabled={deletingId === doc.id}
                      className="p-1.5 text-slate-600 hover:text-red-400 hover:bg-red-500/10 rounded-lg transition-colors disabled:opacity-50"
                      title="Delete document"
                    >
                      {deletingId === doc.id ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : (
                        <Trash2 size={13} />
                      )}
                    </button>
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          )}
        </div>

        {filtered.length > 0 && (
          <p className="text-center text-slate-600 text-xs mt-4">
            {filtered.length} document{filtered.length !== 1 ? 's' : ''}
            {searchQuery && " matching ""}
          </p>
        )}
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