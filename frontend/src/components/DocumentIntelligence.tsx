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
import Button from './ui/Button';
import ConfirmDialog from './ui/ConfirmDialog';
import { Skeleton } from './ui/Skeleton';
import { useToast } from '../hooks/useToast';

const STATUS_CONFIG: Record<string, { label: string; color: string; bg: string; icon: React.ElementType; badgeVariant: any }> = {
  UPLOADED:         { label: 'Uploaded',        color: 'text-slate-400',  bg: 'bg-slate-800/80',   icon: Clock, badgeVariant: 'neutral' },
  VALIDATING:       { label: 'Validating',       color: 'text-blue-400',   bg: 'bg-blue-900/30',    icon: Loader2, badgeVariant: 'info' },
  EXTRACTING:       { label: 'Extracting',       color: 'text-amber-400',  bg: 'bg-amber-900/30',   icon: Activity, badgeVariant: 'warning' },
  OCR_CHECK:        { label: 'OCR Check',        color: 'text-purple-400', bg: 'bg-purple-900/30',  icon: FileScan, badgeVariant: 'accent' },
  OCR_REQUIRED:     { label: 'OCR Required',     color: 'text-orange-400', bg: 'bg-orange-900/30',  icon: FileWarning, badgeVariant: 'warning' },
  PARSING:          { label: 'Parsing',          color: 'text-cyan-400',   bg: 'bg-cyan-900/30',    icon: Loader2, badgeVariant: 'info' },
  STRUCTURING:      { label: 'Structuring',      color: 'text-indigo-400', bg: 'bg-indigo-900/30',  icon: BarChart3, badgeVariant: 'accent' },
  CHUNKING:         { label: 'Chunking',         color: 'text-teal-400',   bg: 'bg-teal-900/30',    icon: Loader2, badgeVariant: 'info' },
  EMBEDDING:        { label: 'Embedding',        color: 'text-sky-400',    bg: 'bg-sky-900/30',     icon: Loader2, badgeVariant: 'info' },
  INDEXING:         { label: 'Indexing',         color: 'text-violet-400', bg: 'bg-violet-900/30',  icon: Loader2, badgeVariant: 'accent' },
  CITATION_EXTRACT: { label: 'Citations',        color: 'text-pink-400',   bg: 'bg-pink-900/30',    icon: Loader2, badgeVariant: 'accent' },
  ANALYZING:        { label: 'Analyzing',        color: 'text-yellow-400', bg: 'bg-yellow-900/30',  icon: Loader2, badgeVariant: 'warning' },
  READY:            { label: 'Ready',            color: 'text-emerald-400',bg: 'bg-emerald-900/30', icon: CheckCircle2, badgeVariant: 'success' },
  FAILED:           { label: 'Failed',           color: 'text-rose-400',   bg: 'bg-rose-900/30',    icon: XCircle, badgeVariant: 'error' },
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
      <div className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${cfg.color} ${cfg.bg} border border-current/20 select-none`}>
        <Icon size={11} className={isActive ? 'animate-spin' : ''} />
        <span>{cfg.label}</span>
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
  const toast = useToast();
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [typeFilter, setTypeFilter] = useState<string>('ALL');

  // Deletion state
  const [confirmDeleteDoc, setConfirmDeleteDoc] = useState<DocumentItem | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
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
    let isMounted = true;
    apiClient.get<DocumentItem[]>('/api/documents')
      .then((res) => {
        if (isMounted) setDocuments(res.data || []);
      })
      .catch((err: unknown) => {
        if (isMounted) setError(getErrorMessage(err, 'Failed to fetch document catalog.'));
      })
      .finally(() => {
        if (isMounted) setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, []);

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

  const handleDelete = async () => {
    if (!confirmDeleteDoc) return;
    setIsDeleting(true);
    try {
      await apiClient.delete(`/api/documents/${confirmDeleteDoc.id}`);
      setDocuments((prev) => prev.filter((d) => d.id !== confirmDeleteDoc.id));
      toast.success(`"${confirmDeleteDoc.title}" deleted successfully.`);
      setConfirmDeleteDoc(null);
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Could not delete document.'));
    } finally {
      setIsDeleting(false);
    }
  };

  const handleRetry = async (id: number) => {
    setRetryingId(id);
    try {
      await apiClient.post(`/api/documents/${id}/retry`, {});
      setDocuments((prev) =>
        prev.map((d) => (d.id === id ? { ...d, status: 'UPLOADED', progress: 0 } : d))
      );
      toast.info('Ingestion retry initiated.');
    } catch (err: unknown) {
      toast.error(getErrorMessage(err, 'Could not retry processing.'));
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
    toast.success('Document uploaded and scheduled for legal indexing.');
  };

  const filtered = documents.filter((d) => {
    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const match =
        d.title?.toLowerCase().includes(q) ||
        d.case_name?.toLowerCase().includes(q) ||
        d.document_type?.toLowerCase().includes(q) ||
        d.original_filename?.toLowerCase().includes(q);
      if (!match) return false;
    }

    // Status filter
    if (statusFilter !== 'ALL') {
      if (statusFilter === 'READY' && d.status !== 'READY') return false;
      if (statusFilter === 'FAILED' && d.status !== 'FAILED') return false;
      if (statusFilter === 'PROCESSING' && !IN_PROGRESS_STATUSES.has(d.status)) return false;
    }

    // Type filter
    if (typeFilter !== 'ALL') {
      if (d.document_type?.toLowerCase() !== typeFilter.toLowerCase()) return false;
    }

    return true;
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

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-8">
        {/* Page Header */}
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

          <Button
            variant="primary"
            size="md"
            icon={<Upload size={15} />}
            onClick={() => setShowUpload(true)}
          >
            Upload Document
          </Button>
        </div>

        {error && (
          <div
            role="alert"
            className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2"
          >
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

        {/* Controls: Search & Filters */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 mb-6">
          <div className="relative flex-1">
            <Search size={16} className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search documents by title, case name, or file type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-11 pr-4 py-2.5 bg-slate-900/50 border border-slate-800 rounded-xl text-slate-200 placeholder-slate-500 text-xs sm:text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-2 text-xs">
            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-3 py-2.5 outline-none focus:border-blue-500 text-xs"
              aria-label="Filter by processing status"
            >
              <option value="ALL">All Statuses</option>
              <option value="READY">Ready & Indexed</option>
              <option value="PROCESSING">Processing</option>
              <option value="FAILED">Failed</option>
            </select>

            {/* Format Filter */}
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="bg-slate-900 border border-slate-800 text-slate-300 rounded-xl px-3 py-2.5 outline-none focus:border-blue-500 text-xs"
              aria-label="Filter by document format"
            >
              <option value="ALL">All Formats</option>
              <option value="pdf">PDF Documents</option>
              <option value="docx">DOCX Briefs</option>
              <option value="txt">TXT Transcripts</option>
            </select>
          </div>
        </div>

        {/* Document Table */}
        <div className="bg-slate-900/40 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
          <div className="hidden lg:grid lg:grid-cols-[2.5fr_1.5fr_0.8fr_1.5fr_1fr_1.2fr] px-6 py-3 border-b border-slate-800 text-[10px] font-bold text-slate-500 uppercase tracking-wider font-mono">
            <span>Document</span>
            <span>Pipeline Status</span>
            <span>Pages</span>
            <span>Case Relation</span>
            <span>Uploaded</span>
            <span className="text-right">Actions</span>
          </div>

          {loading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-slate-950/40 rounded-xl gap-4">
                  <div className="flex items-center gap-3 flex-1">
                    <Skeleton variant="rectangular" width={32} height={32} />
                    <div className="space-y-1.5 flex-1">
                      <Skeleton variant="text" width="40%" height={14} />
                      <Skeleton variant="text" width="20%" height={10} />
                    </div>
                  </div>
                  <Skeleton variant="rectangular" width={100} height={24} />
                </div>
              ))}
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 text-slate-500 p-6 text-center">
              <FileText size={48} className="mb-4 opacity-20 text-blue-400" />
              {searchQuery || statusFilter !== 'ALL' || typeFilter !== 'ALL' ? (
                <div>
                  <p className="text-sm font-semibold text-slate-300 mb-1">No matching documents found</p>
                  <p className="text-xs text-slate-500 mb-4">
                    Try adjusting your search query or reset active filters.
                  </p>
                  <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                      setSearchQuery('');
                      setStatusFilter('ALL');
                      setTypeFilter('ALL');
                    }}
                  >
                    Clear Filters
                  </Button>
                </div>
              ) : (
                <>
                  <p className="text-base font-semibold text-slate-300 mb-1">No documents in catalog</p>
                  <p className="text-xs text-slate-500 mb-4">
                    Upload your first primary transcript, ruling, or pleading to begin extraction.
                  </p>
                  <Button
                    variant="primary"
                    size="sm"
                    icon={<Upload size={14} />}
                    onClick={() => setShowUpload(true)}
                  >
                    Upload Document
                  </Button>
                </>
              )}
            </div>
          ) : (
            <div className="divide-y divide-slate-800/60">
              {filtered.map((doc) => (
                <div
                  key={doc.id}
                  className="flex flex-col lg:grid lg:grid-cols-[2.5fr_1.5fr_0.8fr_1.5fr_1fr_1.2fr] p-4 sm:px-6 sm:py-4 hover:bg-slate-850/40 transition-colors lg:items-center text-xs gap-3 lg:gap-0"
                >
                  {/* Document Title & File Info */}
                  <div className="flex items-center gap-3 min-w-0 lg:pr-4">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                        doc.document_type === 'pdf'
                          ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                          : doc.document_type === 'docx'
                          ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      <FileText size={16} />
                    </div>
                    <div className="min-w-0 flex-1">
                      <p
                        onClick={() => handleOpenDocument(doc.id)}
                        className="font-semibold text-slate-200 hover:text-blue-400 cursor-pointer truncate text-xs sm:text-sm"
                      >
                        {doc.title}
                      </p>
                      <div className="text-[10px] text-slate-500 truncate mt-0.5 flex items-center gap-2 font-mono">
                        <span>{doc.original_filename}</span>
                        {doc.version_number && doc.version_number > 1 && (
                          <span className="px-1.5 rounded bg-slate-800 text-slate-400">
                            v{doc.version_number}
                          </span>
                        )}
                        {doc.file_size_bytes && (
                          <span>{formatFileSize(doc.file_size_bytes)}</span>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Pipeline Status */}
                  <div className="flex items-center justify-between lg:block">
                    <span className="lg:hidden text-slate-500 text-[10px] uppercase font-mono">Status:</span>
                    <StatusPill
                      status={doc.status}
                      progress={doc.progress}
                      currentStage={doc.current_stage}
                    />
                  </div>

                  {/* Page Count */}
                  <div className="flex items-center justify-between lg:block font-mono text-slate-400">
                    <span className="lg:hidden text-slate-500 text-[10px] uppercase font-mono">Pages:</span>
                    <span>{doc.page_count ? `${doc.page_count} pp` : '—'}</span>
                  </div>

                  {/* Case Association */}
                  <div className="flex items-center justify-between lg:block min-w-0 lg:pr-2">
                    <span className="lg:hidden text-slate-500 text-[10px] uppercase font-mono">Case:</span>
                    {doc.case_name ? (
                      <div className="flex items-center gap-1.5 text-slate-300 truncate">
                        <Scale size={12} className="text-blue-400 shrink-0" />
                        <span className="truncate">{doc.case_name}</span>
                      </div>
                    ) : (
                      <span className="text-slate-600">Unlinked</span>
                    )}
                  </div>

                  {/* Upload Date */}
                  <div className="flex items-center justify-between lg:block text-slate-500 font-mono text-[11px]">
                    <span className="lg:hidden text-slate-500 text-[10px] uppercase font-mono">Uploaded:</span>
                    <span>{formatDate(doc.uploaded_at)}</span>
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center gap-2 justify-end pt-2 lg:pt-0 border-t border-slate-800/40 lg:border-t-0">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<Eye size={12} />}
                      onClick={() => handleOpenDocument(doc.id)}
                    >
                      Open Dossier
                    </Button>

                    {doc.status === 'FAILED' && (
                      <Button
                        variant="outline"
                        size="sm"
                        icon={<RefreshCw size={12} className={retryingId === doc.id ? 'animate-spin' : ''} />}
                        onClick={() => handleRetry(doc.id)}
                        disabled={retryingId === doc.id}
                      >
                        Retry
                      </Button>
                    )}

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setConfirmDeleteDoc(doc)}
                      className="text-slate-500 hover:text-rose-400 p-1.5"
                      title="Delete document"
                      aria-label={`Delete ${doc.title}`}
                    >
                      <Trash2 size={13} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      {/* Upload Modal */}
      <AnimatePresence>
        {showUpload && (
          <DocumentUpload
            onClose={() => setShowUpload(false)}
            onComplete={handleUploadComplete}
          />
        )}
      </AnimatePresence>

      {/* In-App Confirmation Dialog for Document Deletion */}
      <ConfirmDialog
        isOpen={!!confirmDeleteDoc}
        onClose={() => setConfirmDeleteDoc(null)}
        onConfirm={handleDelete}
        title="Delete Document Dossier"
        message={`Are you sure you want to permanently delete "${confirmDeleteDoc?.title}" and its associated chunks and embeddings? This action cannot be undone.`}
        confirmLabel="Delete Permanently"
        isDestructive
        isLoading={isDeleting}
      />
    </div>
  );
}