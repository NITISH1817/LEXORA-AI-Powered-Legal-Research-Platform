import React, { useState, useEffect, useRef } from 'react';
import { ZoomIn, ZoomOut, Maximize, AlertCircle } from 'lucide-react';
import { motion } from 'framer-motion';

interface PrecedentGraphProps {
  graphData: any;
  onNodeClick: (nodeId: string) => void;
  onEdgeClick: (edgeId: string) => void;
}

const PrecedentGraph: React.FC<PrecedentGraphProps> = ({ graphData, onNodeClick, onEdgeClick }) => {
  const [scale, setScale] = useState(1);
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes) return;
    
    // Very simple auto-layout for demo purposes (radial layout)
    const centerX = 400;
    const centerY = 300;
    const radius = 200;
    
    const rootNode = graphData.nodes[0]; // Assuming first is root
    const mappedNodes = graphData.nodes.map((node: any, i: number) => {
      if (i === 0) return { ...node, x: centerX, y: centerY };
      
      const angle = (i - 1) * (2 * Math.PI) / (graphData.nodes.length - 1);
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle)
      };
    });
    
    setNodes(mappedNodes);
    setEdges(graphData.edges || []);
  }, [graphData]);

  const getEdgeColor = (relationship: string) => {
    switch(relationship.toUpperCase()) {
      case 'CITES': return '#64748b'; // slate-500
      case 'FOLLOWS': return '#10b981'; // emerald-500
      case 'DISTINGUISHES': return '#f59e0b'; // amber-500
      case 'OVERRULES': return '#ef4444'; // red-500
      default: return '#64748b';
    }
  };

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-4 bg-slate-900/20">
         <AlertCircle size={32} className="opacity-50" />
         <p>No citation network data available.</p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-[#0b0f19] overflow-hidden" ref={containerRef}>
      {/* Controls */}
      <div className="absolute top-4 right-4 z-10 flex flex-col gap-2 bg-slate-900/80 p-2 rounded border border-slate-800 backdrop-blur">
        <button onClick={() => setScale(s => Math.min(s + 0.2, 2))} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white"><ZoomIn size={16}/></button>
        <button onClick={() => setScale(s => Math.max(s - 0.2, 0.4))} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white"><ZoomOut size={16}/></button>
        <button onClick={() => setScale(1)} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white"><Maximize size={16}/></button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-900/80 p-3 rounded border border-slate-800 backdrop-blur text-xs flex gap-4">
        <div className="flex items-center gap-2"><div className="w-3 h-0.5 bg-slate-500"></div> Cites</div>
        <div className="flex items-center gap-2"><div className="w-3 h-0.5 bg-emerald-500"></div> Follows</div>
        <div className="flex items-center gap-2"><div className="w-3 h-0.5 bg-amber-500"></div> Distinguishes</div>
        <div className="flex items-center gap-2"><div className="w-3 h-0.5 bg-red-500"></div> Overrules</div>
      </div>

      {/* SVG Canvas */}
      <div className="w-full h-full cursor-move" style={{ transform: `scale(${scale})`, transformOrigin: 'center center', transition: 'transform 0.2s ease-out' }}>
        <svg width="100%" height="100%" viewBox="0 0 800 600">
          
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map(edge => {
            const source = nodes.find(n => n.id === edge.source);
            const target = nodes.find(n => n.id === edge.target);
            if (!source || !target) return null;
            
            const isUnresolved = target.id.startsWith('unresolved');
            const color = getEdgeColor(edge.relationship);

            return (
              <g key={edge.id} className="cursor-pointer group" onClick={() => onEdgeClick(edge.id)}>
                <line
                  x1={source.x} y1={source.y}
                  x2={target.x} y2={target.y}
                  stroke={color}
                  strokeWidth="2"
                  strokeOpacity="0.6"
                  strokeDasharray={isUnresolved ? "4 4" : "none"}
                  markerEnd="url(#arrowhead)"
                  className="group-hover:stroke-primary group-hover:stroke-opacity-100 transition-all"
                />
                <rect 
                  x={(source.x + target.x)/2 - 30} y={(source.y + target.y)/2 - 10} 
                  width="60" height="20" rx="4" fill="#0f172a" 
                  className="group-hover:fill-slate-800 transition-colors"
                />
                <text 
                  x={(source.x + target.x)/2} y={(source.y + target.y)/2 + 4} 
                  fontSize="8" fill="#94a3b8" textAnchor="middle" 
                  className="group-hover:fill-white font-mono"
                >
                  {edge.relationship}
                </text>
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map(node => {
            const isUnresolved = node.id.startsWith('unresolved');
            return (
              <g key={node.id} className="cursor-pointer group" transform={`translate(${node.x}, ${node.y})`} onClick={() => onNodeClick(node.id)}>
                <rect 
                  x="-75" y="-25" width="150" height="50" rx="6"
                  fill={isUnresolved ? '#1e293b' : '#0f172a'} 
                  stroke={isUnresolved ? '#475569' : '#3b82f6'} 
                  strokeWidth="1.5"
                  className="group-hover:stroke-primary group-hover:fill-slate-800 transition-colors shadow-lg"
                  strokeDasharray={isUnresolved ? "4 4" : "none"}
                />
                <text x="0" y="-5" fontSize="10" fontWeight="bold" fill={isUnresolved ? '#94a3b8' : '#f1f5f9'} textAnchor="middle" className="truncate max-w-[140px]">
                  {node.case_name.length > 20 ? node.case_name.substring(0, 20) + '...' : node.case_name}
                </text>
                <text x="0" y="10" fontSize="8" fill="#64748b" textAnchor="middle">
                  {isUnresolved ? 'Unresolved Authority' : `${node.court || 'Court'} • ${node.year || 'Year'}`}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

export default PrecedentGraph;
