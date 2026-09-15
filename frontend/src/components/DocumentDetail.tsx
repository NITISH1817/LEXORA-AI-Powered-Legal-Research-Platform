import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  FileText, Clock, FileWarning, Scale, Search, History, CheckCircle2,
  ChevronRight, ArrowLeft, Loader2, PlayCircle, Eye, Activity, Database
} from 'lucide-react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: "Bearer $token" } : {};
};

export default function DocumentDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [doc, setDoc] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        const res = await axios.get("${API_URL}/api/documents/", {
          headers: getAuthHeader()
        });
        setDoc(res.data);
      } catch (err) {
        console.error('Failed to fetch document', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDoc();
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center">
        <Loader2 size={32} className="animate-spin text-blue-500 mb-4" />
        <p className="text-slate-400">Loading document intelligence...</p>
      </div>
    );
  }

  if (!doc) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex flex-col items-center justify-center">
        <FileWarning size={48} className="text-slate-600 mb-4" />
        <p className="text-slate-400">Document not found.</p>
        <button onClick={() => navigate('/documents')} className="mt-4 text-blue-400">Back to Documents</button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 font-['Inter',sans-serif]">
      {/* Background */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-6 py-8">
        <button 
          onClick={() => navigate('/documents')}
          className="flex items-center gap-2 text-slate-400 hover:text-white transition-colors mb-6 text-sm"
        >
          <ArrowLeft size={16} />
          Back to Documents
        </button>

        <div className="flex items-start justify-between mb-8">
          <div>
            <div className="flex items-center gap-3 mb-3">
              <div className="px-2.5 py-1 rounded border border-slate-700 bg-slate-800 text-xs text-slate-300 font-mono uppercase">
                {doc.document_type || 'Unknown Type'}
              </div>
              <div className={"px-2.5 py-1 rounded-full text-xs font-semibold $
                doc.status === 'READY' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 
                doc.status === 'FAILED' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : 
                'bg-blue-500/10 text-blue-400 border border-blue-500/20'
              "}>
                {doc.status}
              </div>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">{doc.title}</h1>
            <p className="text-slate-400 flex items-center gap-4 text-sm">
              <span className="flex items-center gap-1.5"><FileText size={14}/> {doc.page_count || 0} Pages</span>
              <span className="flex items-center gap-1.5"><Clock size={14}/> {new Date(doc.uploaded_at).toLocaleDateString()}</span>
            </p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={() => navigate("/documents//source")}
              className="flex items-center gap-2 px-5 py-2.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-lg transition-colors shadow-sm"
            >
              <Eye size={16} />
              View Source Text
            </button>
            <button
              onClick={() => navigate("/research?doc=")}
              className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-600 to-violet-600 hover:from-blue-500 hover:to-violet-500 text-white rounded-lg transition-all shadow-lg shadow-blue-500/20"
            >
              <Search size={16} />
              Research Document
            </button>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-6">
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
              <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
                <Database size={18} className="text-blue-400" />
                Extracted Metadata
              </h2>
              <div className="grid grid-cols-2 gap-4">
                {doc.metadata_fields.filter((f: any) => f.field_value).length > 0 ? (
                  doc.metadata_fields.filter((f: any) => f.field_value).map((f: any) => (
                    <div key={f.field_name} className="p-3 bg-slate-800/50 rounded-xl border border-slate-700/50">
                      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1 flex justify-between">
                        {f.field_name.replace(/_/g, ' ')}
                        <span className="text-[10px] bg-slate-800 px-1 rounded">{Math.round(f.confidence * 100)}%</span>
                      </div>
                      <div className="text-sm text-slate-200 font-medium">{f.field_value}</div>
                    </div>
                  ))
                ) : (
                  <div className="col-span-2 p-6 text-center text-slate-500">
                    No metadata could be extracted from this document.
                  </div>
                )}
              </div>
            </div>

            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
              <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
                <Scale size={18} className="text-violet-400" />
                Detected Legal Structure
              </h2>
              {doc.sections.length > 0 ? (
                <div className="flex flex-col gap-2">
                  {doc.sections.map((s: any, idx: number) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-800/30 rounded-lg border border-slate-700/30 hover:bg-slate-800/60 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-violet-500/10 text-violet-400 flex items-center justify-center font-bold text-xs">
                          {idx + 1}
                        </div>
                        <span className="font-semibold text-slate-300">{s.section_type.replace(/_/g, ' ')}</span>
                      </div>
                      <div className="flex items-center gap-6 text-sm text-slate-400">
                        <span>Pages {s.start_page} - {s.end_page}</span>
                        <span className="w-12 text-right opacity-50">{Math.round(s.confidence * 100)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-6 text-center text-slate-500 bg-slate-800/30 rounded-lg">
                  Standard legal structure could not be mapped.
                </div>
              )}
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-slate-900/40 border border-slate-800 rounded-2xl p-6 backdrop-blur-sm">
              <h2 className="text-lg font-bold text-white flex items-center gap-2 mb-6">
                <History size={18} className="text-emerald-400" />
                Processing Log
              </h2>
              <div className="relative pl-3 border-l border-slate-700/50 space-y-6">
                {doc.processing_logs.map((log: any, idx: number) => (
                  <div key={idx} className="relative">
                    <div className={"absolute -left-[17px] top-1 w-2 h-2 rounded-full $
                      log.status === 'SUCCESS' ? 'bg-emerald-500' :
                      log.status === 'FAILED' ? 'bg-red-500' : 'bg-slate-500'
                    "} />
                    <p className="text-xs font-bold text-slate-300 uppercase tracking-wider">{log.stage}</p>
                    <p className="text-xs text-slate-500 mt-1">{new Date(log.timestamp).toLocaleTimeString()}</p>
                    {log.message && (
                      <p className="text-sm text-slate-400 mt-1.5 p-2 bg-slate-800/50 rounded border border-slate-700/50">
                        {log.message}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}