import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FileText, Search, ArrowLeft, Loader2, ChevronLeft, ChevronRight,
  Menu, X, FileWarning
} from 'lucide-react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const getAuthHeader = () => {
  const token = localStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}` } : {};
};

export default function DocumentSourceViewer() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  
  const [doc, setDoc] = useState<any>(null);
  const [currentPageNum, setCurrentPageNum] = useState(1);
  const [pageData, setPageData] = useState<any>(null);
  const [loadingDoc, setLoadingDoc] = useState(true);
  const [loadingPage, setLoadingPage] = useState(true);
  
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [showSearch, setShowSearch] = useState(false);

  useEffect(() => {
    const fetchDoc = async () => {
      try {
        const res = await axios.get(`${API_URL}/api/documents/${id}`, {
          headers: getAuthHeader()
        });
        setDoc(res.data);
      } catch (err) {
        console.error('Failed to fetch document', err);
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
        const res = await axios.get(`${API_URL}/api/documents/${id}/pages/${currentPageNum}`, {
          headers: getAuthHeader()
        });
        setPageData(res.data);
      } catch (err) {
        console.error('Failed to fetch page', err);
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
      const res = await axios.get(`${API_URL}/api/documents/${id}/search?q=${encodeURIComponent(searchQuery)}`, {
        headers: getAuthHeader()
      });
      setSearchResults(res.data);
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

  const renderHighlightedText = (text: string, query: string) => {
    if (!query.trim() || !text) return text;
    
    const parts = text.split(new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi'));
    
    return parts.map((part, i) => 
      part.toLowerCase() === query.toLowerCase() ? 
        <mark key={i} className="bg-yellow-500/30 text-yellow-200 rounded px-1">{part}</mark> : part
    );
  };

  if (loadingDoc) {
    return (
      <div className="min-h-screen bg-[#0b0f19] flex items-center justify-center">
        <Loader2 size={32} className="animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-[#0b0f19] text-slate-100 font-['Inter',sans-serif] overflow-hidden">
      <div className="h-14 border-b border-slate-800 bg-slate-900/50 flex items-center justify-between px-4 flex-shrink-0 z-20">
        <div className="flex items-center gap-4">
          <button 
            onClick={() => navigate(`/documents/${id}`)}
            className="p-2 -ml-2 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <ArrowLeft size={18} />
          </button>
          <div className="flex items-center gap-2 max-w-md">
            <FileText size={16} className="text-blue-400 flex-shrink-0" />
            <span className="font-semibold text-sm truncate">{doc?.title}</span>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowSearch(!showSearch)}
            className={`p-2 rounded-lg transition-colors flex items-center gap-2 ${
              showSearch ? 'bg-blue-500/10 text-blue-400' : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Search size={18} />
            <span className="text-sm font-medium hidden sm:inline">Search</span>
          </button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden relative">
        <div className="flex-1 flex flex-col bg-[#050811] relative">
          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-4 px-4 py-2 bg-slate-800/80 backdrop-blur border border-slate-700 rounded-full shadow-2xl z-10">
            <button 
              onClick={() => jumpToPage(currentPageNum - 1)}
              disabled={currentPageNum <= 1 || loadingPage}
              className="p-1 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
            >
              <ChevronLeft size={20} />
            </button>
            <span className="text-sm font-medium font-mono text-slate-300 w-24 text-center">
              {currentPageNum} / {doc?.page_count || 1}
            </span>
            <button 
              onClick={() => jumpToPage(currentPageNum + 1)}
              disabled={currentPageNum >= (doc?.page_count || 1) || loadingPage}
              className="p-1 text-slate-300 hover:text-white disabled:opacity-30 transition-colors"
            >
              <ChevronRight size={20} />
            </button>
          </div>

          <div className="flex-1 overflow-auto p-4 sm:p-8 flex justify-center">
            {loadingPage ? (
              <div className="w-full max-w-3xl aspect-[1/1.4] bg-slate-900/50 rounded-xl border border-slate-800 flex items-center justify-center animate-pulse">
                <Loader2 size={32} className="animate-spin text-slate-600" />
              </div>
            ) : pageData ? (
              <div className="w-full max-w-3xl bg-white text-slate-900 shadow-2xl rounded-sm min-h-[800px] flex flex-col relative transition-all duration-300">
                <div className="absolute -left-32 top-8 text-xs font-mono text-slate-500 flex flex-col items-end gap-1 opacity-50 hidden xl:flex">
                  <span>Page {pageData.page_number}</span>
                  {pageData.section && pageData.section !== 'OTHER' && (
                    <span className="px-2 py-1 bg-violet-500/20 text-violet-400 rounded">
                      {pageData.section.replace(/_/g, ' ')}
                    </span>
                  )}
                </div>

                <div className="p-12 text-sm leading-relaxed whitespace-pre-wrap font-serif">
                  {pageData.has_text ? (
                    searchQuery ? renderHighlightedText(pageData.text, searchQuery) : pageData.text
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-400 opacity-50 py-32">
                      <FileWarning size={48} className="mb-4" />
                      <p>This page appears to be a scanned image or contains no extractable text.</p>
                      {doc?.ocr_required && (
                        <p className="text-xs mt-2">(OCR may be required)</p>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center h-full text-slate-500">
                Failed to load page content.
              </div>
            )}
          </div>
        </div>

        <AnimatePresence>
          {showSearch && (
            <motion.div
              initial={{ width: 0, opacity: 0 }}
              animate={{ width: 320, opacity: 1 }}
              exit={{ width: 0, opacity: 0 }}
              className="border-l border-slate-800 bg-slate-900/80 backdrop-blur flex flex-col overflow-hidden z-20 flex-shrink-0 absolute right-0 h-full lg:relative lg:h-auto"
            >
              <div className="p-4 border-b border-slate-800">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-sm">Search Document</h3>
                  <button onClick={() => setShowSearch(false)} className="lg:hidden p-1 text-slate-400 hover:text-white">
                    <X size={16} />
                  </button>
                </div>
                <form onSubmit={handleSearch} className="relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search text..."
                    className="w-full bg-slate-800 border border-slate-700 rounded-lg pl-9 pr-3 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                  />
                  <Search size={14} className="absolute left-3 top-2.5 text-slate-500" />
                </form>
              </div>

              <div className="flex-1 overflow-y-auto p-2">
                {isSearching ? (
                  <div className="flex justify-center p-8">
                    <Loader2 size={20} className="animate-spin text-blue-500" />
                  </div>
                ) : searchResults.length > 0 ? (
                  <div className="space-y-2">
                    <p className="text-xs text-slate-500 px-2 py-1 font-medium">{searchResults.length} matches found</p>
                    {searchResults.map((res, idx) => (
                      <button
                        key={idx}
                        onClick={() => jumpToPage(res.page_number)}
                        className="w-full text-left p-3 rounded-lg hover:bg-slate-800/80 transition-colors border border-transparent hover:border-slate-700/50 group"
                      >
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-mono text-blue-400">Page {res.page_number}</span>
                          <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity">
                            Jump
                          </span>
                        </div>
                        <p className="text-xs text-slate-300 line-clamp-3 leading-relaxed">
                          ...{renderHighlightedText(res.text_snippet, searchQuery)}...
                        </p>
                      </button>
                    ))}
                  </div>
                ) : searchQuery ? (
                  <div className="p-8 text-center text-sm text-slate-500">
                    No results found for "{searchQuery}"
                  </div>
                ) : (
                  <div className="p-8 text-center text-sm text-slate-600 flex flex-col items-center gap-2">
                    <Search size={24} className="opacity-20 mb-2" />
                    Enter a term to search across all {doc?.page_count || 0} pages
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