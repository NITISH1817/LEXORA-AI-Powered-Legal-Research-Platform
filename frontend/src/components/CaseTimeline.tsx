import React, { useState } from 'react';
import { Calendar, Clock, FileText, Briefcase, ChevronDown, CheckCircle2, AlertTriangle, AlertCircle } from 'lucide-react';

interface CaseTimelineProps {
  timelineData: any;
  onViewSource: (eventData: any) => void;
}

const CaseTimeline: React.FC<CaseTimelineProps> = ({ timelineData, onViewSource }) => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'FACTUAL' | 'PROCEDURAL'>('ALL');

  if (!timelineData || !timelineData.events) {
    return <div className="p-8 text-center text-slate-500">No timeline data available.</div>;
  }

  let events = timelineData.events;
  if (activeTab === 'FACTUAL') events = timelineData.factual_events;
  if (activeTab === 'PROCEDURAL') events = timelineData.procedural_events;

  const renderEvent = (event: any, index: number) => {
    const isFactual = event.timeline_type === 'FACTUAL';
    const isApproximate = event.date_precision === 'approximate' || event.date_precision === 'range';
    const isUnknown = event.date_precision === 'unknown';

    return (
      <div key={event.id || index} className="relative flex gap-6 pb-12 group">
        {/* Line connector */}
        <div className="absolute top-8 left-[19px] bottom-[-24px] w-0.5 bg-slate-800 group-last:bg-transparent"></div>
        
        {/* Icon */}
        <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2 ${isFactual ? 'bg-amber-950/30 border-amber-900/50 text-amber-500' : 'bg-blue-950/30 border-blue-900/50 text-blue-500'}`}>
          {isFactual ? <Briefcase size={16} /> : <Calendar size={16} />}
        </div>
        
        {/* Content */}
        <div className="flex-1 bg-slate-900/40 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition-colors shadow-lg relative overflow-hidden">
          {/* Label strip */}
          <div className={`absolute top-0 left-0 w-1 h-full ${isFactual ? 'bg-amber-500' : 'bg-blue-500'}`}></div>
          
          <div className="flex justify-between items-start mb-3">
             <div>
               <div className="flex items-center gap-2 mb-1">
                 <span className="text-lg font-bold text-slate-200">{event.date_text}</span>
                 {isApproximate && <span className="text-[10px] bg-amber-950/40 text-amber-500 px-2 py-0.5 rounded border border-amber-900/50 flex items-center gap-1"><AlertTriangle size={10}/> Approximate</span>}
                 {isUnknown && <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700">Unknown Date</span>}
               </div>
               <h3 className="text-sm font-semibold text-slate-300">{event.title}</h3>
             </div>
             <span className={`text-[9px] uppercase tracking-widest font-bold ${isFactual ? 'text-amber-500' : 'text-blue-500'}`}>
               {event.timeline_type} • {event.event_type}
             </span>
          </div>
          
          <p className="text-sm text-slate-400 leading-relaxed font-serif mb-4">
            {event.description}
          </p>
          
          <div className="flex flex-wrap gap-2 mb-4">
            {event.actors && (
              <div className="text-xs bg-slate-950 px-2 py-1 rounded text-slate-400 border border-slate-800/50 flex items-center gap-1">
                <span className="font-bold text-slate-500">ACTORS:</span> {JSON.parse(event.actors).join(', ')}
              </div>
            )}
            {event.court && (
              <div className="text-xs bg-slate-950 px-2 py-1 rounded text-slate-400 border border-slate-800/50 flex items-center gap-1">
                <span className="font-bold text-slate-500">COURT:</span> {event.court}
              </div>
            )}
          </div>
          
          <div className="pt-3 border-t border-slate-800/50 flex justify-between items-center">
             <div className="flex items-center gap-2 text-[10px] text-slate-500">
               <CheckCircle2 size={12} className="text-emerald-500"/>
               AI Extracted • Page {event.page_number || 'N/A'}
             </div>
             <button 
               onClick={() => onViewSource(event)}
               className="text-xs flex items-center gap-1 text-slate-300 hover:text-primary transition-colors bg-slate-800 px-3 py-1.5 rounded border border-slate-700 hover:border-primary/50"
             >
               <FileText size={14}/> View Evidence
             </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0f19]">
      <div className="p-6 border-b border-slate-800/50 bg-slate-900/30">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mb-2">
          <Clock size={20} className="text-primary"/> Case Timeline
        </h2>
        <p className="text-sm text-slate-400">Chronological history of factual events and procedural steps extracted from the judgment.</p>
        
        <div className="flex gap-2 mt-6">
          <button onClick={() => setActiveTab('ALL')} className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors border ${activeTab === 'ALL' ? 'bg-primary/20 text-primary border-primary/30' : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>All Events</button>
          <button onClick={() => setActiveTab('FACTUAL')} className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors border ${activeTab === 'FACTUAL' ? 'bg-amber-500/20 text-amber-500 border-amber-500/30' : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>Factual Timeline</button>
          <button onClick={() => setActiveTab('PROCEDURAL')} className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors border ${activeTab === 'PROCEDURAL' ? 'bg-blue-500/20 text-blue-500 border-blue-500/30' : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800'}`}>Procedural History</button>
        </div>
      </div>
      
      <div className="flex-1 overflow-auto p-8 custom-scrollbar relative">
         <div className="max-w-3xl mx-auto pt-4">
           {/* Timeline warnings */}
           <div className="mb-8 p-4 bg-slate-900/50 border border-slate-800 rounded-lg flex gap-3 text-sm text-slate-400">
              <AlertCircle size={18} className="text-primary shrink-0 mt-0.5" />
              <div>
                <strong>AI-Generated Timeline</strong>
                <p className="mt-1">Events are extracted directly from the indexed document text. Timelines may be incomplete if the document omits dates or specific procedural steps.</p>
              </div>
           </div>
           
           {events.length === 0 ? (
             <div className="text-center text-slate-500 py-12 font-serif">No events found for this category.</div>
           ) : (
             <div className="mt-4">
               {events.map((event: any, i: number) => renderEvent(event, i))}
             </div>
           )}
         </div>
      </div>
    </div>
  );
};

export default CaseTimeline;
