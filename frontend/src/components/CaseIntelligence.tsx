import React, { useState, useEffect } from 'react';
import {
  Scale, FileText, CheckCircle2, Bookmark,
  TrendingUp, Clock, BookOpen, AlertCircle, Loader2, Sparkles
} from 'lucide-react';
import { motion } from 'framer-motion';
import CaseTimeline from './CaseTimeline';
import SafeMarkdown from './common/SafeMarkdown';
import apiClient, { getErrorMessage } from '../api/client';

interface CaseIntelligenceProps {
  caseData: any;
  onViewSource: (sourceId: string) => void;
  onRefreshCase?: () => void;
}

export const CaseIntelligence: React.FC<CaseIntelligenceProps> = ({
  caseData,
  onViewSource,
  onRefreshCase,
}) => {
  const [activeTab, setActiveTab] = useState('Executive');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisError, setAnalysisError] = useState<string | null>(null);

  const tabs = [
    'Executive',
    'Facts',
    'Issues',
    'Arguments',
    'Reasoning',
    'Principles',
    'Outcome',
    'Timeline',
  ];

  useEffect(() => {
    setActiveTab('Executive');
    setAnalysisError(null);
  }, [caseData?.id]);

  if (!caseData) {
    return (
      <div className="h-full flex items-center justify-center p-8 text-slate-500 bg-[#080c14]">
        <div className="text-center">
          <Scale size={36} className="mx-auto mb-3 opacity-30 text-blue-400" />
          <p className="text-sm">Select an authority or case to view its intelligence profile.</p>
        </div>
      </div>
    );
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setAnalysisError(null);
    try {
      await apiClient.post(`/api/cases/${caseData.id}/analyze`);
      if (onRefreshCase) {
        onRefreshCase();
      }
    } catch (err: unknown) {
      setAnalysisError(getErrorMessage(err, 'Failed to trigger case intelligence analysis.'));
    } finally {
      setIsAnalyzing(false);
    }
  };

  const isAnalyzed = caseData.analysis_status === 'COMPLETE' || !!caseData.executive_summary;

  return (
    <div className="flex flex-col h-full bg-[#080c14] border-l border-slate-800/80 overflow-hidden">
      {/* Header Profile */}
      <div className="p-6 border-b border-slate-800/80 bg-slate-900/40">
        <div className="flex justify-between items-start gap-4 mb-3">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1.5 text-xs font-bold uppercase tracking-widest text-blue-400">
              <Scale size={14} />
              <span>Case Intelligence Dossier</span>
              {isAnalyzed ? (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-mono">
                  Indexed
                </span>
              ) : (
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 font-mono">
                  Pending Analysis
                </span>
              )}
            </div>

            <h2 className="text-xl md:text-2xl font-serif font-bold text-white leading-snug">
              {caseData.case_name}
            </h2>

            <div className="text-xs text-slate-400 mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
              <span className="font-medium text-slate-300">{caseData.court}</span>
              <span className="text-slate-600">•</span>
              <span>
                {caseData.decision_date
                  ? new Date(caseData.decision_date).toLocaleDateString('en-GB', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })
                  : caseData.year || 'Date Unrecorded'}
              </span>
              {caseData.case_number && (
                <>
                  <span className="text-slate-600">•</span>
                  <span className="font-mono text-slate-400">{caseData.case_number}</span>
                </>
              )}
            </div>
          </div>

          <div className="flex gap-2 shrink-0">
            {!isAnalyzed && (
              <button
                type="button"
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-md shadow transition-colors disabled:opacity-50"
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 size={13} className="animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <Sparkles size={13} />
                    <span>Analyze Case</span>
                  </>
                )}
              </button>
            )}
            <button
              type="button"
              className="p-2 bg-slate-800/80 hover:bg-slate-750 text-slate-400 hover:text-white rounded-md border border-slate-700/60 transition-colors"
              title="Bookmark Case"
            >
              <Bookmark size={15} />
            </button>
          </div>
        </div>

        {/* Topics Tags */}
        {caseData.legal_topics && (
          <div className="flex gap-1.5 mt-3 flex-wrap">
            {caseData.legal_topics.split(',').map((topic: string) => (
              <span
                key={topic}
                className="px-2 py-0.5 bg-slate-800/60 text-slate-300 text-[10px] font-medium tracking-wide rounded border border-slate-700/60"
              >
                {topic.trim()}
              </span>
            ))}
          </div>
        )}

        {analysisError && (
          <div className="mt-3 p-2.5 rounded bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle size={14} className="shrink-0" />
            <span>{analysisError}</span>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800/80 px-4 bg-slate-950/60 overflow-x-auto hide-scrollbar">
        {tabs.map((tab) => (
          <button
            key={tab}
            type="button"
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-3 text-xs font-medium border-b-2 transition-colors whitespace-nowrap ${
              activeTab === tab
                ? 'border-blue-500 text-blue-400 font-semibold'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            {tab === 'Timeline' ? (
              <span className="flex items-center gap-1.5">
                <Clock size={13} /> {tab}
              </span>
            ) : (
              tab
            )}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto bg-[#080c14] custom-scrollbar">
        {activeTab === 'Timeline' && (
          <CaseTimeline
            timelineData={caseData}
            onViewSource={(event) => onViewSource(event.source_chunk_id || `chunk_${caseData.id}`)}
          />
        )}

        {activeTab !== 'Timeline' && (
          <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-8">
            {/* Executive Summary */}
            {activeTab === 'Executive' && (
              <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                <div className="p-6 bg-slate-900/50 rounded-xl border border-slate-800 shadow-xl relative overflow-hidden">
                  <div className="absolute top-0 left-0 w-1 h-full bg-blue-500"></div>
                  <h3 className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-3 flex items-center gap-2">
                    <TrendingUp size={14} /> Executive Legal Synthesis
                  </h3>
                  {caseData.executive_summary ? (
                    <div className="text-slate-200 text-sm leading-relaxed font-serif">
                      <SafeMarkdown content={caseData.executive_summary} />
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm italic">
                      No executive summary has been generated for this case record yet.
                    </p>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  <div className="p-5 bg-slate-900/40 rounded-xl border border-slate-800">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                      <Scale size={13} className="text-blue-400" /> Key Issues Framed
                    </h4>
                    {caseData.issues && caseData.issues.length > 0 ? (
                      <ul className="space-y-2.5">
                        {caseData.issues.slice(0, 4).map((issue: any, i: number) => (
                          <li key={i} className="text-xs text-slate-300 flex items-start gap-2 leading-relaxed">
                            <span className="text-blue-400 mt-0.5">•</span>
                            <span>{issue.issue_text}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-slate-500 text-xs italic">No legal issues mapped.</p>
                    )}
                  </div>

                  <div className="p-5 bg-slate-900/40 rounded-xl border border-slate-800">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-1.5">
                      <CheckCircle2 size={13} className="text-emerald-400" /> Ruling & Disposition
                    </h4>
                    {caseData.decision ? (
                      <p className="text-xs text-slate-200 leading-relaxed font-serif">
                        {caseData.decision}
                      </p>
                    ) : (
                      <p className="text-slate-500 text-xs italic">Disposition text not extracted.</p>
                    )}
                  </div>
                </div>
              </motion.div>
            )}

            {/* Material Facts */}
            {activeTab === 'Facts' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">
                    Extracted Factual Record ({caseData.facts?.length || 0})
                  </h3>
                </div>

                <div className="space-y-3">
                  {caseData.facts?.map((fact: any, i: number) => (
                    <div
                      key={i}
                      className="p-4 rounded-lg bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition-colors flex gap-4 items-start"
                    >
                      <div className="w-24 shrink-0">
                        <span
                          className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded ${
                            fact.fact_type === 'Material'
                              ? 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                              : 'bg-slate-800 text-slate-400'
                          }`}
                        >
                          {fact.fact_type || 'FACT'}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-slate-200 leading-relaxed font-serif">{fact.description}</p>
                        {fact.source_id && (
                          <button
                            type="button"
                            onClick={() => onViewSource(fact.source_id)}
                            className="mt-2 text-xs text-blue-400 hover:underline flex items-center gap-1"
                          >
                            <FileText size={12} /> Inspect Source Evidence
                          </button>
                        )}
                      </div>
                    </div>
                  ))}

                  {(!caseData.facts || caseData.facts.length === 0) && (
                    <div className="text-center py-12 text-slate-500 text-sm">
                      No material facts extracted for this authority.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Legal Issues */}
            {activeTab === 'Issues' && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Substantive Legal Questions Framed ({caseData.issues?.length || 0})
                </h3>

                <div className="space-y-3">
                  {caseData.issues?.map((issue: any, i: number) => (
                    <div
                      key={i}
                      className="p-4 rounded-lg bg-slate-900/40 border border-slate-800 flex gap-3 items-start"
                    >
                      <span className="font-mono text-xs font-bold text-blue-400 mt-0.5">Q{i + 1}.</span>
                      <p className="text-sm text-slate-200 leading-relaxed font-serif">{issue.issue_text}</p>
                    </div>
                  ))}

                  {(!caseData.issues || caseData.issues.length === 0) && (
                    <div className="text-center py-12 text-slate-500 text-sm">
                      No legal issues mapped for this authority.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Arguments */}
            {activeTab === 'Arguments' && (
              <div className="space-y-6">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Submissions & Party Arguments
                </h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Petitioner / Appellant */}
                  <div className="space-y-3">
                    <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
                        Petitioner / Appellant
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {caseData.arguments?.Petitioner?.length || 0} Submissions
                      </span>
                    </div>

                    {caseData.arguments?.Petitioner?.map((arg: any, i: number) => (
                      <div
                        key={i}
                        className="text-xs text-slate-300 p-3.5 bg-slate-900/40 rounded-lg border border-slate-800/80 border-l-2 border-l-blue-500 leading-relaxed font-serif"
                      >
                        {arg.argument_text}
                      </div>
                    ))}

                    {(!caseData.arguments?.Petitioner || caseData.arguments.Petitioner.length === 0) && (
                      <p className="text-slate-500 text-xs italic py-4">No petitioner submissions extracted.</p>
                    )}
                  </div>

                  {/* Respondent */}
                  <div className="space-y-3">
                    <div className="pb-2 border-b border-slate-800 flex items-center justify-between">
                      <span className="text-xs font-bold uppercase tracking-wider text-rose-400">
                        Respondent / State
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">
                        {caseData.arguments?.Respondent?.length || 0} Submissions
                      </span>
                    </div>

                    {caseData.arguments?.Respondent?.map((arg: any, i: number) => (
                      <div
                        key={i}
                        className="text-xs text-slate-300 p-3.5 bg-slate-900/40 rounded-lg border border-slate-800/80 border-l-2 border-l-rose-500 leading-relaxed font-serif"
                      >
                        {arg.argument_text}
                      </div>
                    ))}

                    {(!caseData.arguments?.Respondent || caseData.arguments.Respondent.length === 0) && (
                      <p className="text-slate-500 text-xs italic py-4">No respondent submissions extracted.</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Court Reasoning */}
            {activeTab === 'Reasoning' && (
              <div className="space-y-4">
                <div className="p-6 rounded-xl bg-slate-900/40 border border-slate-800">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-4 flex items-center gap-2">
                    <BookOpen size={14} /> Judicial Reasoning & Ratio Decidendi
                  </h3>
                  {caseData.court_reasoning ? (
                    <div className="text-sm leading-relaxed text-slate-200 font-serif">
                      <SafeMarkdown content={caseData.court_reasoning} />
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm italic">
                      Detailed judicial reasoning not yet parsed for this case.
                    </p>
                  )}
                </div>
              </div>
            )}

            {/* Legal Principles */}
            {activeTab === 'Principles' && (
              <div className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400">
                  Authoritative Legal Principles ({caseData.principles?.length || 0})
                </h3>

                <div className="space-y-3">
                  {caseData.principles?.map((principle: any, i: number) => (
                    <div
                      key={i}
                      className="p-4 rounded-lg bg-slate-900/40 border border-slate-800 border-l-2 border-l-purple-500"
                    >
                      <div className="text-sm text-purple-200 font-medium mb-1.5 font-serif">
                        {principle.description}
                      </div>
                      {principle.source_passage && (
                        <div className="text-xs text-slate-400 bg-slate-950/60 p-2.5 rounded border border-slate-800/60 italic font-serif">
                          "{principle.source_passage}"
                        </div>
                      )}
                    </div>
                  ))}

                  {(!caseData.principles || caseData.principles.length === 0) && (
                    <div className="text-center py-12 text-slate-500 text-sm">
                      No legal principles recorded for this case.
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Outcome / Disposition */}
            {activeTab === 'Outcome' && (
              <div className="space-y-4">
                <div className="bg-emerald-950/20 border border-emerald-900/40 p-6 rounded-xl shadow-lg">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-emerald-400 mb-3 flex items-center gap-2">
                    <CheckCircle2 size={16} /> Final Judicial Disposition & Remedy
                  </h3>
                  {caseData.decision ? (
                    <p className="text-sm text-emerald-100/90 leading-relaxed font-serif">
                      {caseData.decision}
                    </p>
                  ) : (
                    <p className="text-slate-500 text-sm italic">
                      Final order or disposition not explicitly extracted.
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CaseIntelligence;
