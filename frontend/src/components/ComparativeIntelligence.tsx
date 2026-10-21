import { useState } from 'react';
import { Scale, AlertCircle, FileText, X } from 'lucide-react';
import { motion } from 'framer-motion';
import SafeMarkdown from './common/SafeMarkdown';

interface ComparativeIntelligenceProps {
  comparisonData: any;
  onViewSource: (sourceId: string | null) => void;
  onClose: () => void;
}

export const ComparativeIntelligence: React.FC<ComparativeIntelligenceProps> = ({
  comparisonData,
  onViewSource,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState('Executive');
  const tabs = ['Executive', 'Facts', 'Issues', 'Reasoning', 'Principles', 'Outcome', 'Tensions'];

  if (!comparisonData || !comparisonData.cases || comparisonData.cases.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full p-8 text-slate-500 bg-[#080c14]">
        <Scale size={36} className="mb-3 text-slate-600" />
        <p className="text-sm">Select at least 2 saved cases to generate a comparative analysis.</p>
      </div>
    );
  }

  const cases = comparisonData.cases;

  const renderClaims = (claims: any[], title: string, emptyMessage: string) => {
    if (!claims || claims.length === 0) {
      return <p className="text-slate-500 text-xs italic py-3">{emptyMessage}</p>;
    }

    return (
      <div className="space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-2">{title}</h3>
        {claims.map((claim, idx) => (
          <div
            key={idx}
            className="p-4 bg-slate-900/60 rounded-xl border border-slate-800/80 flex gap-3.5 items-start"
          >
            <span className="text-blue-400 font-bold mt-0.5">•</span>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-slate-200 leading-relaxed font-serif">{claim.claim}</p>
              {claim.sources && claim.sources.length > 0 && (
                <div className="mt-2.5 flex gap-1.5 flex-wrap">
                  {claim.sources.map((s: string) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => onViewSource(s)}
                      className="text-[10px] bg-slate-800 hover:bg-slate-750 text-slate-300 hover:text-white px-2 py-0.5 rounded border border-slate-700/60 transition-colors flex items-center gap-1 font-mono"
                    >
                      <FileText size={10} />
                      <span>{s.replace('case_', 'Case ')}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex flex-col h-full bg-[#080c14] border-l border-slate-800/80 overflow-hidden font-sans">
      {/* Header */}
      <div className="p-6 border-b border-slate-800/80 bg-slate-950/60">
        <div className="flex justify-between items-start mb-3">
          <div>
            <div className="flex items-center gap-2 mb-1 text-xs font-bold uppercase tracking-widest text-blue-400">
              <Scale size={14} />
              <span>Comparative Legal Matrix</span>
            </div>
            <h2 className="text-xl font-serif font-bold text-white">
              Comparative Analysis across {cases.length} Authorities
            </h2>
            <div className="text-[10px] text-amber-300/90 bg-amber-500/10 border border-amber-500/20 px-2.5 py-1 rounded-md mt-2 inline-flex items-center gap-1.5">
              <AlertCircle size={12} className="shrink-0 text-amber-400" />
              <span>
                Controlled Pilot: Distinctions and tensions reflect factual or statutory context; verify before relying in pleadings.
              </span>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
            title="Close Comparison"
          >
            <X size={18} />
          </button>
        </div>

        {/* Selected Cases Header Grid */}
        <div className="flex gap-3 mt-4 overflow-x-auto pb-2 custom-scrollbar">
          {cases.map((c: any) => (
            <div
              key={c.id}
              className="min-w-[220px] flex-1 p-3 bg-slate-900/60 rounded-xl border border-slate-800/80"
            >
              <div className="font-semibold text-xs text-slate-200 truncate" title={c.case_name}>
                {c.case_name}
              </div>
              <div className="text-[10px] text-slate-500 mt-0.5">
                {c.court || 'Supreme Court'} •{' '}
                {c.decision_date ? new Date(c.decision_date).getFullYear() : c.year || 'N/A'}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-800/80 px-4 bg-slate-950/40 overflow-x-auto hide-scrollbar">
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
            {tab}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-y-auto p-6 bg-[#080c14] custom-scrollbar">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.15 }}
          className="max-w-4xl mx-auto space-y-6"
        >
          {activeTab === 'Executive' && (
            <div className="space-y-6">
              <div className="bg-slate-900/60 p-6 rounded-2xl border border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-widest text-blue-400 mb-3">
                  Comparative Synthesis
                </h3>
                <div className="text-xs text-slate-200 leading-relaxed font-serif">
                  <SafeMarkdown content={comparisonData.executive_comparison || 'No summary available.'} />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {renderClaims(
                  comparisonData.similarities,
                  'Material Similarities',
                  'No significant doctrinal similarities detected.'
                )}
                {renderClaims(
                  comparisonData.differences,
                  'Material Differences',
                  'No significant doctrinal differences detected.'
                )}
              </div>
            </div>
          )}

          {activeTab === 'Facts' && (
            <div className="space-y-6">
              {renderClaims(
                comparisonData.distinguishing_factors,
                'Distinguishing Factual Factors',
                'No distinguishing facts flagged across cases.'
              )}

              <div className="mt-6">
                <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">
                  Cross-Case Fact Matrix
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {cases.map((c: any) => (
                    <div
                      key={c.id}
                      className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl space-y-2"
                    >
                      <h4 className="text-xs font-semibold text-blue-400 truncate">{c.case_name}</h4>
                      {c.facts && c.facts.length > 0 ? (
                        <ul className="space-y-2 text-xs text-slate-300 font-serif leading-relaxed">
                          {c.facts.slice(0, 4).map((f: any, i: number) => (
                            <li key={i} className="flex items-start gap-1.5">
                              <span className="text-slate-500 font-mono">•</span>
                              <span>
                                <strong className="text-slate-400 font-sans font-semibold text-[10px] uppercase mr-1">
                                  {f.fact_type}:
                                </strong>
                                {f.description}
                              </span>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-slate-500 italic">No facts extracted in record.</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'Issues' && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-400 mb-3">
                Legal Issues Comparison Matrix
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {cases.map((c: any) => (
                  <div
                    key={c.id}
                    className="bg-slate-900/40 border border-slate-800/80 p-4 rounded-xl space-y-2"
                  >
                    <h4 className="text-xs font-semibold text-blue-400 truncate">{c.case_name}</h4>
                    {c.issues && c.issues.length > 0 ? (
                      <ul className="space-y-2">
                        {c.issues.map((issue: any, idx: number) => (
                          <li
                            key={idx}
                            className="text-xs text-slate-200 font-serif leading-relaxed flex items-start gap-2"
                          >
                            <span className="text-blue-400 font-mono font-bold">{idx + 1}.</span>
                            <span>{issue.issue_text}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-xs text-slate-500 italic">No legal issues mapped in record.</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'Reasoning' && (
            <div className="space-y-6">
              {renderClaims(
                comparisonData.reasoning_comparison,
                'Comparative Judicial Reasoning',
                'No comparative reasoning extracted.'
              )}
            </div>
          )}

          {activeTab === 'Principles' && (
            <div className="space-y-6">
              {renderClaims(
                comparisonData.principle_comparison,
                'Legal Principle Comparison',
                'No principle comparison recorded.'
              )}
            </div>
          )}

          {activeTab === 'Outcome' && (
            <div className="space-y-6">
              {renderClaims(
                comparisonData.outcome_comparison,
                'Comparative Disposition & Outcome',
                'No outcome comparison available.'
              )}
            </div>
          )}

          {activeTab === 'Tensions' && (
            <div className="space-y-4">
              <div className="bg-amber-500/10 border border-amber-500/30 p-5 rounded-2xl">
                <h3 className="text-xs font-bold uppercase tracking-widest text-amber-400 mb-1.5 flex items-center gap-2">
                  <AlertCircle size={15} />
                  <span>Doctrinal Tension & Conflict Analysis</span>
                </h3>
                <p className="text-xs text-amber-200/80 font-serif leading-relaxed">
                  LEXORA distinguishes direct judicial overruling from distinguishing based on distinct facts, procedural postures, or legislative amendments. Tensions should be checked for subsequent Constitution Bench clarification.
                </p>
              </div>

              {renderClaims(
                comparisonData.potential_tensions,
                'Potential Doctrinal Tensions & Distinctions',
                'No significant unresolved tensions or direct conflicts identified among selected authorities.'
              )}
            </div>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default ComparativeIntelligence;
