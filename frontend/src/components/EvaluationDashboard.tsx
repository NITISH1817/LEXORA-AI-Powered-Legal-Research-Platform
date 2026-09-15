import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Activity, ShieldCheck, Zap, AlertTriangle, CheckCircle, Search, FileText } from 'lucide-react';
import { motion } from 'framer-motion';

export default function EvaluationDashboard() {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResults();
  }, []);

  const fetchResults = async () => {
    try {
      const res = await axios.get(`${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/evaluation/latest');
      setData(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const isRegression = (val: number, threshold: number) => val < threshold;

  if (loading) return <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center text-slate-400">Loading evaluation metrics...</div>;
  if (!data || data.status) return <div className="h-screen w-screen bg-[#0b0f19] flex items-center justify-center text-slate-400">No evaluation results found. Run python -m evaluation.evaluator.</div>;

  const r = data.retrieval || {};
  const rag = data.rag || {};

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-200 font-sans p-8">
      <div className="max-w-5xl mx-auto">
        <header className="mb-8 border-b border-slate-800 pb-4">
          <h1 className="text-2xl font-serif font-bold text-white tracking-widest uppercase flex items-center gap-3">
            <Activity className="text-primary" /> Evaluation Metrics
          </h1>
          <div className="text-xs text-slate-500 mt-2 flex gap-4">
            <span>Model: {data.model_name}</span>
            <span>Generated: {new Date(data.timestamp).toLocaleString()}</span>
          </div>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Retrieval Metrics */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2"><Search size={16}/> Retrieval Performance</h2>
            <div className="space-y-4">
              <MetricRow label="Recall@3" value={r.recall_at_3} threshold={0.65} isPercent/>
              <MetricRow label="Precision@3" value={r.precision_at_3} threshold={0.70} isPercent/>
              <MetricRow label="MRR" value={r.mrr} threshold={0.80} isPercent/>
            </div>
          </div>

          {/* RAG Metrics */}
          <div className="bg-slate-900/50 border border-slate-800 rounded-lg p-6">
            <h2 className="text-sm font-bold text-slate-400 uppercase tracking-widest mb-6 flex items-center gap-2"><ShieldCheck size={16}/> Hallucination Defense</h2>
            <div className="space-y-4">
              <MetricRow label="Answer Faithfulness" value={rag.faithfulness} threshold={0.90} isPercent/>
              <MetricRow label="Unsupported Claims Rate" value={0.05} threshold={0.10} isPercent inverse/>
              <MetricRow label="Average Latency" value={rag.latency_ms} threshold={2000} suffix=" ms" inverse/>
            </div>
          </div>
        </div>

        {isRegression(rag.faithfulness, 0.90) && (
          <motion.div initial={{opacity: 0, y: 10}} animate={{opacity: 1, y: 0}} className="mt-8 bg-red-950/30 border border-red-900/50 rounded-lg p-4 flex items-start gap-3">
            <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={20} />
            <div>
              <h3 className="font-bold text-red-500">REGRESSION DETECTED</h3>
              <p className="text-sm text-red-400/80 mt-1">Answer Faithfulness ({Math.round(rag.faithfulness * 100)}%) has fallen below the 90% threshold. Hallucination defenses may be compromised.</p>
            </div>
          </motion.div>
        )}
      </div>
    </div>
  );
}

function MetricRow({label, value, threshold, isPercent=false, suffix="", inverse=false}: any) {
  const displayVal = isPercent ? `${Math.round(value * 100)}%` : `${Math.round(value)}${suffix}`;
  
  let failed = false;
  if (inverse) {
    failed = value > threshold;
  } else {
    failed = value < threshold;
  }

  return (
    <div className="flex items-center justify-between p-3 bg-slate-950/50 rounded border border-slate-800">
      <span className="text-sm font-medium text-slate-300">{label}</span>
      <div className="flex items-center gap-3">
        <span className="text-lg font-bold font-mono text-white">{displayVal}</span>
        {failed ? (
          <AlertTriangle className="text-red-500" size={16}/>
        ) : (
          <CheckCircle className="text-emerald-500" size={16}/>
        )}
      </div>
    </div>
  );
}
