import React, { useState } from 'react';
import { 
  Calendar, Clock, FileText, Briefcase, CheckCircle2, 
  AlertTriangle, AlertCircle, HelpCircle, ShieldAlert, X 
} from 'lucide-react';

interface CaseTimelineProps {
  timelineData: any;
  onViewSource: (eventData: any) => void;
}

const CaseTimeline: React.FC<CaseTimelineProps> = ({ timelineData, onViewSource }) => {
  const [activeTab, setActiveTab] = useState<'ALL' | 'FACTUAL' | 'PROCEDURAL'>('ALL');
  const [inspectEvent, setInspectEvent] = useState<any | null>(null);

  const rawEvents: any[] = timelineData?.events || timelineData?.timeline || timelineData?.timeline_events || [];
  
  if (!rawEvents || rawEvents.length === 0) {
    return (
      <div className="p-12 text-center text-slate-500 bg-[#0b0f19] h-full flex flex-col items-center justify-center">
        <Clock size={36} className="text-slate-700 mb-3" />
        <h3 className="text-base font-semibold text-slate-300">No Timeline Data Available</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-sm">
          No factual or procedural timeline events have been indexed or extracted for this case record yet.
        </p>
      </div>
    );
  }

  // Filter by category tab
  let filtered = rawEvents;
  if (activeTab === 'FACTUAL') {
    filtered = timelineData?.factual_events || rawEvents.filter((e: any) => e.timeline_type === 'FACTUAL');
  } else if (activeTab === 'PROCEDURAL') {
    filtered = timelineData?.procedural_events || rawEvents.filter((e: any) => e.timeline_type === 'PROCEDURAL');
  }

  // Partition dated events vs. undated/relative events
  const datedEvents = filtered.filter((e: any) => {
    const prec = (e.date_precision || '').toLowerCase();
    return prec !== 'unknown' && (e.event_date || /\b(19\d\d|20\d\d)\b/.test(e.date_text || ''));
  });

  const undatedEvents = filtered.filter((e: any) => {
    const prec = (e.date_precision || '').toLowerCase();
    return prec === 'unknown' || (!e.event_date && !/\b(19\d\d|20\d\d)\b/.test(e.date_text || ''));
  });

  const handleInspect = (event: any) => {
    setInspectEvent(event);
    if (onViewSource) {
      onViewSource(event);
    }
  };

  const renderEventCard = (event: any, index: number, isUndated: boolean = false) => {
    const isFactual = event.timeline_type === 'FACTUAL';
    const precision = (event.date_precision || 'unknown').toLowerCase();
    const isExact = precision === 'exact';
    const isApproximate = precision === 'approximate';
    const isRange = precision === 'range';
    const isUnknown = precision === 'unknown';

    const isAllegation = event.is_allegation || 
      event.attribution_status === 'ALLEGATION' || 
      event.attribution_status === 'DISPUTED';

    return (
      <div key={event.id || index} className="relative flex gap-6 pb-10 group">
        {/* Connecting Line (only for dated chronological stream) */}
        {!isUndated && (
          <div className="absolute top-8 left-[19px] bottom-[-20px] w-0.5 bg-slate-800 group-last:bg-transparent"></div>
        )}

        {/* Node Icon */}
        <div className={`relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2 ${
          isUndated 
            ? 'bg-slate-900 border-slate-700 text-slate-400'
            : isFactual 
              ? 'bg-amber-950/40 border-amber-800/60 text-amber-500' 
              : 'bg-blue-950/40 border-blue-800/60 text-blue-500'
        }`}>
          {isUndated ? <HelpCircle size={16} /> : isFactual ? <Briefcase size={16} /> : <Calendar size={16} />}
        </div>

        {/* Event Card Content */}
        <div className="flex-1 bg-slate-900/40 border border-slate-800 rounded-lg p-5 hover:border-slate-700 transition-colors shadow-lg relative overflow-hidden">
          {/* Color accent strip */}
          <div className={`absolute top-0 left-0 w-1 h-full ${
            isUndated ? 'bg-slate-600' : isFactual ? 'bg-amber-500' : 'bg-blue-500'
          }`}></div>

          <div className="flex justify-between items-start gap-4 mb-3">
            <div>
              {/* Date & Precision Badges */}
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <span className="text-base font-bold text-slate-200">
                  {event.date_text || (event.event_date ? event.event_date : "Undated Event")}
                </span>

                {isExact && (
                  <span className="text-[10px] bg-emerald-950/40 text-emerald-400 px-2 py-0.5 rounded border border-emerald-900/50 flex items-center gap-1">
                    <CheckCircle2 size={10} /> Exact Date
                  </span>
                )}
                {isApproximate && (
                  <span className="text-[10px] bg-amber-950/40 text-amber-400 px-2 py-0.5 rounded border border-amber-900/50 flex items-center gap-1">
                    <AlertTriangle size={10} /> Approximate
                  </span>
                )}
                {isRange && (
                  <span className="text-[10px] bg-purple-950/40 text-purple-400 px-2 py-0.5 rounded border border-purple-900/50 flex items-center gap-1">
                    <Clock size={10} /> Date Range
                  </span>
                )}
                {isUnknown && (
                  <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded border border-slate-700 flex items-center gap-1">
                    <HelpCircle size={10} /> Date Unknown / Relative
                  </span>
                )}

                {/* Allegation Tag */}
                {isAllegation && (
                  <span className="text-[10px] bg-rose-950/40 text-rose-400 px-2 py-0.5 rounded border border-rose-900/50 flex items-center gap-1">
                    <ShieldAlert size={10} /> Allegation / Submission
                  </span>
                )}
              </div>

              <h3 className="text-sm font-semibold text-slate-300">{event.title}</h3>
            </div>

            <span className={`text-[9px] uppercase tracking-wider font-bold shrink-0 ${
              isFactual ? 'text-amber-500' : 'text-blue-500'
            }`}>
              {event.timeline_type} • {event.event_type}
            </span>
          </div>

          <p className="text-sm text-slate-400 leading-relaxed font-serif mb-4">
            {event.description}
          </p>

          {/* Actors & Court Metadata */}
          <div className="flex flex-wrap gap-2 mb-4">
            {event.actors && (
              <div className="text-xs bg-slate-950 px-2.5 py-1 rounded text-slate-400 border border-slate-800 flex items-center gap-1">
                <span className="font-semibold text-slate-500 text-[10px]">ACTORS:</span>
                <span>{typeof event.actors === 'string' ? event.actors.replace(/[\]["]/g, '') : JSON.stringify(event.actors)}</span>
              </div>
            )}
            {event.court && (
              <div className="text-xs bg-slate-950 px-2.5 py-1 rounded text-slate-400 border border-slate-800 flex items-center gap-1">
                <span className="font-semibold text-slate-500 text-[10px]">FORUM:</span> {event.court}
              </div>
            )}
            {event.verification_status && (
              <div className="text-[10px] bg-slate-950 px-2 py-1 rounded text-slate-500 border border-slate-800">
                STATUS: <span className="text-slate-300 uppercase">{event.verification_status}</span>
              </div>
            )}
          </div>

          {/* Footer with Source Provenance */}
          <div className="pt-3 border-t border-slate-800/60 flex justify-between items-center text-xs">
            <div className="flex items-center gap-2 text-[11px] text-slate-500">
              <CheckCircle2 size={12} className="text-emerald-500" />
              Source Grounded • Page {event.page_number || 'N/A'}
            </div>
            <button
              onClick={() => handleInspect(event)}
              className="flex items-center gap-1 text-slate-300 hover:text-primary transition-colors bg-slate-800 hover:bg-slate-750 px-3 py-1.5 rounded border border-slate-700"
            >
              <FileText size={13} /> View Evidence
            </button>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0f19] relative">
      {/* Header */}
      <div className="p-6 border-b border-slate-800/50 bg-slate-900/30">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2 mb-1.5">
          <Clock size={20} className="text-primary" /> Case Timeline Intelligence
        </h2>
        <p className="text-xs text-slate-400">
          Source-grounded factual and procedural history with explicit date precision and verification metadata.
        </p>

        {/* Category Filter Tabs */}
        <div className="flex gap-2 mt-5">
          <button
            onClick={() => setActiveTab('ALL')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors border ${
              activeTab === 'ALL'
                ? 'bg-primary/20 text-primary border-primary/30'
                : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800'
            }`}
          >
            All Events ({rawEvents.length})
          </button>
          <button
            onClick={() => setActiveTab('FACTUAL')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors border ${
              activeTab === 'FACTUAL'
                ? 'bg-amber-500/20 text-amber-500 border-amber-500/30'
                : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800'
            }`}
          >
            Factual Timeline ({rawEvents.filter((e: any) => e.timeline_type === 'FACTUAL').length})
          </button>
          <button
            onClick={() => setActiveTab('PROCEDURAL')}
            className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors border ${
              activeTab === 'PROCEDURAL'
                ? 'bg-blue-500/20 text-blue-500 border-blue-500/30'
                : 'bg-slate-800/50 text-slate-400 border-slate-700 hover:bg-slate-800'
            }`}
          >
            Procedural History ({rawEvents.filter((e: any) => e.timeline_type === 'PROCEDURAL').length})
          </button>
        </div>
      </div>

      {/* Main Timeline Scrollable Content */}
      <div className="flex-1 overflow-auto p-6 md:p-8 custom-scrollbar">
        <div className="max-w-3xl mx-auto space-y-8">
          
          {/* Grounding and Date Precision Notice */}
          <div className="p-4 bg-slate-900/60 border border-slate-800 rounded-lg flex gap-3 text-xs text-slate-400">
            <AlertCircle size={18} className="text-primary shrink-0 mt-0.5" />
            <div>
              <strong className="text-slate-200">Date Precision Safeguards</strong>
              <p className="mt-0.5 leading-relaxed">
                Dates are strictly extracted from source text. Approximate expressions (e.g. <em>"around March 2020"</em>) and relative references are not fabricated into exact calendar days.
              </p>
            </div>
          </div>

          {/* Section 1: Chronological Sequence (Dated Events) */}
          {datedEvents.length > 0 && (
            <div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-6 flex items-center gap-2">
                <Calendar size={14} className="text-primary" /> Chronologically Verified Events ({datedEvents.length})
              </h3>
              <div>
                {datedEvents.map((event: any, i: number) => renderEventCard(event, i, false))}
              </div>
            </div>
          )}

          {/* Section 2: Undated & Relative Events (Partitioned to prevent false chronology) */}
          {undatedEvents.length > 0 && (
            <div className="pt-6 border-t border-slate-800">
              <div className="mb-6">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
                  <HelpCircle size={14} className="text-slate-500" /> Undated & Relative Sequence Events ({undatedEvents.length})
                </h3>
                <p className="text-[11px] text-slate-500 mt-1">
                  These events are documented in the record with approximate relative sequence (e.g., <em>"subsequently"</em>, <em>"several years later"</em>) and are not placed on a verified calendar day.
                </p>
              </div>
              <div>
                {undatedEvents.map((event: any, i: number) => renderEventCard(event, i, true))}
              </div>
            </div>
          )}

          {filtered.length === 0 && (
            <div className="text-center text-slate-500 py-12 text-sm font-serif">
              No events found for this filter category.
            </div>
          )}
        </div>
      </div>

      {/* Source Passage Evidence Inspection Modal */}
      {inspectEvent && (
        <div className="fixed inset-0 z-50 bg-black/75 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-xl max-w-xl w-full p-6 shadow-2xl relative">
            <button
              onClick={() => setInspectEvent(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition-colors"
            >
              <X size={18} />
            </button>

            <div className="flex items-center gap-2 text-primary font-bold text-xs uppercase tracking-wider mb-2">
              <FileText size={16} /> Supporting Passage Evidence
            </div>
            <h3 className="text-lg font-bold text-slate-100 mb-1">{inspectEvent.title}</h3>
            <p className="text-xs text-slate-400 mb-4">{inspectEvent.date_text} • {inspectEvent.timeline_type}</p>

            <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 mb-4">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest block mb-1">Source Excerpt</span>
              <p className="text-sm font-serif text-slate-300 leading-relaxed italic">
                "{inspectEvent.supporting_text || 'No verbatim excerpt recorded for this event.'}"
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs mb-6">
              <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">PAGE NUMBER</span>
                <span className="font-semibold text-slate-300">{inspectEvent.page_number || 'N/A'}</span>
              </div>
              <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">CHUNK ID</span>
                <span className="font-mono text-slate-300 text-[11px] truncate block">{inspectEvent.source_chunk_id || 'N/A'}</span>
              </div>
              <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">DATE PRECISION</span>
                <span className="font-semibold text-slate-300 uppercase">{inspectEvent.date_precision || 'UNKNOWN'}</span>
              </div>
              <div className="bg-slate-950/50 p-2.5 rounded border border-slate-800/80">
                <span className="text-slate-500 block text-[10px]">VERIFICATION</span>
                <span className="font-semibold text-slate-300 uppercase">{inspectEvent.verification_status || 'VERIFIED'}</span>
              </div>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setInspectEvent(null)}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded transition-colors"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CaseTimeline;
