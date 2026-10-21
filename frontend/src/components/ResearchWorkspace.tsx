import React, { useState, useEffect, useCallback } from 'react';
import {
  Search, Plus, History, FileText, Bookmark, ChevronRight, X, Loader2,
  BookOpen, ShieldAlert, Sparkles, Scale, GitFork,
  Copy, Check, AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import AppNavbar from './common/AppNavbar';
import SafeMarkdown from './common/SafeMarkdown';
import CaseIntelligence from './CaseIntelligence';
import ComparativeIntelligence from './ComparativeIntelligence';
import PrecedentGraph from './PrecedentGraph';
import apiClient, { getErrorMessage } from '../api/client';

export type ActiveWorkspaceView = 'SYNTHESIS' | 'SEARCH' | 'CASE' | 'COMPARE' | 'GRAPH' | 'BRIEF';

export default function ResearchWorkspace() {
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

  // Initialize: fetch existing sessions
  const fetchSessions = useCallback(async () => {
    try {
      const res = await apiClient.get('/api/research');
      setSessions(res.data || []);
      if (res.data && res.data.length > 0 && !activeSession) {
        setActiveSession(res.data[0]);
      }
    } catch (err) {
      console.warn('Could not load research sessions:', err);
    }
  }, [activeSession]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

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
    } catch (err) {
      console.error('Failed to create session', err);
    }
  };

  const loadSession = async (id: number) => {
    try {
      const res = await apiClient.get(`/api/research/${id}`);
      setActiveSession(res.data);
      setShowHistory(false);
    } catch (err) {
      console.error('Failed to load session', err);
    }
  };

  const handleExecuteResearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchQuery.trim() || isLoading) return;

    setIsLoading(true);
    setQueryError(null);

    // Auto-create session if none active
    let currentSessionId = activeSession?.id;
    if (!currentSessionId) {
      try {
        const sessionRes = await apiClient.post('/api/research', {
          title: `Research: ${searchQuery.slice(0, 36)}`,
          research_question: searchQuery,
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
          query: searchQuery,
          top_k: 8,
          summary_mode: 'RESEARCH',
        });
        setSynthesisResult(res.data);
      } else {
        setActiveView('SEARCH');
        const res = await apiClient.post('/api/search', {
          query: searchQuery,
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

  const addCaseToSession = async (caseId: number, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!activeSession) return;
    try {
      await apiClient.post(`/api/research/${activeSession.id}/cases`, { case_id: caseId });
      loadSession(activeSession.id);
    } catch (err) {
      console.error('Failed to save case to session:', err);
    }
  };

  const addEvidenceToSession = async (evidence: any) => {
    if (!activeSession) return;
    try {
      await apiClient.post(`/api/research/${activeSession.id}/evidence`, {
        case_id: evidence.document_id || evidence.case_id || selectedCaseId,
        source_chunk_id: evidence.chunk_id || evidence.source_chunk_id || evidence.source_id,
        category: evidence.category || evidence.section || 'EVIDENCE',
        supporting_text: evidence.matched_text || evidence.supporting_text || evidence.text,
        page_number: evidence.page_number || evidence.page,
      });
      loadSession(activeSession.id);
    } catch (err) {
      console.error('Failed to save evidence to session:', err);
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
      console.error('Failed to load case profile:', err);
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
      const caseIds = activeSession.cases.map((c: any) => c.case_id);
      const res = await apiClient.post('/api/compare', {
        case_ids: caseIds,
        research_question: activeSession.research_question || searchQuery || undefined,
      });
      setComparisonData(res.data);
    } catch (err) {
      console.error('Failed to run comparative intelligence:', err);
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

    const citationText = `"${text}" — ${caseName}, ${court} ${year}${page} [LEXORA Verified Extract]`;
    navigator.clipboard.writeText(citationText);
    setCopiedCitation(true);
    setTimeout(() => setCopiedCitation(false), 2000);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#080c14] overflow-hidden text-sm font-sans selection:bg-blue-600/30">
      {/* Top Navigation */}
      <AppNavbar
        showSidebarToggle
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
              className="w-72 border-r border-slate-800/80 bg-slate-950/70 flex flex-col z-20 absolute lg:relative h-full backdrop-blur-md shadow-xl"
            >
              {/* Session Header */}
              <div className="p-4 border-b border-slate-800/80">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-widest text-blue-400">
                    Active Session
                  </span>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setShowHistory(true)}
                      className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded"
                      title="Session History"
                    >
                      <History size={14} />
                    </button>
                    <button
                      type="button"
                      onClick={createNewSession}
                      className="p-1 hover:bg-slate-800 text-slate-400 hover:text-white rounded"
                      title="New Session"
                    >
                      <Plus size={14} />
                    </button>
                  </div>
                </div>

                <h3 className="font-semibold text-slate-100 truncate text-xs">
                  {activeSession ? activeSession.title : 'No Session Selected'}
                </h3>

                {activeSession && (
                  <button
                    type="button"
                    onClick={generateBrief}
                    disabled={isGeneratingBrief}
                    className="w-full mt-3 py-1.5 bg-blue-600/10 hover:bg-blue-600/20 text-blue-400 border border-blue-500/30 rounded-md text-xs font-semibold transition-colors flex items-center justify-center gap-2"
                  >
                    {isGeneratingBrief ? (
                      <>
                        <Loader2 size={13} className="animate-spin" />
                        <span>Synthesizing...</span>
                      </>
                    ) : (
                      <>
                        <FileText size={13} />
                        <span>Generate Brief</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {/* Saved Cases & Evidence */}
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
                            <Scale size={11} /> Compare
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
                            className="p-2.5 bg-slate-900/40 rounded-lg border border-slate-800/60"
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
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center h-full text-slate-500 gap-3 text-center px-4">
                    <BookOpen size={32} className="opacity-20 text-blue-400" />
                    <p className="text-xs leading-relaxed">
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
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <div className="absolute inset-y-0 left-3.5 flex items-center pointer-events-none text-slate-500">
                    <Search size={16} />
                  </div>
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Ask a constitutional or commercial research question (e.g. proportionality standard under Article 21)..."
                    className="w-full bg-slate-900/90 border border-slate-700/80 text-slate-100 placeholder-slate-500 rounded-xl py-2.5 pl-11 pr-4 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-inner"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading || !searchQuery.trim()}
                  className="px-5 py-2.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium text-sm transition-all shadow-md shadow-blue-500/20 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 shrink-0"
                >
                  {isLoading ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Synthesizing...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles size={16} />
                      <span>Execute Research</span>
                    </>
                  )}
                </button>
              </div>

              {/* Research Controls: Mode Selection & Quick Views */}
              <div className="flex items-center justify-between text-xs pt-1">
                <div className="flex items-center gap-2">
                  <span className="text-slate-500 text-[11px] uppercase font-bold tracking-wider">Mode:</span>
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
                      className={`px-2.5 py-1 rounded text-xs transition-colors ${
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
                      className={`px-2.5 py-1 rounded text-xs transition-colors ${
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
              <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 text-xs text-amber-200/90 shadow-sm backdrop-blur-sm">
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
                <div className="p-4 bg-rose-500/10 border border-rose-500/30 rounded-xl text-rose-300 text-xs flex items-start gap-3">
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

                    <div className="text-slate-100 text-sm leading-relaxed">
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
                      <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-start gap-2.5 text-xs text-slate-400 bg-slate-950/40 p-3 rounded-lg">
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
                                  <button
                                    type="button"
                                    onClick={() => inspectSource(src)}
                                    className="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded text-xs transition-colors flex items-center gap-1"
                                  >
                                    <FileText size={12} /> Inspect
                                  </button>

                                  {src.document_id && (
                                    <button
                                      type="button"
                                      onClick={(e) => addCaseToSession(src.document_id, e)}
                                      disabled={isSaved}
                                      className={`px-2.5 py-1 rounded text-xs transition-colors flex items-center gap-1 ${
                                        isSaved
                                          ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50'
                                          : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
                                      }`}
                                    >
                                      {isSaved ? <Bookmark size={12} /> : <Plus size={12} />}
                                      <span>{isSaved ? 'Saved' : 'Save'}</span>
                                    </button>
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
                            <button
                              type="button"
                              onClick={(e) => addCaseToSession(cid, e)}
                              disabled={isSaved}
                              className={`flex items-center gap-1 text-xs px-3 py-1.5 rounded transition-colors ${
                                isSaved
                                  ? 'bg-emerald-950/40 text-emerald-400 border border-emerald-900/50'
                                  : 'bg-slate-800 text-slate-300 hover:bg-slate-750 border border-slate-700'
                              }`}
                            >
                              {isSaved ? <Bookmark size={13} /> : <Plus size={13} />}
                              <span>{isSaved ? 'Saved' : 'Save Case'}</span>
                            </button>
                            <button
                              type="button"
                              onClick={() => openCase(cid)}
                              className="p-1.5 bg-slate-800 text-slate-300 hover:bg-slate-700 rounded border border-slate-700"
                              title="Open Dossier"
                            >
                              <ChevronRight size={14} />
                            </button>
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
                      No passages found for this search query. Try broader legal terms or switch to AI Legal Synthesis.
                    </div>
                  )}
                </div>
              )}

              {/* VIEW 3: Case Intelligence Profile */}
              {activeView === 'CASE' && (
                <div className="h-[750px] rounded-2xl overflow-hidden border border-slate-800 relative bg-[#080c14]">
                  <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => setActiveView('GRAPH')}
                      className="px-3 py-1.5 bg-slate-800/90 text-blue-400 border border-slate-700 rounded-md text-xs font-semibold hover:bg-slate-700 transition-colors flex items-center gap-1.5"
                    >
                      <GitFork size={13} />
                      <span>Precedent Graph</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveView('SYNTHESIS')}
                      className="p-1.5 bg-slate-800/90 text-slate-400 hover:text-white border border-slate-700 rounded-md transition-colors"
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
                        matched_text: `Extracted passage ID: ${sourceId}`,
                        court: caseData?.court,
                      });
                    }}
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
                    <button
                      type="button"
                      onClick={() => setActiveView('CASE')}
                      className="px-3 py-1.5 bg-slate-800/90 text-slate-200 border border-slate-700 rounded-md text-xs font-semibold hover:bg-slate-700 transition-colors"
                    >
                      ← Back to Dossier
                    </button>
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
                      className="p-1.5 text-slate-400 hover:text-white rounded"
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
                  className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white"
                >
                  <X size={18} />
                </button>
              </div>

              <div className="p-5 overflow-y-auto space-y-2.5 custom-scrollbar">
                {sessions.map((s) => (
                  <div
                    key={s.id}
                    onClick={() => loadSession(s.id)}
                    className="p-4 bg-slate-950/50 hover:bg-slate-850 border border-slate-800/80 rounded-xl cursor-pointer flex justify-between items-center group transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-slate-200 group-hover:text-blue-400 text-xs">
                        {s.title}
                      </div>
                      <div className="text-[10px] text-slate-500 mt-1">
                        Updated {new Date(s.updated_at).toLocaleString()} • {s.cases?.length || 0} Cases •{' '}
                        {s.evidence?.length || 0} Evidence Items
                      </div>
                    </div>
                    <ChevronRight size={16} className="text-slate-600 group-hover:text-blue-400" />
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
                  <div className="text-[10px] font-bold uppercase tracking-wider text-blue-400 flex items-center gap-1 mb-1">
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
                  className="p-1 text-slate-400 hover:text-white rounded"
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
                <button
                  type="button"
                  onClick={copySourceCitation}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-slate-800 hover:bg-slate-750 text-slate-200 text-xs rounded-lg border border-slate-700 transition-colors"
                >
                  {copiedCitation ? (
                    <>
                      <Check size={13} className="text-emerald-400" />
                      <span className="text-emerald-400">Copied Citation!</span>
                    </>
                  ) : (
                    <>
                      <Copy size={13} />
                      <span>Copy with Citation</span>
                    </>
                  )}
                </button>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      addEvidenceToSession(selectedSource);
                      setSelectedSource(null);
                    }}
                    className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-500 text-white font-medium text-xs rounded-lg transition-colors shadow-md"
                  >
                    Save as Evidence
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
