import React, { useState } from 'react';
import { Scale, CheckCircle2, AlertCircle, FileText, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface ComparativeIntelligenceProps {
  comparisonData: any;
  onViewSource: (sourceId: string | null) => void;
  onClose: () => void;
}

const ComparativeIntelligence: React.FC<ComparativeIntelligenceProps> = ({ comparisonData, onViewSource, onClose }) => {
  const [activeTab, setActiveTab] = useState('Executive');
  const tabs = ['Executive', 'Facts', 'Issues', 'Reasoning', 'Principles', 'Outcome', 'Tensions'];

  if (!comparisonData || !comparisonData.cases) return null;
  const cases = comparisonData.cases;

  const renderClaims = (claims: any[], title: string, emptyMessage: string) => {
    if (!claims || claims.length === 0) return <p className="text-slate-500 text-sm italic">{emptyMessage}</p>;
    return (
      <div className="space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">{title}</h3>
        {claims.map((claim, idx) => (
          <div key={idx} className="p-4 bg-slate-900/50 rounded-lg border border-slate-800 flex gap-4 items-start">
             <div className="text-primary mt-1">•</div>
             <div className="flex-1">
               <p className="text-sm text-slate-200">{claim.claim}</p>
               {claim.sources && claim.sources.length > 0 && (
                 <div className="mt-3 flex gap-2 flex-wrap">
                   {claim.sources.map((s: string) => (
                     <button key={s} onClick={() => onViewSource(s)} className="text-[10px] bg-slate-800 hover:bg-primary/20 text-slate-300 hover:text-primary px-2 py-1 rounded border border-slate-700 transition-colors flex items-center gap-1">
                       <FileText size={10}/> Source: {s.replace('case_', 'Case ')}
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
    <div className="flex flex-col h-full bg-background border-l border-border/50">
      {/* Header */}
      <div className="p-6 border-b border-border/50 bg-slate-900/30">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
              <Scale size={20} className="text-primary"/> Comparative Intelligence
            </h2>
            <div className="text-xs text-slate-400 mt-1">{cases.length} authorities selected</div>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors">
            <X size={18} />
          </button>
        </div>
        
        {/* Cases Matrix Header */}
        <div className="flex gap-4 mt-6 overflow-x-auto pb-2 custom-scrollbar">
          {cases.map((c: any) => (
            <div key={c.id} className="min-w-[250px] flex-1 p-4 bg-slate-800/30 rounded border border-slate-700">
               <div className="font-bold text-sm text-slate-200 truncate" title={c.case_name}>{c.case_name}</div>
               <div className="text-xs text-slate-500 mt-1">{c.court} • {c.decision_date ? new Date(c.decision_date).getFullYear() : 'N/A'}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border/50 px-4 pt-4 bg-surface/10 overflow-x-auto hide-scrollbar">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${activeTab === tab ? 'border-primary text-primary' : 'border-transparent text-textMuted hover:text-slate-300'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6 bg-[#0b0f19]">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="max-w-5xl mx-auto space-y-8"
        >
          {activeTab === 'Executive' && (
            <div className="space-y-8">
              <div className="bg-slate-900/50 p-6 rounded-lg border border-slate-800">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-3">Executive Summary</h3>
                <p className="text-sm text-slate-200 leading-relaxed font-serif">
                  {comparisonData.executive_comparison || "No summary available."}
                </p>
              </div>
              <div className="grid grid-cols-2 gap-6">
                {renderClaims(comparisonData.similarities, "Key Similarities", "No significant similarities detected.")}
                {renderClaims(comparisonData.differences, "Key Differences", "No significant differences detected.")}
              </div>
            </div>
          )}

          {activeTab === 'Facts' && (
             <div className="space-y-8">
               {renderClaims(comparisonData.distinguishing_factors, "Distinguishing Factual Factors", "No distinguishing facts detected.")}
               
               <div className="mt-8">
                 <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">Raw Fact Matrix</h3>
                 <div className="flex gap-4 overflow-x-auto">
                   {cases.map((c: any) => (
                     <div key={c.id} className="min-w-[300px] flex-1 bg-slate-900/30 border border-slate-800 p-4 rounded">
                       <h4 className="text-xs font-bold text-slate-400 mb-3">{c.case_name}</h4>
                       <ul className="space-y-3">
                         {c.facts?.slice(0, 5).map((f: any, i: number) => (
                           <li key={i} className="text-xs text-slate-300 leading-relaxed">
                             <span className="text-primary font-bold mr-2">{f.fact_type}:</span>{f.description}
                           </li>
                         ))}
                       </ul>
                     </div>
                   ))}
                 </div>
               </div>
             </div>
          )}

          {activeTab === 'Issues' && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">Legal Issue Matrix</h3>
              <div className="flex gap-4 overflow-x-auto">
                 {cases.map((c: any) => (
                   <div key={c.id} className="min-w-[300px] flex-1 bg-slate-900/30 border border-slate-800 p-4 rounded">
                     <h4 className="text-xs font-bold text-slate-400 mb-3">{c.case_name}</h4>
                     <ul className="space-y-3">
                       {c.issues?.map((i: any, idx: number) => (
                         <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                           <span className="text-primary mt-1">•</span> {i.issue_text}
                         </li>
                       ))}
                     </ul>
                   </div>
                 ))}
              </div>
            </div>
          )}

          {activeTab === 'Reasoning' && (
            <div className="space-y-8">
              {renderClaims(comparisonData.reasoning_comparison, "Comparative Reasoning", "No reasoning comparison available.")}
            </div>
          )}
          
          {activeTab === 'Principles' && (
            <div className="space-y-8">
              {renderClaims(comparisonData.principle_comparison, "Legal Principle Comparison", "No principle comparison available.")}
            </div>
          )}
          
          {activeTab === 'Outcome' && (
            <div className="space-y-8">
              {renderClaims(comparisonData.outcome_comparison, "Outcome Analysis", "No outcome comparison available.")}
            </div>
          )}

          {activeTab === 'Tensions' && (
            <div className="space-y-6">
              <div className="bg-amber-950/20 border border-amber-900/50 p-6 rounded-lg mb-6">
                <h3 className="text-xs font-bold uppercase tracking-widest text-amber-500 mb-2 flex items-center gap-2">
                  <AlertCircle size={14}/> Tension Detection
                </h3>
                <p className="text-sm text-amber-200/70">
                  Lexora highlights areas where courts applied different tests or reached diverging conclusions on similar facts. These are potential areas of legal conflict or distinction.
                </p>
              </div>
              {renderClaims(comparisonData.potential_tensions, "Potential Legal Tensions", "No significant tensions detected among the selected authorities.")}
            </div>
          )}

        </motion.div>
      </div>
    </div>
  );
}

export default ComparativeIntelligence;
