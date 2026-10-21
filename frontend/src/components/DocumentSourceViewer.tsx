import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, ArrowLeft, Loader2, ChevronLeft, ChevronRight,
  X, FileWarning, Copy, Check
} from 'lucide-react';
import { useParams, useNavigate } from 'react-router-dom';
import AppNavbar from './common/AppNavbar';
import apiClient, { getErrorMessage } from '../api/client';
import Breadcrumbs from './ui/Breadcrumbs';
import Button from './ui/Button';
import { useToast } from '../hooks/useToast';

export default function DocumentSourceViewer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const toast = useToast();

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
    let isCancelled = false;
    const fetchDoc = async () => {
      try {
        const res = await apiClient.get(`/api/documents/${id}`);
        if (!isCancelled) {
          setDoc(res.data);
        }
      } catch (err: unknown) {
        if (!isCancelled) {
          setError(getErrorMessage(err, 'Failed to load document metadata.'));
        }
      } finally {
        if (!isCancelled) {
          setLoadingDoc(false);
        }
      }
    };
    fetchDoc();
    return () => {
      isCancelled = true;
    };
  }, [id]);

  useEffect(() => {
    if (!doc) return;
    let isCancelled = false;

    const fetchPage = async () => {
      setLoadingPage(true);
      try {
        const res = await apiClient.get(`/api/documents/${id}/pages/${currentPageNum}`);
        if (!isCancelled) {
          setPageData(res.data);
        }
      } catch (err) {
        console.warn('Failed to load page:', err);
        if (!isCancelled) {
          setPageData(null);
        }
      } finally {
        if (!isCancelled) {
          setLoadingPage(false);
        }
      }
    };

    fetchPage();
    return () => {
      isCancelled = true;
    };
  }, [id, currentPageNum, doc]);

  const jumpToPage = useCallback(
    (pageNum: number) => {
      const maxPages = doc?.page_count || 1;
      if (pageNum >= 1 && pageNum <= maxPages) {
        setCurrentPageNum(pageNum);
        if (window.innerWidth < 1024) {
          setShowSearch(false);
        }
      }
    },
    [doc]
  );

  // Keyboard shortcut listener for page navigation (ArrowLeft / ArrowRight)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === 'INPUT' ||
        document.activeElement?.tagName === 'TEXTAREA'
      ) {
        return;
      }
      if (e.key === 'ArrowLeft') {
        jumpToPage(currentPageNum - 1);
      } else if (e.key === 'ArrowRight') {
        jumpToPage(currentPageNum + 1);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentPageNum, jumpToPage]);

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

  const copyPageWithAttribution = () => {
    if (!pageData?.text) return;
    const title = doc?.title || 'Legal Document';
    const citation = `"${pageData.text}"\n\n— Excerpt from ${title}, Page ${currentPageNum} [LEXORA Primary Record]`;
    navigator.clipboard.writeText(citation);
    setCopiedPage(true);
    toast.success(`Page ${currentPageNum} excerpt copied with primary attribution.`);
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
      <div className="min-h-screen bg-[#080c14] flex flex-col font-sans">
        <AppNavbar />
        <main className="flex-1 flex flex-col items-center justify-center p-6 text-center max-w-md mx-auto">
          <FileWarning size={48} className="text-slate-600 mb-4" />
          <h1 className="text-lg font-bold text-white mb-2">Transcript Unavailable</h1>
          <p className="text-xs text-slate-400 mb-6">{error || 'Document not found.'}</p>
          <Button
            variant="secondary"
            size="md"
            icon={<ArrowLeft size={14} />}
            onClick={() => navigate('/documents')}
          >
            Back to Documents
          </Button>
        </main>
      </div>
    );
  }

  const breadcrumbs = [
    { label: 'Document Catalog', href: '/documents' },
    { label: doc.title, href: `/documents/${id}` },
    { label: `Page ${currentPageNum} Reader` },
  ];

  return (
    <div className="h-screen flex flex-col bg-[#080c14] text-slate-100 font-sans overflow-hidden">
      <AppNavbar />

      {/* Subheader bar for document reader */}
      <div className="h-12 border-b border-slate-800 bg-slate-950/80 flex items-center justify-between px-4 shrink-0 z-20">
        <div className="flex items-center gap-3 min-w-0">
          <button
            type="button"
            onClick={() => navigate(`/documents/${id}`)}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors shrink-0"
            title="Back to Dossier"
            aria-label="Back to Dossier"
          >
            <ArrowLeft size={16} />
          </button>
          <div className="hidden sm:block">
            <Breadcrumbs items={breadcrumbs} />
          </div>
          <span className="sm:hidden text-xs font-semibold text-slate-200 truncate">
            {doc.title}
          </span>
        </div>

        <div className="flex items-center gap-2">
          {pageData?.has_text && (
            <Button
              variant="secondary"
              size="sm"
              icon={copiedPage ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
              onClick={copyPageWithAttribution}
              title="Copy Page with Legal Attribution"
            >
              {copiedPage ? 'Copied Citation' : 'Copy Page'}
            </Button>
          )}

          <Button
            variant={showSearch ? 'primary' : 'outline'}
            size="sm"
            icon={<Search size={13} />}
            onClick={() => setShowSearch(!showSearch)}
          >
            Search Text
          </Button>
        </div>
      </div>

      {/* Reader Body */}
      <div className="flex flex-1 overflow-hidden relative">
        <main className="flex-1 flex flex-col bg-[#050811] relative overflow-hidden">
          {/* Floating Pagination Bar */}
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-3 px-4 py-2 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-full shadow-2xl z-20">
            <button
              type="button"
              onClick={() => jumpToPage(currentPageNum - 1)}
              disabled={currentPageNum <= 1 || loadingPage}
              className="p-1 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
              title="Previous Page (Left Arrow)"
              aria-label="Previous Page"
            >
              <ChevronLeft size={18} />
            </button>

            <span className="text-xs font-mono font-medium text-slate-300 w-28 text-center select-none">
              Page {currentPageNum} / {doc?.page_count || 1}
            </span>

            <button
              type="button"
              onClick={() => jumpToPage(currentPageNum + 1)}
              disabled={currentPageNum >= (doc?.page_count || 1) || loadingPage}
              className="p-1 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
              title="Next Page (Right Arrow)"
              aria-label="Next Page"
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
              <article className="w-full max-w-3xl bg-slate-900/70 border border-slate-800/90 text-slate-200 shadow-2xl rounded-xl min-h-[750px] p-8 md:p-12 relative flex flex-col">
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
              </article>
            ) : (
              <div className="text-center text-slate-500 py-24">
                Unable to load page content.
              </div>
            )}
          </div>
        </main>

        {/* Search Drawer Panel */}
        <AnimatePresence>
          {showSearch && (
            <motion.aside
              initial={{ x: 320 }}
              animate={{ x: 0 }}
              exit={{ x: 320 }}
              transition={{ duration: 0.2 }}
              className="w-80 border-l border-slate-800 bg-slate-950 flex flex-col z-30 shadow-2xl absolute right-0 h-full"
            >
              <div className="p-4 border-b border-slate-800 flex items-center justify-between">
                <h3 className="font-semibold text-xs text-white uppercase tracking-wider flex items-center gap-2">
                  <Search size={14} className="text-blue-400" />
                  <span>Search in Document</span>
                </h3>
                <button
                  type="button"
                  onClick={() => setShowSearch(false)}
                  className="p-1 text-slate-400 hover:text-white rounded"
                  aria-label="Close search drawer"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="p-4 border-b border-slate-800">
                <form onSubmit={handleSearch} className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Search keywords..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-500 outline-none focus:border-blue-500"
                  />
                  <Button type="submit" variant="primary" size="sm" isLoading={isSearching}>
                    Go
                  </Button>
                </form>
              </div>

              <div className="flex-1 overflow-y-auto p-4 space-y-3 custom-scrollbar">
                {searchResults.length > 0 ? (
                  searchResults.map((res: any, idx: number) => (
                    <div
                      key={idx}
                      onClick={() => jumpToPage(res.page_number)}
                      className="p-3 bg-slate-900/60 hover:bg-slate-850 rounded-xl border border-slate-800 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono font-bold text-blue-400">
                          Page {res.page_number}
                        </span>
                        <span className="text-[9px] text-slate-500 font-mono">
                          {res.match_count} match{res.match_count > 1 ? 'es' : ''}
                        </span>
                      </div>
                      <p className="text-xs text-slate-300 font-serif italic line-clamp-3">
                        "...{renderHighlightedText(res.text_snippet, searchQuery)}..."
                      </p>
                    </div>
                  ))
                ) : isSearching ? (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    Searching indexed document chunks...
                  </div>
                ) : searchQuery ? (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    No matches found for "{searchQuery}".
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-500 text-xs">
                    Enter terms to scan pages.
                  </div>
                )}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}