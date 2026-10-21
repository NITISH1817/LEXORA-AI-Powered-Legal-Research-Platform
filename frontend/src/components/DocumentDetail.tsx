import { useState, useEffect } from 'react';
import {
  FileText, Clock, FileWarning, Scale, Search, History,
  ArrowLeft, Loader2, Eye, Database
} from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import AppNavbar from './common/AppNavbar';
import apiClient, { getErrorMessage } from '../api/client';

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        const res = await apiClient.get(`/api/documents/${id}`);
        setDoc(res.data);
      } catch (err: unknown) {
        setError(getErrorMessage(err, 'Failed to fetch document intelligence profile.'));
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#080c14] flex flex-col items-center justify-center text-slate-400 gap-3">
        <Loader2 size={32} className="animate-spin text-blue-500" />
        <p className="text-xs">Loading document intelligence dossier...</p>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="min-h-screen bg-[#080c14] flex flex-col items-center justify-center p-6 text-center">
        <AppNavbar />
        <div className="my-auto max-w-md">
          <FileWarning size={48} className="text-slate-600 mb-4 mx-auto" />
          <h2 className="text-lg font-bold text-white mb-2">Document Unavailable</h2>
          <p className="text-xs text-slate-400 mb-6">
            {error || 'The requested document record does not exist or access is restricted.'}
          </p>
          <button
            type="button"
            onClick={() => navigate('/documents')}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-white rounded-lg text-xs font-semibold transition-colors"
          >
            ← Back to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-100 font-sans flex flex-col">
      <AppNavbar />

      <div className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <button
          type="button"
          onClick={() => navigate('/documents')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-6 text-xs font-medium"
        >
          <ArrowLeft size={14} />
          <span>Back to Document Catalog</span>
        </button>

        {/* Top Header Card */}
        <div className="flex flex-col md:flex-row md:items-start justify-between gap-6 mb-8 pb-6 border-b border-slate-800">
          <div>
            <div className="flex items-center gap-2.5 mb-2.5">
              <span className="px-2 py-0.5 rounded border border-slate-700/80 bg-slate-800/80 text-[10px] text-slate-300 font-mono uppercase">
                {doc.document_type || 'PDF'}
              </span>
              <span
                className={`px-2.5 py-0.5 rounded-full text-[10px] font-semibold font-mono ${
                  doc.status === 'READY'
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : doc.status === 'FAILED'
                    ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                    : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                }`}
              >
                {doc.status}
              </span>
              {doc.version_number && doc.version_number > 1 && (
                <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 font-mono text-[10px]">
                  v{doc.version_number}
                </span>
              )}
            </div>

            <h1 className="text-2xl md:text-3xl font-serif font-bold text-white mb-2 leading-tight">
              {doc.title}
            </h1>

            <div className="text-slate-400 flex flex-wrap items-center gap-x-4 gap-y-1 text-xs">
              <span className="flex items-center gap-1.5 font-mono">
                <FileText size={13} /> {doc.page_count || 0} Pages
              </span>
              <span className="text-slate-600">•</span>
              <span className="flex items-center gap-1.5">
                <Clock size={13} /> Uploaded{' '}
                {new Date(doc.uploaded_at).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}
              </span>
              {doc.case_name && (
                <>
                  <span className="text-slate-600">•</span>
                  <span className="flex items-center gap-1 text-slate-300">
                    <Scale size={13} className="text-blue-400" /> {doc.case_name}
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            <button
              type="button"
              onClick={() => navigate(`/documents/${id}/source`)}
              className="flex items-center gap-1.5 px-4 py-2 bg-slate-800 hover:bg-slate-750 border border-slate-700 text-white rounded-lg text-xs font-semibold transition-colors"
            >
              <Eye size={14} />
              <span>Read Full Transcript</span>
            </button>
            <button
              type="button"
              onClick={() => navigate(`/research?doc=${id}`)}
              className="flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition-colors shadow-md shadow-blue-500/20"
            >
              <Search size={14} />
              <span>Research in Workspace</span>
            </button>
          </div>
        </div>

        {/* Content Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            {/* Extracted Metadata Card */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-300 flex items-center gap-2 mb-4">
                <Database size={15} className="text-blue-400" />
                <span>Extracted Legal Metadata</span>
              </h2>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {doc.metadata_fields && doc.metadata_fields.filter((f: any) => f.field_value).length > 0 ? (
                  doc.metadata_fields
                    .filter((f: any) => f.field_value)
                    .map((f: any) => (
                      <div
                        key={f.field_name}
                        className="p-3 bg-slate-950/60 rounded-xl border border-slate-800/80"
                      >
                        <div className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 flex justify-between font-mono">
                          <span>{f.field_name.replace(/_/g, ' ')}</span>
                          <span className="text-slate-400 font-bold">
                            {Math.round((f.confidence || 1) * 100)}%
                          </span>
                        </div>
                        <div className="text-xs text-slate-200 font-medium font-serif leading-relaxed">
                          {f.field_value}
                        </div>
                      </div>
                    ))
                ) : (
                  <div className="col-span-2 p-6 text-center text-slate-500 text-xs italic">
                    No custom metadata attributes extracted from this filing.
                  </div>
                )}
              </div>
            </div>

            {/* Document Structure & Sections */}
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-300 flex items-center gap-2 mb-4">
                <Scale size={15} className="text-purple-400" />
                <span>Detected Pleading / Judgment Structure</span>
              </h2>

              {doc.sections && doc.sections.length > 0 ? (
                <div className="space-y-2">
                  {doc.sections.map((s: any, idx: number) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-3 bg-slate-950/50 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-6 h-6 rounded-md bg-purple-500/10 text-purple-400 flex items-center justify-center font-mono font-bold text-[10px]">
                          {idx + 1}
                        </div>
                        <span className="font-semibold text-xs text-slate-200">
                          {s.section_type.replace(/_/g, ' ')}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400 font-mono">
                        <span>Pages {s.start_page}–{s.end_page}</span>
                        <span className="text-slate-500">
                          {Math.round((s.confidence || 1) * 100)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-slate-500 bg-slate-950/50 rounded-xl text-xs italic">
                  Standard legal pleading sections could not be mapped automatically.
                </div>
              )}
            </div>
          </div>

          {/* Right Rail: Processing Log */}
          <div className="space-y-6">
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6">
              <h2 className="text-xs font-bold uppercase tracking-widest text-slate-300 flex items-center gap-2 mb-5">
                <History size={15} className="text-emerald-400" />
                <span>Pipeline Audit Log</span>
              </h2>

              <div className="relative pl-3 border-l border-slate-800 space-y-5">
                {doc.processing_logs && doc.processing_logs.length > 0 ? (
                  doc.processing_logs.map((log: any, idx: number) => (
                    <div key={idx} className="relative">
                      <div
                        className={`absolute -left-[17px] top-1 w-2 h-2 rounded-full ${
                          log.status === 'SUCCESS'
                            ? 'bg-emerald-500 shadow-sm shadow-emerald-500/50'
                            : log.status === 'FAILED'
                            ? 'bg-rose-500'
                            : 'bg-slate-500'
                        }`}
                      />
                      <p className="text-[11px] font-bold text-slate-200 uppercase tracking-wider font-mono">
                        {log.stage}
                      </p>
                      <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </p>
                      {log.message && (
                        <p className="text-xs text-slate-400 mt-1 p-2 bg-slate-950/60 rounded border border-slate-800/80 font-mono leading-relaxed">
                          {log.message}
                        </p>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 italic">No pipeline audit logs recorded.</p>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}