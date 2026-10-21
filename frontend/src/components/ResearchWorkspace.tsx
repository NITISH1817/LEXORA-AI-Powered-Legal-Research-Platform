import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Plus, History, FileText, Bookmark, ChevronRight, X, Loader2,
  BookOpen, ShieldAlert, Sparkles, Scale, GitFork,
  Copy, Check, AlertCircle, Trash2, StickyNote, CornerDownLeft
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import AppNavbar from './common/AppNavbar';
import SafeMarkdown from './common/SafeMarkdown';
import CaseIntelligence from './CaseIntelligence';
import ComparativeIntelligence from './ComparativeIntelligence';
import PrecedentGraph from './PrecedentGraph';
import apiClient, { getErrorMessage } from '../api/client';
import Button from './ui/Button';
import ConfirmDialog from './ui/ConfirmDialog';
import Modal from './ui/Modal';
import { useToast } from '../hooks/useToast';

export type ActiveWorkspaceView = 'SYNTHESIS' | 'SEARCH' | 'CASE' | 'COMPARE' | 'GRAPH' | 'BRIEF';

export default function ResearchWorkspace() {
  const toast = useToast();

  // Navigation & Sessions
  const [activeSession, setActiveSession] = useState<any>(null);
  const [sessions, setSessions] = useState<any[]>([]);
  const [showHistory, setShowHistory] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Search & Query state
  const [searchQuery, setSearchQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'SYNTHESIS' | 'PASSAGES'>('SYNTHESIS');
  const [isLoading, setIsLoading] = useState(false);
  const [queryError, setQueryError] = useState<string | null>(null);

  // Results state
  const [synthesisResult, setSynthesisResult] = useState<any | null>(null);
  const [passageResults, setPassageResults] = useState<any[]>([]);

  // Center panel view
  const [activeView, setActiveView] = useState<ActiveWorkspaceView>('SYNTHESIS');
  const [selectedCaseId, setSelectedCaseId] = useState<number | null>(null);
  const [caseData, setCaseData] = useState<any | null>(null);
  const [graphData, setGraphData] = useState<any | null>(null);
  const [graphDepth, setGraphDepth] = useState<number>(1);
  const [comparisonData, setComparisonData] = useState<any | null>(null);
  const [briefMarkdown, setBriefMarkdown] = useState<string | null>(null);
  const [isGeneratingBrief, setIsGeneratingBrief] = useState(false);

  // Source inspection drawer
  const [selectedSource, setSelectedSource] = useState<any | null>(null);
  const [copiedCitation, setCopiedCitation] = useState(false);

  // Dialog states: Delete Session & Add Note
  const [sessionToDelete, setSessionToDelete] = useState<any | null>(null);
  const [isDeletingSession, setIsDeletingSession] = useState(false);
  const [showNoteModal, setShowNoteModal] = useState(false);
  const [noteContent, setNoteContent] = useState('');
  const [isAddingNote, setIsAddingNote] = useState(false);

  // Fetch existing research sessions asynchronously
  const fetchSessions = useCallback(async () => {
    try {
      const res = await apiClient.get('/api/research');
      const loadedSessions = res.data || [];
      setSessions(loadedSessions);
      if (loadedSessions.length > 0) {
        setActiveSession((prev: any) => prev || loadedSessions[0]);
      }
    } catch (err) {
      console.warn('Could not load research sessions:', err);
    }
  }, []);

  useEffect(() => {
    let isCancelled = false;
    apiClient
      .get('/api/research')
      .then((res) => {
        if (!isCancelled) {
          const loadedSessions = res.data || [];
          setSessions(loadedSessions);
          if (loadedSessions.length > 0) {
            setActiveSession((prev: any) => prev || loadedSessions[0]);
          }
        }
      })
      .catch((err) => {
        if (!isCancelled) console.warn('Could not load research sessions:', err);
      });

    return () => {
      isCancelled = true;
    };
  }, []);

  const createNewSession = async () => {
    try {
      const title = searchQuery.trim()
        ? `Research: ${searchQuery.slice(0, 32)}...`
        : `Session #${sessions.length + 1} (${new Date().toLocaleDateString()})`;
      const res = await apiClient.post('/api/research', {
        title,
        research_question: searchQuery.trim() || null,
      });
      setActiveSession(res.data);
      fetchSessions();
      toast.success(`Created research session "${title}".`);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to create session.'));
    }
  };

  const loadSession = async (id: number) => {
    try {
      const res = await apiClient.get(`/api/research/${id}`);
      setActiveSession(res.data);
      setShowHistory(false);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load session.'));
    }
  };

  const handleDeleteSession = async () => {
    if (!sessionToDelete) return;
    setIsDeletingSession(true);
    try {
      await apiClient.delete(`/api/research/${sessionToDelete.id}`);
      toast.success(`Deleted session "${sessionToDelete.title}".`);
      if (activeSession?.id === sessionToDelete.id) {
        setActiveSession(null);
      }
      setSessionToDelete(null);
      fetchSessions();
    } catch (err) {
      toast.error(getErrorMessage(err, 'Could not delete session.'));
    } finally {
      setIsDeletingSession(false);
    }
  };

  const handleAddNote = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeSession || !noteContent.trim() || isAddingNote) return;

    setIsAddingNote(true);
    try {
      await apiClient.post(`/api/research/${activeSession.id}/notes`, {
        content: noteContent.trim(),
        reference_case_id: selectedCaseId || undefined,
      });
      toast.success('Researcher note saved to session.');
      setNoteContent('');
      setShowNoteModal(false);
      loadSession(activeSession.id);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to add note to session.'));
    } finally {
      setIsAddingNote(false);
    }
  };

  const handleExecuteResearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const cleanQuery = searchQuery.trim();
    if (!cleanQuery || isLoading) return;

    setIsLoading(true);
    setQueryError(null);

    // Auto-create session if none active
    let currentSessionId = activeSession?.id;
    if (!currentSessionId) {
      try {
        const sessionRes = await apiClient.post('/api/research', {
          title: `Research: ${cleanQuery.slice(0, 36)}`,
          research_question: cleanQuery,
        });
        setActiveSession(sessionRes.data);
        currentSessionId = sessionRes.data.id;
        fetchSessions();
      } catch (err) {
        console.warn('Auto-session creation failed:', err);
      }
    }

    try {
      if (searchMode === 'SYNTHESIS') {
        setActiveView('SYNTHESIS');
        const res = await apiClient.post('/api/research/ask', {
          query: cleanQuery,
          top_k: 8,
          summary_mode: 'RESEARCH',
        });
        setSynthesisResult(res.data);
      } else {
        setActiveView('SEARCH');
        const res = await apiClient.post('/api/search', {
          query: cleanQuery,
          top_k: 8,
        });
        setPassageResults(res.data || []);
      }
    } catch (err: unknown) {
      setQueryError(getErrorMessage(err, 'Research request failed. Please check connection and try again.'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDownTextarea = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      handleExecuteResearch();
    }
  };

  const addCaseToSession = async (caseId: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!activeSession) {
      toast.warning('Please create or select an active research session first.');
      return;
    }
    try {
      await apiClient.post(`/api/research/${activeSession.id}/cases`, { case_id: caseId });
      loadSession(activeSession.id);
      toast.success('Case authority added to research session.');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save case to session.'));
    }
  };

  const addEvidenceToSession = async (evidence: any) => {
    if (!activeSession) {
      toast.warning('Please create or select an active research session first.');
      return;
    }
    try {
      await apiClient.post(`/api/research/${activeSession.id}/evidence`, {
        case_id: evidence.document_id || evidence.case_id || selectedCaseId,
        source_chunk_id: evidence.chunk_id || evidence.source_chunk_id || evidence.source_id,
        category: evidence.category || evidence.section || 'EVIDENCE',
        supporting_text: evidence.matched_text || evidence.supporting_text || evidence.text,
        page_number: evidence.page_number || evidence.page,
      });
      loadSession(activeSession.id);
      toast.success('Source passage pinned to session evidence.');
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to save evidence to session.'));
    }
  };

  const generateBrief = async () => {
    if (!activeSession) return;
    setIsGeneratingBrief(true);
    setActiveView('BRIEF');
    try {
      const res = await apiClient.post(`/api/research/${activeSession.id}/brief`);
      setBriefMarkdown(res.data.brief);
    } catch (err) {
      console.warn('Brief generation failed:', err);
      setBriefMarkdown('Failed to generate research brief. Please verify backend AI provider connectivity.');
    } finally {
      setIsGeneratingBrief(false);
    }
  };

  const openCase = async (caseId: number) => {
    setSelectedCaseId(caseId);
    setActiveView('CASE');
    setCaseData(null);
    try {
      const res = await apiClient.get(`/api/cases/${caseId}`);
      setCaseData(res.data);
      loadGraph(caseId, 1);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to load case profile.'));
    }
  };

  const loadGraph = async (caseId: number, depth: number = 1) => {
    setGraphDepth(depth);
    try {
      const res = await apiClient.get(`/api/cases/${caseId}/graph?depth=${depth}`);
      setGraphData(res.data);
    } catch (err) {
      console.warn('Citation graph unavailable:', err);
    }
  };

  const openComparison = async () => {
    if (!activeSession || (activeSession.cases?.length || 0) < 2) return;
    setActiveView('COMPARE');
    try {
      const caseIds = activeSession.cases.map((c: any) => c.case_id).slice(0, 5);
      const res = await apiClient.post('/api/compare', {
        case_ids: caseIds,
        research_question: activeSession.research_question || searchQuery || undefined,
      });
      setComparisonData(res.data);
    } catch (err) {
      toast.error(getErrorMessage(err, 'Failed to execute comparative analysis.'));
    }
  };

  const inspectSource = (source: any) => {
    setSelectedSource(source);
    setCopiedCitation(false);
  };

  const copySourceCitation = () => {
    if (!selectedSource) return;
    const caseName = selectedSource.case_name || 'Supreme Court Landmark';
    const court = selectedSource.court || 'Supreme Court of India';
    const year = selectedSource.year ? `(${selectedSource.year})` : '';
    const page = selectedSource.page_number ? `, p. ${selectedSource.page_number}` : '';
    const text = selectedSource.matched_text || selectedSource.supporting_text || selectedSource.text || '';

    const citationText = `"${text}"\n\n— ${caseName}, ${court} ${year}${page} [LEXORA Verified Extract]`;
    navigator.clipboard.writeText(citationText);
    setCopiedCitation(true);
    toast.success('Verbatim extract copied with primary citation.');
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#080c14] overflow-hidden text-sm font-sans selection:bg-blue-600/30">
      {/* Top Navigation */}
      <AppNavbar
        showSidebarToggle
        isSidebarOpen={isSidebarOpen}
        onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
      />

      {/* Main Layout Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar: Active Research Session */}
        <AnimatePresence>
          {isSidebarOpen && (
            <motion.aside
              initial={{ x: -280 }}
              animate={{ x: 0 }}
              exit={{ x: -280 }}
              transition={{ duration: 0.2 }}
              className="w-72 sm:w-80 border-r border-slate-800/80 bg-slate-950/70 flex flex-col z-20 absolute lg:relative h-full backdrop-blur-md shadow-xl"
            >
              {/* Session Header */}
              <div className="p-4 border-b border-slate-800/80">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400 font-mono">
                    Active Session
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setShowHistory(true)}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
                      title="Session History"
                      aria-label="View Session History"
                    >
                      <History size={14} />
                    </button>
                    <button
                      type="button"
                      onClick={createNewSession}
                      className="p-1.5 hover:bg-slate-800 text-slate-400 hover:text-white rounded-lg transition-colors"
                      title="New Research Session"
                      aria-label="Create New Research Session"
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>

                <h3 className="font-semibold text-slate-100 truncate text-xs">
                  {activeSession ? activeSession.title : 'No Session Selected'}
                </h3>

                {activeSession && (
                  <div className="mt-3 flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={generateBrief}
                      isLoading={isGeneratingBrief}
                      icon={<FileText size={13} />}
                      className="flex-1 text-xs"
                    >
                      Generate Brief
                    </Button>

                    <Button
                      variant="outline"
                      size="sm"
                      icon={<StickyNote size={13} />}
                      onClick={() => setShowNoteModal(true)}
                      title="Add note to session"
                    >
                      Note
                    </Button>
                  </div>
                )}
              </div>

              {/* Saved Cases, Evidence, and Notes */}
              <div className="flex-1 overflow-y-auto p-4 space-y-6 custom-scrollbar">
                {activeSession ? (
                  <>
                    {/* Saved Cases */}
                    <div>
                      <div className="flex items-center justify-between mb-2.5">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Saved Cases ({activeSession.cases?.length || 0})
                        </span>
                        {(activeSession.cases?.length || 0) >= 2 && (
                          <button
                            type="button"
                            onClick={openComparison}
                            className="text-[10px] text-blue-400 hover:underline flex items-center gap-1 font-semibold"
                          >
                            <Scale size={11} /> Compare (2-5)
                          </button>
                        )}
                      </div>

                      <div className="space-y-1.5">
                        {activeSession.cases?.map((c: any) => (
                          <div
                            key={c.id}
                            onClick={() => openCase(c.case_id)}
                            className="p-2.5 bg-slate-900/60 hover:bg-slate-850 rounded-lg border border-slate-800/80 cursor-pointer transition-colors group"
                          >
                            <div className="text-xs font-medium text-slate-200 group-hover:text-blue-400 truncate">
                              {c.case?.case_name || `Case #${c.case_id}`}
                            </div>
                            <div className="text-[10px] text-slate-500 mt-0.5">
                              {c.case?.court || 'Supreme Court'} • {c.case?.year || 'Indexed'}
                            </div>
                          </div>
                        ))}

                        {(!activeSession.cases || activeSession.cases.length === 0) && (
                          <div className="text-xs text-slate-500 italic py-2">
                            No cases saved in this session.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Saved Evidence */}
                    <div>
                      <div className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                        Saved Evidence ({activeSession.evidence?.length || 0})
                      </div>
                      <div className="space-y-2">
                        {activeSession.evidence?.map((e: any) => (
                          <div
                            key={e.id}
                            className="p-2.5 bg-slate-900/40 rounded-lg border border-slate-800/60 hover:border-slate-700 transition-colors cursor-pointer"
                            onClick={() => inspectSource(e)}
                          >
                            <div className="text-[10px] font-bold text-amber-400/90 mb-1 flex items-center gap-1">
                              <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                              <span>{e.category}</span>
                            </div>
                            <p className="text-xs text-slate-300 font-serif italic line-clamp-3">
                              "{e.supporting_text}"
                            </p>
                          </div>
                        ))}

                        {(!activeSession.evidence || activeSession.evidence.length === 0) && (
                          <div className="text-xs text-slate-500 italic py-2">
                            No excerpts saved to session evidence.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Researcher Notes */}
                    <div>
                      <div className="flex items-center justify-between mb-2.5">
                        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">
                          Researcher Notes ({activeSession.notes?.length || 0})
                        </span>
                        <button
                          type="button"
                          onClick={() => setShowNoteModal(true)}
                          className="text-[10px] text-blue-400 hover:underline flex items-center gap-1 font-semibold"
                        >
                          <Plus size={10} /> Add
                        </button>
                      </div>

                      <div className="space-y-2">
                        {activeSession.notes?.map((n: any) => (
                          <div
                            key={n.id}
                            className="p-2.5 bg-slate-900/40 rounded-lg border border-slate-800/60 text-xs text-slate-300 font-serif leading-relaxed"
                          >
                            <p>{n.content}</p>
                            <div className="text-[9px] text-slate-500 font-mono mt-1">
                              {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        ))}

                        {(!activeSession.notes || activeSession.notes.length === 0) && (
                          <div className="text-xs text-slate-500 italic py-2">
                            No research notes captured yet.
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3 text-center px-4">
                    <BookOpen size={32} className="opacity-20 text-blue-400" />
                    <p className="text-xs leading-relaxed font-sans">
                      Enter a legal research question to start capturing cases and verified excerpts.
                    </p>
                  </div>
                )}
              </div>
            </motion.aside>
          )}
        </AnimatePresence>

        {/* Center Panel: Research Workspace */}
        <main className="flex-1 flex flex-col bg-[#080c14] relative min-w-0 overflow-hidden">
          {/* Query Bar */}
          <div className="p-4 border-b border-slate-800/80 bg-slate-950/40 backdrop-blur-sm z-10">
            <form onSubmit={handleExecuteResearch} className="max-w-4xl mx-auto space-y-3">
              <div className="relative">
                <div className="flex items-center justify-between mb-1.5">
                  <label
                    htmlFor="research-query-input"
                    className="block text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5"
                  >
                    <Sparkles size={13} className="text-blue-400" />
                    <span>Legal Research Proposition or Inquiry</span>
                  </label>
                  <span className="text-[10px] text-slate-500 font-mono hidden sm:inline-block">
                    Press Ctrl+Enter to execute • Shift+Enter for new line
                  </span>
                </div>

                <div className="relative">
                  <textarea
                    id="research-query-input"
                    rows={2}
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={handleKeyDownTextarea}
                    placeholder="Enter proposition (e.g. proportionality test under Article 21, standards for Section 9 interim relief in arbitration, or lifting corporate veil under Companies Act)..."
                    className="w-full bg-slate-900/90 border border-slate-700/80 text-slate-100 placeholder-slate-500 rounded-xl p-3 pr-28 text-xs sm:text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-inner resize-y min-h-[64px]"
                  />

                  <div className="absolute right-2.5 bottom-2.5">
                    <Button
                      type="submit"
                      variant="primary"
                      size="sm"
                      isLoading={isLoading}
                      disabled={isLoading || !searchQuery.trim()}
                      icon={<CornerDownLeft size={13} />}
                      className="shadow-md shadow-blue-500/20"
                    >
                      {isLoading ? 'Synthesizing...' : 'Execute'}
                    </Button>
                  </div>
                </div>
              </div>

              {/* Research Controls: Mode Selection & Quick Views */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs pt-1">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider font-mono">
                    Mode:
                  </span>
                  <div className="flex rounded-lg bg-slate-900 border border-slate-800 p-0.5">
                    <button
                      type="button"
                      onClick={() => setSearchMode('SYNTHESIS')}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
                        searchMode === 'SYNTHESIS'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Sparkles size={12} />
                      <span>AI Legal Synthesis (RAG)</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setSearchMode('PASSAGES')}
                      className={`px-3 py-1 rounded-md text-xs font-medium transition-colors flex items-center gap-1.5 ${
                        searchMode === 'PASSAGES'
                          ? 'bg-blue-600 text-white shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      <Search size={12} />
                      <span>Passage Search</span>
                    </button>
                  </div>
                </div>

                {/* View switcher when results are available */}
                <div className="flex items-center gap-1">
                  {synthesisResult && (
                    <button
                      type="button"
                      onClick={() => setActiveView('SYNTHESIS')}
                      className={`px-2.5 py-1 rounded-lg text-xs transition-colors ${
                        activeView === 'SYNTHESIS'
                          ? 'bg-slate-800 text-blue-400 font-semibold'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Synthesis View
                    </button>
                  )}
                  {passageResults.length > 0 && (
                    <button
                      type="button"
                      onClick={() => setActiveView('SEARCH')}
                      className={`px-2.5 py-1 rounded-lg text-xs transition-colors ${
                        activeView === 'SEARCH'
                          ? 'bg-slate-800 text-blue-400 font-semibold'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Passages ({passageResults.length})
                    </button>
                  )}
                </div>
              </div>
            </form>
          </div>

          {/* Center Scrollable Content */}
          <div className="flex-1 overflow-y-auto p-4 md:p-8 custom-scrollbar">
            <div className="max-w-4xl mx-auto space-y-6">
              {/* Mandatory Legal Disclaimer & Corpus Scope Notice */}
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-2xl p-4 text-xs text-amber-200/90 shadow-sm backdrop-blur-sm">
                <div className="flex items-center gap-2 font-bold text-amber-300 mb-1">
                  <ShieldAlert size={16} className="text-amber-400 shrink-0" />
                  <span>Controlled Pilot Safeguards & Mandatory Verification Standard</span>
                </div>
                <p className="text-[11px] leading-relaxed text-amber-200/80">
                  <strong>Non-Reliance Notice:</strong> LEXORA provides AI-assisted legal research synthesis, not legal advice. Consequential legal claims and citations require independent verification by qualified legal counsel against official law reporters (SCR, SCC, AIR).
                </p>
                <p className="text-[11px] leading-relaxed text-amber-200/70 mt-1">
                  <strong>Indexed Corpus Scope:</strong> Grounded strictly against indexed landmark Supreme Court of India constitutional benches and major commercial authorities. Unindexed statutory rules and state tribunal orders fall outside verified scope.
                </p>
              </div>

              {/* Query Error Notification */}
              {queryError && (
                <div
                  role="alert"
                  className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start gap-3"
                >
                  <AlertCircle size={18} className="text-rose-400 shrink-0 mt-0.5" />
                  <div>
                    <h4 className="font-semibold text-rose-200">Research Request Failed</h4>
                    <p className="mt-0.5 leading-relaxed">{queryError}</p>
                  </div>
                </div>
              )}

              {/* VIEW 1: AI Legal Synthesis Result */}
              {activeView === 'SYNTHESIS' && synthesisResult && (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                  {/* Executive Answer Card */}
                  <div className="p-6 md:p-8 bg-slate-900/60 border border-slate-800 rounded-2xl shadow-xl relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-1 h-full bg-blue-500" />
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <Sparkles size={16} className="text-blue-400" />
                        <h2 className="text-xs font-bold uppercase tracking-widest text-blue-400">
                          AI Legal Synthesis & Answer
                        </h2>
                      </div>
                      <span className="text-[10px] text-slate-500 font-mono">
                        Query: "{synthesisResult.query}"
                      </span>
                    </div>

                    <div className="text-slate-100 text-sm leading-relaxed font-sans">
                      <SafeMarkdown
                        content={synthesisResult.answer}
                        onCitationClick={(cite) => {
                          const matchingSource = synthesisResult.sources?.find(
                            (s: any) =>
                              cite.includes(s.case_name) ||
                              cite.includes(s.source_id) ||
                              s.matched_text?.includes(cite)
                          );
                          if (matchingSource) {
                            inspectSource(matchingSource);
                          } else {
                            inspectSource({
                              case_name: cite,
                              matched_text: `Citation reference: ${cite}`,
                              court: 'Supreme Court Landmark',
                            });
                          }
                        }}
                      />
                    </div>

                    {/* Abstention / Insufficient Evidence Notification */}
                    {synthesisResult.limitations && (
                      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-start gap-2.5 text-xs text-slate-400 bg-slate-950/40 p-3.5 rounded-xl">
                        <AlertCircle size={15} className="text-amber-400 shrink-0 mt-0.5" />
                        <div>
                          <strong className="text-slate-300">Corpus Limitations & Scope:</strong>
                          <p className="mt-0.5 leading-relaxed text-slate-400 font-serif">
                            {synthesisResult.limitations}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Key Findings Grid */}
                  {synthesisResult.key_findings && synthesisResult.key_findings.length > 0 && (
                    <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
                        <Scale size={14} className="text-blue-400" />
                        <span>Key Legal Findings ({synthesisResult.key_findings.length})</span>
                      </h3>

                      <div className="space-y-3">
                        {synthesisResult.key_findings.map((item: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80 flex items-start gap-3"
                          >
                            <span className="font-mono text-xs font-bold text-blue-400 mt-0.5">
                              #{idx + 1}
                            </span>
                            <div className="flex-1 min-w-0">
                              <p className="text-xs text-slate-200 leading-relaxed font-serif">
                                {item.finding}
                              </p>
                              {item.sources && item.sources.length > 0 && (
                                <div className="mt-2 flex gap-1.5 flex-wrap">
                                  {item.sources.map((s: string) => (
                                    <button
                                      key={s}
                                      type="button"
                                      onClick={() => {
                                        const src = synthesisResult.sources?.find((srcItem: any) => srcItem.source_id === s);
                                        if (src) inspectSource(src);
                                      }}
                                      className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950/60 text-blue-300 border border-blue-900/50 hover:bg-blue-900/40 transition-colors"
                                    >
                                      Source: {s}
                                    </button>
                                  ))}
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Grounded Legal Principles */}
                  {synthesisResult.legal_principles && synthesisResult.legal_principles.length > 0 && (
                    <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl">
                      <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-4 flex items-center gap-2">
                        <BookOpen size={14} className="text-purple-400" />
                        <span>Established Principles of Law</span>
                      </h3>

                      <div className="space-y-3">
                        {synthesisResult.legal_principles.map((lp: any, idx: number) => (
                          <div
                            key={idx}
                            className="p-3.5 bg-slate-950/60 rounded-xl border border-slate-800/80 border-l-2 border-l-purple-500"
                          >
                            <p className="text-xs text-purple-100 font-serif leading-relaxed">
                              {lp.principle}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Supporting Authorities & Cited Passages */}
                  {synthesisResult.sources && synthesisResult.sources.length > 0 && (
                    <div className="p-6 bg-slate-900/40 border border-slate-800 rounded-2xl">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">
                          Indexed Supporting Passages ({synthesisResult.sources.length})
                        </h3>
                        <span className="text-[10px] text-slate-500 font-mono">
                          Evidence Traceability Verified
                        </span>
                      </div>

                      <div className="space-y-3">
                        {synthesisResult.sources.map((src: any, idx: number) => {
                          const isSaved = activeSession?.cases?.some(
                            (c: any) => c.case?.case_name === src.case_name
                          );

                          return (
                            <div
                              key={idx}
                              className="p-4 bg-slate-950/60 rounded-xl border border-slate-800/80 hover:border-slate-700 transition-colors space-y-2.5"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="min-w-0">
                                  <h4
                                    onClick={() => src.document_id && openCase(src.document_id)}
                                    className="font-semibold text-xs text-slate-200 hover:text-blue-400 cursor-pointer truncate"
                                  >
                                    {src.case_name}
                                  </h4>
                                  <div className="text-[10px] text-slate-500 mt-0.5">
                                    {src.court} • {src.year} • Page {src.page_number || 'N/A'} • {src.section || 'Passage'}
                                  </div>
                                </div>

                                <div className="flex items-center gap-1.5 shrink-0">
                                  <Button
                                    variant="secondary"
                                    size="sm"
                                    icon={<FileText size={12} />}
                                    onClick={() => inspectSource(src)}
                                  >
                                    Inspect
                                  </Button>

                                  {src.document_id && (
                                    <Button
                                      variant={isSaved ? 'primary' : 'outline'}
                                      size="sm"
                                      icon={isSaved ? <Bookmark size={12} /> : <Plus size={12} />}
                                      onClick={(e) => addCaseToSession(src.document_id, e)}
                                      disabled={isSaved}
                                    >
                                      {isSaved ? 'Saved' : 'Save'}
                                    </Button>
                                  )}
                                </div>
                              </div>

                              <div className="p-3 bg-slate-900/60 rounded-lg border-l-2 border-l-blue-500/70 text-xs font-serif italic text-slate-300 leading-relaxed">
                                "{src.matched_text}"
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </motion.div>
              )}

              {/* VIEW 2: Raw Passage Search Results */}
              {activeView === 'SEARCH' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-xs text-slate-400 pb-2 border-b border-slate-800">
                    <span>Indexed Passages Matching Query ({passageResults.length})</span>
                    <span className="font-mono text-[10px]">RRF Hybrid Ranking</span>
                  </div>

                  {passageResults.map((res: any, idx: number) => {
                    const cid = res.document_id || idx + 1;
                    const isSaved = activeSession?.cases?.some((c: any) => c.case_id === cid);

                    return (
                      <div
                        key={idx}
                        className="bg-slate-900/50 border border-slate-800 hover:border-slate-700 rounded-xl p-5 transition-colors space-y-3"
                      >
                        <div className="flex justify-between items-start gap-4">
                          <div className="flex-1 min-w-0">
                            <h3
                              onClick={() => openCase(cid)}
                              className="font-bold text-sm text-slate-100 hover:text-blue-400 cursor-pointer truncate"
                            >
                              {res.case_name}
                            </h3>
                            <div className="text-xs text-slate-400 mt-0.5">
                              {res.court} • {res.year} • Page {res.page_number} • Relevance:{' '}
                              {Math.round((res.relevance_score || 0) * 100)}%
                            </div>
                          </div>

                          <div className="flex gap-2 shrink-0">
                            <Button
                              variant={isSaved ? 'primary' : 'outline'}
                              size="sm"
                              icon={isSaved ? <Bookmark size={13} /> : <Plus size={13} />}
                              onClick={(e) => addCaseToSession(cid, e)}
                              disabled={isSaved}
                            >
                              {isSaved ? 'Saved' : 'Save Case'}
                            </Button>
                            <Button
                              variant="secondary"
                              size="sm"
                              icon={<ChevronRight size={14} />}
                              onClick={() => openCase(cid)}
                              title="Open Dossier"
                            >
                              Open
                            </Button>
                          </div>
                        </div>

                        <div className="text-xs text-slate-300 bg-slate-950/60 p-4 rounded-lg border-l-2 border-l-blue-500 font-serif leading-relaxed italic">
                          "{res.matched_text}"
                        </div>
                      </div>
                    );
                  })}

                  {passageResults.length === 0 && !isLoading && (
                    <div className="text-center py-16 text-slate-500 text-sm">
                      No passages found for this query. Try broader legal terms or switch to AI Legal Synthesis.
                    </div>
                  )}
                </div>
              )}

              {/* VIEW 3: Case Intelligence Profile */}
              {activeView === 'CASE' && (
                <div className="h-[750px] rounded-2xl overflow-hidden border border-slate-800 relative bg-[#080c14]">
                  <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      icon={<GitFork size={13} />}
                      onClick={() => setActiveView('GRAPH')}
                    >
                      Precedent Graph
                    </Button>
                    <button
                      type="button"
                      onClick={() => setActiveView('SYNTHESIS')}
                      className="p-1.5 bg-slate-800/90 text-slate-400 hover:text-white border border-slate-700 rounded-lg transition-colors"
                      title="Close Dossier"
                    >
                      <X size={15} />
                    </button>
                  </div>

                  <CaseIntelligence
                    caseData={caseData}
                    onViewSource={(sourceId) => {
                      inspectSource({
                        case_name: caseData?.case_name || 'Selected Authority',
                        matched_text: `Extracted passage anchor ID: ${sourceId}`,
                        court: caseData?.court,
                      });
                    }}
                    onBookmarkCase={(cid) => addCaseToSession(cid)}
                    isBookmarked={activeSession?.cases?.some((c: any) => c.case_id === selectedCaseId)}
                    onRefreshCase={() => selectedCaseId && openCase(selectedCaseId)}
                  />
                </div>
              )}

              {/* VIEW 4: Comparative Intelligence Matrix */}
              {activeView === 'COMPARE' && (
                <div className="h-[750px] rounded-2xl overflow-hidden border border-slate-800 relative bg-[#080c14]">
                  <ComparativeIntelligence
                    comparisonData={comparisonData}
                    onViewSource={(sourceId) => {
                      inspectSource({
                        case_name: 'Comparative Source Authority',
                        matched_text: `Verified source anchor: ${sourceId}`,
                      });
                    }}
                    onClose={() => setActiveView('SYNTHESIS')}
                  />
                </div>
              )}

              {/* VIEW 5: Precedent Graph */}
              {activeView === 'GRAPH' && (
                <div className="h-[750px] rounded-2xl overflow-hidden border border-slate-800 relative bg-[#080c14]">
                  <div className="absolute top-4 left-4 z-20 flex items-center gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => setActiveView('CASE')}
                    >
                      ← Back to Dossier
                    </Button>
                  </div>

                  <PrecedentGraph
                    graphData={graphData}
                    depth={graphDepth}
                    onDepthChange={(newDepth) => selectedCaseId && loadGraph(selectedCaseId, newDepth)}
                    onNodeClick={(id) => openCase(Number(id))}
                  />
                </div>
              )}

              {/* VIEW 6: Research Brief View */}
              {activeView === 'BRIEF' && (
                <div className="p-6 md:p-8 bg-slate-900/50 border border-slate-800 rounded-2xl">
                  <div className="flex justify-between items-center mb-6 pb-4 border-b border-slate-800">
                    <div className="flex items-center gap-2">
                      <FileText size={18} className="text-blue-400" />
                      <h2 className="text-lg font-serif font-bold text-white">Synthesized Research Brief</h2>
                    </div>
                    <button
                      type="button"
                      onClick={() => setActiveView('SYNTHESIS')}
                      className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  {isGeneratingBrief ? (
                    <div className="flex flex-col items-center justify-center py-24 text-slate-400 gap-3">
                      <Loader2 className="animate-spin text-blue-500" size={36} />
                      <span className="font-serif tracking-widest uppercase text-xs">
                        Synthesizing verified authorities and citations...
                      </span>
                    </div>
                  ) : (
                    <div className="text-slate-200 leading-relaxed font-serif">
                      <SafeMarkdown content={briefMarkdown || 'No brief content available.'} />
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>

      {/* History Modal */}
      <AnimatePresence>
        {showHistory && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl w-full max-w-2xl flex flex-col max-h-[80vh] overflow-hidden"
            >
              <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-950/60">
                <h3 className="font-bold text-base text-slate-100 flex items-center gap-2">
                  <History size={16} className="text-blue-400" />
                  <span>Research Session History</span>
                </h3>
                <button
                  type="button"
                  onClick={() => setShowHistory(false)}
                  className="p-1.5 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-5 overflow-y-auto space-y-2.5 custom-scrollbar">
                {sessions.map((s) => (
                  <div
                    key={s.id}
                    className="p-4 bg-slate-950/50 hover:bg-slate-850 border border-slate-800/80 rounded-xl flex justify-between items-center group transition-colors"
                  >
                    <div
                      onClick={() => loadSession(s.id)}
                      className="flex-1 cursor-pointer min-w-0 pr-4"
                    >
                      <div className="font-semibold text-slate-200 group-hover:text-blue-400 text-xs truncate">
                        {s.title}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        Updated {new Date(s.updated_at).toLocaleString()} • {s.cases?.length || 0} Cases •{' '}
                        {s.evidence?.length || 0} Evidence • {s.notes?.length || 0} Notes
                      </div>
                    </div>

                    <div className="flex items-center gap-1 shrink-0">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={(e) => {
                          e.stopPropagation();
                          setSessionToDelete(s);
                        }}
                        className="text-slate-500 hover:text-rose-400 p-1.5"
                        title="Delete Session"
                      >
                        <Trash2 size={13} />
                      </Button>
                      <button
                        type="button"
                        onClick={() => loadSession(s.id)}
                        className="p-1 text-slate-600 group-hover:text-blue-400"
                        title="Open Session"
                      >
                        <ChevronRight size={16} />
                      </button>
                    </div>
                  </div>
                ))}

                {sessions.length === 0 && (
                  <div className="text-center text-slate-500 py-12 text-xs">
                    No previous research sessions found.
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Source Passage Evidence Inspection Drawer */}
      <AnimatePresence>
        {selectedSource && (
          <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl w-full max-w-lg p-6 overflow-hidden"
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1 mb-1 font-mono">
                    <FileText size={12} />
                    <span>Source Evidence Inspector</span>
                  </div>
                  <h3 className="font-bold text-slate-100 text-sm">
                    {selectedSource.case_name || 'Supreme Court Landmark Authority'}
                  </h3>
                  <div className="text-xs text-slate-400 mt-0.5">
                    {selectedSource.court || 'Supreme Court of India'}
                    {selectedSource.year ? ` • (${selectedSource.year})` : ''}
                    {selectedSource.page_number ? ` • Page ${selectedSource.page_number}` : ''}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => setSelectedSource(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
                >
                  <X size={16} />
                </button>
              </div>

              {/* Verbatim Excerpt */}
              <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800/80 mb-5">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block mb-1">
                  Verbatim Passage Excerpt
                </span>
                <p className="text-xs text-slate-200 font-serif italic leading-relaxed">
                  "{selectedSource.matched_text || selectedSource.supporting_text || selectedSource.text}"
                </p>
              </div>

              {/* Action buttons */}
              <div className="flex items-center justify-between pt-2">
                <Button
                  variant="secondary"
                  size="sm"
                  icon={copiedCitation ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
                  onClick={copySourceCitation}
                >
                  {copiedCitation ? 'Copied Citation!' : 'Copy with Citation'}
                </Button>

                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    addEvidenceToSession(selectedSource);
                    setSelectedSource(null);
                  }}
                >
                  Pin as Evidence
                </Button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Add Researcher Note Modal */}
      <Modal
        isOpen={showNoteModal}
        onClose={() => setShowNoteModal(false)}
        title="Add Researcher Annotation"
        maxWidth="md"
      >
        <form onSubmit={handleAddNote} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1.5">
              Annotation Note
            </label>
            <textarea
              rows={4}
              value={noteContent}
              onChange={(e) => setNoteContent(e.target.value)}
              placeholder="Record analytical impressions, doctrinal distinctions, or draft submission thoughts..."
              className="w-full bg-slate-950 border border-slate-800 text-slate-100 placeholder-slate-500 rounded-xl p-3 text-xs outline-none focus:border-blue-500 resize-y"
              required
              autoFocus
            />
          </div>

          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-800">
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowNoteModal(false)}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="sm"
              isLoading={isAddingNote}
              disabled={!noteContent.trim() || isAddingNote}
            >
              Save Note
            </Button>
          </div>
        </form>
      </Modal>

      {/* Delete Session Confirmation Dialog */}
      <ConfirmDialog
        isOpen={!!sessionToDelete}
        onClose={() => setSessionToDelete(null)}
        onConfirm={handleDeleteSession}
        title="Delete Research Session"
        message={`Are you sure you want to delete session "${sessionToDelete?.title}"? All pinned cases, evidence, and notes in this session will be removed.`}
        confirmLabel="Delete Session"
        isDestructive
        isLoading={isDeletingSession}
      />
    </div>
  );
}
