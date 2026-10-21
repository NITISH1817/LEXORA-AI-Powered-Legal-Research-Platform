import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Scale, ArrowLeft, Search, FileText } from 'lucide-react';
import Button from '../ui/Button';

export const NotFound: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#080c14] text-slate-200 font-sans flex flex-col items-center justify-center p-6 relative overflow-hidden">
      {/* Background ambient lighting */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none" />

      <main className="relative z-10 max-w-lg w-full bg-slate-900/80 border border-slate-800 rounded-2xl p-8 sm:p-10 text-center shadow-2xl backdrop-blur-md">
        <div className="w-14 h-14 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 flex items-center justify-center mx-auto mb-5 shadow-inner">
          <Scale size={28} />
        </div>

        <span className="text-[10px] uppercase font-bold tracking-widest px-2.5 py-1 rounded bg-slate-800 border border-slate-700/60 text-slate-400 font-mono inline-block mb-3">
          Error 404 • Unindexed Route
        </span>

        <h1 className="text-2xl sm:text-3xl font-serif font-bold text-white mb-3">
          Authority or Resource Not Found
        </h1>

        <p className="text-xs sm:text-sm text-slate-400 mb-8 leading-relaxed font-sans">
          The requested URL does not match any indexed research workspace view, document dossier, or evaluation endpoint in LEXORA.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Button
            variant="primary"
            size="md"
            icon={<Search size={14} />}
            onClick={() => navigate('/')}
            className="w-full sm:w-auto"
          >
            Research Workspace
          </Button>

          <Button
            variant="secondary"
            size="md"
            icon={<FileText size={14} />}
            onClick={() => navigate('/documents')}
            className="w-full sm:w-auto"
          >
            Document Catalog
          </Button>

          <Button
            variant="outline"
            size="md"
            icon={<ArrowLeft size={14} />}
            onClick={() => navigate(-1)}
            className="w-full sm:w-auto"
          >
            Go Back
          </Button>
        </div>
      </main>

      <footer className="mt-8 text-center text-xs text-slate-600">
        LEXORA — AI-Powered Legal Intelligence & Research Platform
      </footer>
    </div>
  );
};

export default NotFound;
