import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Search, ArrowLeft, Loader2, ChevronLeft, ChevronRight,
  X, FileWarning, Copy, Check
} from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import AppNavbar from './common/AppNavbar';
import apiClient, { getErrorMessage } from '../api/client';

export default function DocumentSourceViewer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [doc, setDoc] = useState<any>(null);
  const [currentPageNum, setCurrentPageNum] = useState(1);
  const [pageData, setPageData] = useState<any>(null);
  const [loadingDoc, setLoadingDoc] = useState(true);
  const [loadingPage, setLoadingPage] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [copiedPage, setCopiedPage] = useState(false);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        const res = await apiClient.get(`/api/documents/${id}`);
        setDoc(res.data);
      } catch (err: unknown) {
        setError(getErrorMessage(err, 'Failed to load document metadata.'));
      } finally {
        setLoadingDoc(false);
      }
    };
    fetchDoc();
  }, [id]);

  useEffect(() => {
    if (!doc) return;

    const fetchPage = async () => {
      setLoadingPage(true);
      try {
        const res = await apiClient.get(`/api/documents/${id}/pages/${currentPageNum}`);
        setPageData(res.data);
      } catch (err) {
        console.warn('Failed to load page:', err);
        setPageData(null);
      } finally {
        setLoadingPage(false);
      }
    };

    fetchPage();
  }, [id, currentPageNum, doc]);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setIsSearching(true);
    try {
      const res = await apiClient.get(`/api/documents/${id}/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchResults(res.data || []);
    } catch (err) {
      console.error('Search failed', err);
    } finally {
      setIsSearching(false);
    }
  };

  const jumpToPage = (pageNum: number) => {
    if (pageNum >= 1 && pageNum <= (doc?.page_count || 1)) {
      setCurrentPageNum(pageNum);
      if (window.innerWidth < 1024) {
        setShowSearch(false);
      }
    }
  };

  const copyPageWithAttribution = () => {
    if (!pageData?.text) return;
    const title = doc?.title || 'Legal Document';
    const citation = `"${pageData.text}"\n\n— Excerpt from ${title}, Page ${currentPageNum} [LEXORA Primary Record]`;
    navigator.clipboard.writeText(citation);
    setCopiedPage(true);
    setTimeout(() => setCopiedPage(false), 2000);
  };

  const renderHighlightedText = (text: string, query: string) => {
    if (!query.trim() || !text) return text;
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} className="bg-yellow-500/30 text-yellow-200 rounded px-1">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  if (loadingDoc) {
    return (
      <div className="min-h-screen bg-[#080c14] flex flex-col items-center justify-center text-slate-400 gap-3 font-sans">
        <Loader2 size={32} className="animate-spin text-blue-500" />
        <span className="text-xs">Loading document transcript...</span>
      </div>
    );
  }

  if (error || !doc) {
    return (
      <div className="min-h-screen bg-[#080c14] flex flex-col items-center justify-center p-6 text-center font-sans">
        <AppNavbar />
        <div className="my-auto max-w-md">
          <FileWarning size={48} className="text-slate-600 mb-4 mx-auto" />
          <h2 className="text-lg font-bold text-white mb-2">Transcript Unavailable</h2>
          <p className="text-xs text-slate-400 mb-6">{error || 'Document not found.'}</p>
          <button
            type="button"
            onClick={() => navigate('/documents')}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-750 text-white rounded-lg text-xs font-semibold"
          >
            ← Back to Documents
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-[#080c14] text-slate-100 font-sans overflow-hidden">
      <AppNavbar />

      {/* Subheader bar for document reader */}
      <div className="h-12 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between px-4 shrink-0 z-20">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => navigate(`/documents/${id}`)}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="Back to Dossier"
          >
            <ArrowLeft size={16} />
          </button>
          <div className="flex items-center gap-2 max-w-lg min-w-0">
            <FileText size={15} className="text-blue-400 shrink-0" />
            <span className="font-semibold text-xs text-slate-200 truncate">{doc?.title}</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {pageData?.has_text && (
            <button
              type="button"
              onClick={copyPageWithAttribution}
              className="flex items-center gap-1.5 px-3 py-1 bg-slate-800 hover:bg-slate-750 text-slate-300 rounded text-xs transition-colors border border-slate-700/60"
              title="Copy Page with Legal Attribution"
            >
              {copiedPage ? (
                <>
                  <Check size={12} className="text-emerald-400" />
                  <span className="text-emerald-400">Copied!</span>
                </>
              ) : (
                <>
                  <Copy size={12} />
                  <span>Copy Page Citation</span>
                </>
              )}
            </button>
          )}

          <button
            type="button"
            onClick={() => setShowSearch(!showSearch)}
            className={`p-1.5 px-3 rounded-md transition-colors flex items-center gap-1.5 text-xs font-medium ${
              showSearch
                ? 'bg-blue-600/20 text-blue-400 border border-blue-500/30'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Search size={14} />
            <span>Search Text</span>
          </button>
        </div>
      </div>

      {/* Reader Body */}
      <div className="flex flex-1 overflow-hidden relative">
        <div className="flex-1 flex flex-col bg-[#050811] relative overflow-hidden">
          {/* Floating Pagination Bar */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-2 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-full shadow-2xl z-20">
            <button
              type="button"
              onClick={() => jumpToPage(currentPageNum - 1)}
              disabled={currentPageNum <= 1 || loadingPage}
              className="p-1 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
              title="Previous Page"
            >
              <ChevronLeft size={18} />
            </button>

            <span className="text-xs font-mono font-medium text-slate-300 w-24 text-center">
              Page {currentPageNum} / {doc?.page_count || 1}
            </span>

            <button
              type="button"
              onClick={() => jumpToPage(currentPageNum + 1)}
              disabled={currentPageNum >= (doc?.page_count || 1) || loadingPage}
              className="p-1 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
              title="Next Page"
            >
              <ChevronRight size={18} />
            </button>
          </div>

          {/* Transcript Viewer Canvas */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-8 flex justify-center pb-24 custom-scrollbar">
            {loadingPage ? (
              <div className="w-full max-w-3xl aspect-[1/1.4] bg-slate-900/40 rounded-xl border border-slate-800 flex items-center justify-center animate-pulse">
                <Loader2 size={32} className="animate-spin text-slate-600" />
              </div>
            ) : pageData ? (
              <div className="w-full max-w-3xl bg-slate-900/70 border border-slate-800/90 text-slate-200 shadow-2xl rounded-xl min-h-[750px] p-8 md:p-12 relative flex flex-col">
                <div className="flex justify-between items-center text-[11px] font-mono text-slate-500 pb-4 border-b border-slate-800 mb-6">
                  <span>PAGE {pageData.page_number}</span>
                  {pageData.section && pageData.section !== 'OTHER' && (
                    <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-sans uppercase">
                      {pageData.section.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>

                <div className="text-xs sm:text-sm leading-relaxed whitespace-pre-wrap font-serif text-slate-200 selection:bg-blue-600/40 flex-1">
                  {pageData.has_text ? (
                    searchQuery ? renderHighlightedText(pageData.text, searchQuery) : pageData.text
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-60 py-24 text-center">
                      <FileWarning size={40} className="mb-3 text-slate-500" />
                      <p className="text-xs">This page contains scanned graphical imagery with no extractable text.</p>
                      {doc?.ocr_required && (
                        <p className="text-[10px] text-amber-400 mt-1">OCR processing recommended.</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500 text-xs">
                Failed to load page text.
              </div>
            )}
          </div>
        </div>

        {/* Search Sidebar Drawer */}
        <AnimatePresence>
          {showSearch && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-l border-slate-800 bg-slate-950/90 backdrop-blur-md flex flex-col overflow-hidden z-20 shrink-0 absolute right-0 h-full lg:relative shadow-2xl"
            >
              <div className="p-4 border-b border-slate-800">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-xs text-slate-200">Search In Document</h3>
                  <button
                    type="button"
                    onClick={() => setShowSearch(false)}
                    className="p-1 text-slate-400 hover:text-white rounded"
                  >
                    <X size={15} />
                  </button>
                </div>

                <form onSubmit={handleSearch} className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search keywords..."
                    className="w-full bg-slate-900 border border-slate-700/80 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                  <Search size={13} className="absolute left-2.5 top-2.5 text-slate-500" />
                </form>
              </div>

              <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
                {isSearching ? (
                  <div className="flex justify-center p-8">
                    <Loader2 size={20} className="animate-spin text-blue-400" />
                  </div>
                ) : searchResults.length > 0 ? (
                  <>
                    <p className="text-[10px] text-slate-500 font-mono px-1">
                      {searchResults.length} matches found
                    </p>
                    {searchResults.map((res, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => jumpToPage(res.page_number)}
                        className="w-full text-left p-2.5 rounded-lg bg-slate-900/60 hover:bg-slate-850 border border-slate-800/80 hover:border-slate-700 transition-colors group"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-[10px] font-mono text-blue-400 font-bold">
                            Page {res.page_number}
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 font-serif line-clamp-3 leading-relaxed">
                          ...{renderHighlightedText(res.text_snippet, searchQuery)}...
                        </p>
                      </button>
                    ))}
                  </>
                ) : searchQuery ? (
                  <div className="p-8 text-center text-xs text-slate-500">
                    No results for "{searchQuery}"
                  </div>
                ) : (
                  <div className="p-8 text-center text-xs text-slate-500">
                    Enter a legal term to search across all {doc?.page_count || 0} pages.
                  </div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}