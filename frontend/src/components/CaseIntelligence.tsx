import React, { useState, useEffect } from 'react';
import { Scale, ChevronRight, FileText, CheckCircle2, Bookmark, Share2, Download, AlertCircle, TrendingUp, Filter, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import CaseTimeline from './CaseTimeline';

interface CaseIntelligenceProps {
  caseData: any;
  onViewSource: (sourceId: string) => void;
}

const CaseIntelligence: React.FC<CaseIntelligenceProps> = ({ caseData, onViewSource }) => {
  const [activeTab, setActiveTab] = useState('Executive');
  const tabs = ['Executive', 'Timeline', 'Facts', 'Issues', 'Reasoning', 'Principles', 'Outcome'];

  useEffect(() => {
    setActiveTab('Executive');
  }, [caseData?.id]);

  if (!caseData) return null;

  return (
    <div className="flex flex-col h-full bg-background border-l border-border/50">
      {/* Header */}
      <div className="p-6 md:p-8 border-b border-border/50 bg-slate-900/30">
        <div className="flex justify-between items-start mb-4">
          <div>
            <div className="flex items-center gap-2 mb-2 text-xs font-bold uppercase tracking-widest text-primary">
              <Scale size={14} /> Case Intelligence Profile
            </div>
            <h2 className="text-2xl md:text-3xl font-serif font-bold text-slate-100 leading-tight">
              {caseData.case_name}
            </h2>
            <div className="text-sm text-slate-400 mt-2 flex items-center gap-2">
              <span>{caseData.court}</span>
              <span className="text-slate-600">•</span>
              <span>{caseData.decision_date ? new Date(caseData.decision_date).toLocaleDateString() : 'N/A'}</span>
              {caseData.case_number && (
                <>
                  <span className="text-slate-600">•</span>
                  <span>{caseData.case_number}</span>
                </>
              )}
            </div>
          </div>
          <div className="flex gap-2">
             <button className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"><Bookmark size={16}/></button>
             <button className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"><Share2 size={16}/></button>
             <button className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded transition-colors"><Download size={16}/></button>
          </div>
        </div>
        
        {/* Topics Tags */}
        <div className="flex gap-2 mt-4 flex-wrap">
          {caseData.legal_topics?.split(',').map((topic: string) => (
             <span key={topic} className="px-2.5 py-1 bg-slate-800 text-slate-300 text-[10px] font-bold uppercase tracking-wider rounded border border-slate-700">
               {topic.trim()}
             </span>
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
            {tab === 'Timeline' ? <span className="flex items-center gap-1"><Clock size={14}/> {tab}</span> : tab}
          </button>
        ))}
      </div>

      {/* Content Area */}
      <div className="flex-1 overflow-auto bg-[#0b0f19]">
        
        {activeTab === 'Timeline' && (
           <CaseTimeline timelineData={caseData} onViewSource={(event) => onViewSource(event.source_chunk_id || "document_1")} />
        )}

        {activeTab !== 'Timeline' && (
          <div className="p-6 md:p-8 max-w-4xl mx-auto space-y-12">
            
            {activeTab === 'Executive' && (
              <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
                 <div className="p-6 bg-slate-900/50 rounded-xl border border-slate-800 shadow-xl relative overflow-hidden">
                   <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                   <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-4 flex items-center gap-2"><TrendingUp size={14}/> AI Synthesis</h3>
                   <p className="text-slate-200 text-base leading-relaxed font-serif">
                     {caseData.executive_summary || "No executive summary available."}
                   </p>
                 </div>
                 
                 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                   <div className="p-5 bg-slate-900/30 rounded-lg border border-slate-800">
                     <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Key Issues</h4>
                     <ul className="space-y-2">
                       {caseData.issues?.slice(0,3).map((issue: any, i: number) => (
                         <li key={i} className="text-sm text-slate-300 flex items-start gap-2">
                           <span className="text-primary mt-1">•</span> {issue.issue_text}
                         </li>
                       ))}
                     </ul>
                   </div>
                   <div className="p-5 bg-slate-900/30 rounded-lg border border-slate-800">
                     <h4 className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Final Decision</h4>
                     <p className="text-sm text-slate-300 leading-relaxed">
                       {caseData.decision}
                     </p>
                   </div>
                 </div>
              </motion.div>
            )}

          {activeTab === 'Facts' && (
             <div className="max-w-3xl">
               <div className="space-y-4">
                 {caseData.facts?.map((fact: any, i: number) => (
                    <div key={i} className="flex gap-4 p-4 rounded-lg bg-slate-900/30 border border-slate-800/50 hover:border-primary/30 transition-colors">
                      <div className="w-24 shrink-0">
                         <span className={`text-[10px] font-bold uppercase px-2 py-1 rounded ${fact.fact_type === 'Material' ? 'bg-primary/20 text-primary' : 'bg-slate-800 text-slate-400'}`}>
                           {fact.fact_type}
                         </span>
                      </div>
                      <div className="flex-1">
                        <p className="text-sm text-slate-200">{fact.description}</p>
                        {fact.source_id && (
                          <button onClick={() => onViewSource(fact.source_id)} className="mt-2 text-xs text-primary hover:underline flex items-center gap-1">
                            <FileText size={12}/> View Source
                          </button>
                        )}
                      </div>
                    </div>
                 ))}
                 {(!caseData.facts || caseData.facts.length === 0) && <p className="text-textMuted text-sm">No facts extracted.</p>}
               </div>
             </div>
          )}

          {activeTab === 'Issues' && (
             <div className="max-w-3xl space-y-4">
                {caseData.issues?.map((issue: any, i: number) => (
                   <div key={i} className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/50 flex gap-3">
                     <span className="text-primary font-bold">{i+1}.</span>
                     <p className="text-sm text-slate-200">{issue.issue_text}</p>
                   </div>
                ))}
             </div>
          )}

          {activeTab === 'Arguments' && (
             <div className="max-w-4xl grid grid-cols-2 gap-6">
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-widest text-textMuted mb-4 border-b border-border/50 pb-2">Petitioner / Plaintiff</h3>
                  <div className="space-y-3">
                     {caseData.arguments?.Petitioner?.map((arg: any, i: number) => (
                        <div key={i} className="text-sm text-slate-300 p-3 bg-slate-900/30 rounded border border-slate-800/50 border-l-2 border-l-blue-500">
                          {arg.argument_text}
                        </div>
                     ))}
                  </div>
                </div>
                <div>
                  <h3 className="text-xs font-bold uppercase tracking-widest text-textMuted mb-4 border-b border-border/50 pb-2">Respondent / Defendant</h3>
                  <div className="space-y-3">
                     {caseData.arguments?.Respondent?.map((arg: any, i: number) => (
                        <div key={i} className="text-sm text-slate-300 p-3 bg-slate-900/30 rounded border border-slate-800/50 border-l-2 border-l-rose-500">
                          {arg.argument_text}
                        </div>
                     ))}
                  </div>
                </div>
             </div>
          )}

          {activeTab === 'Reasoning' && (
             <div className="max-w-3xl space-y-6">
               <div className="bg-slate-900/30 p-6 rounded-lg border border-slate-800/50">
                 <h3 className="text-xs font-bold uppercase tracking-widest text-primary mb-4 flex items-center gap-2"><BookOpen size={14}/> Court Reasoning</h3>
                 <div className="text-sm leading-relaxed text-slate-200 whitespace-pre-wrap font-serif">
                   {caseData.court_reasoning || "Reasoning not explicitly extracted."}
                 </div>
               </div>
             </div>
          )}

          {activeTab === 'Decision' && (
             <div className="max-w-3xl">
                <div className="bg-emerald-950/20 border border-emerald-900/50 p-6 rounded-lg">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-emerald-500 mb-4 flex items-center gap-2"><CheckCircle2 size={14}/> Final Decision</h3>
                  <p className="text-sm text-emerald-100">{caseData.decision || "Decision not explicitly extracted."}</p>
                </div>
             </div>
          )}

          {activeTab === 'Principles' && (
             <div className="max-w-3xl space-y-4">
                {caseData.principles?.map((principle: any, i: number) => (
                   <div key={i} className="p-4 rounded-lg bg-slate-900/30 border border-slate-800/50 border-l-2 border-l-purple-500">
                     <div className="text-sm text-purple-100 font-medium mb-2">{principle.description}</div>
                     {principle.source_passage && (
                       <div className="text-xs text-slate-400 bg-black/20 p-2 rounded italic mt-2">
                         "{principle.source_passage}"
                       </div>
                     )}
                   </div>
                ))}
             </div>
          )}

          {activeTab === 'Timeline' && (
             <div className="max-w-2xl relative before:absolute before:inset-0 before:ml-5 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-slate-700 before:to-transparent">
                {caseData.timeline?.map((event: any, i: number) => (
                   <div key={i} className="relative flex items-center justify-between md:justify-normal md:odd:flex-row-reverse group is-active mb-8">
                     <div className="flex items-center justify-center w-10 h-10 rounded-full border border-slate-700 bg-slate-900 text-slate-400 shadow shrink-0 md:order-1 md:group-odd:-translate-x-1/2 md:group-even:translate-x-1/2">
                       <History size={16}/>
                     </div>
                     <div className="w-[calc(100%-4rem)] md:w-[calc(50%-2.5rem)] p-4 rounded-lg border border-slate-700 bg-slate-900/50 shadow">
                        <div className="flex items-center justify-between mb-1">
                          <div className="text-primary font-bold text-xs">{event.event_date}</div>
                        </div>
                        <div className="text-sm text-slate-300">{event.event_description}</div>
                     </div>
                   </div>
                ))}
                {(!caseData.timeline || caseData.timeline.length === 0) && <p className="text-textMuted text-sm ml-12">No timeline events extracted.</p>}
             </div>
          )}

        </motion.div>
      </div>
    </div>
  );
}

export default CaseIntelligence;
