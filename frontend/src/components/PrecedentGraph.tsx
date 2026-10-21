import React, { useState, useEffect, useRef } from 'react';
import { ZoomIn, ZoomOut, Maximize, GitFork } from 'lucide-react';

interface PrecedentGraphProps {
  graphData: any;
  onNodeClick: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  depth?: number;
  onDepthChange?: (newDepth: number) => void;
}

export const PrecedentGraph: React.FC<PrecedentGraphProps> = ({
  graphData,
  onNodeClick,
  onEdgeClick,
  depth = 1,
  onDepthChange,
}) => {
  const [scale, setScale] = useState(1);
  const [nodes, setNodes] = useState<any[]>([]);
  const [edges, setEdges] = useState<any[]>([]);
  const [selectedEdge, setSelectedEdge] = useState<any | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      setNodes([]);
      setEdges([]);
      return;
    }

    // Radial layout with central root node and concentric layers
    const centerX = 400;
    const centerY = 300;
    const radius = Math.min(220, Math.max(140, graphData.nodes.length * 15));

    const mappedNodes = graphData.nodes.map((node: any, i: number) => {
      if (i === 0) return { ...node, x: centerX, y: centerY };

      const angle = ((i - 1) * (2 * Math.PI)) / Math.max(graphData.nodes.length - 1, 1);
      return {
        ...node,
        x: centerX + radius * Math.cos(angle),
        y: centerY + radius * Math.sin(angle),
      };
    });

    setNodes(mappedNodes);
    setEdges(graphData.edges || []);
    setSelectedEdge(null);
  }, [graphData]);

  const getEdgeColor = (relationship: string) => {
    switch (relationship?.toUpperCase()) {
      case 'CITES':
        return '#64748b'; // slate-500
      case 'FOLLOWS':
        return '#10b981'; // emerald-500
      case 'APPLIES':
        return '#3b82f6'; // blue-500
      case 'DISTINGUISHES':
        return '#f59e0b'; // amber-500
      case 'OVERRULES':
        return '#ef4444'; // red-500
      case 'REVERSES':
        return '#ec4899'; // pink-500
      default:
        return '#64748b';
    }
  };

  const handleEdgeClick = (edge: any) => {
    setSelectedEdge(edge);
    if (onEdgeClick) onEdgeClick(edge.id);
  };

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-3 bg-[#080c14] p-8">
        <GitFork size={40} className="text-slate-700" />
        <h3 className="text-sm font-semibold text-slate-300">No Precedent Network Data</h3>
        <p className="text-xs text-slate-500 max-w-sm text-center leading-relaxed">
          No citation relationships have been indexed between this authority and other indexed cases in the landmark corpus.
        </p>
      </div>
    );
  }

  return (
    <div className="relative w-full h-full bg-[#080c14] overflow-hidden select-none" ref={containerRef}>
      {/* Controls Header */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2 bg-slate-900/90 p-1.5 rounded-lg border border-slate-800 backdrop-blur-md shadow-xl">
        {onDepthChange && (
          <div className="flex items-center gap-1 border-r border-slate-800 pr-2 mr-1">
            <span className="text-[10px] uppercase font-bold text-slate-500 px-1">Depth:</span>
            {[1, 2, 3].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => onDepthChange(d)}
                className={`px-2 py-0.5 rounded text-xs font-mono font-medium transition-colors ${
                  depth === d
                    ? 'bg-blue-600 text-white'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={() => setScale((s) => Math.min(s + 0.2, 2.5))}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          title="Zoom In"
        >
          <ZoomIn size={15} />
        </button>
        <button
          type="button"
          onClick={() => setScale((s) => Math.max(s - 0.2, 0.4))}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          title="Zoom Out"
        >
          <ZoomOut size={15} />
        </button>
        <button
          type="button"
          onClick={() => setScale(1)}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          title="Reset View"
        >
          <Maximize size={15} />
        </button>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-900/90 p-3 rounded-lg border border-slate-800 backdrop-blur-md text-xs flex flex-wrap gap-x-4 gap-y-2 max-w-xl shadow-xl">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-500"></div>
          <span className="text-slate-300">Cites</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500"></div>
          <span className="text-slate-300">Follows</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500"></div>
          <span className="text-slate-300">Applies</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500"></div>
          <span className="text-slate-300">Distinguishes</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500"></div>
          <span className="text-slate-300">Overrules</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-pink-500"></div>
          <span className="text-slate-300">Reverses</span>
        </div>
      </div>

      {/* Selected Edge Detail Modal / Card */}
      {selectedEdge && (
        <div className="absolute top-4 left-4 z-10 bg-slate-900/95 border border-slate-700 p-4 rounded-xl shadow-2xl max-w-sm backdrop-blur-md">
          <div className="flex justify-between items-center mb-2">
            <span
              className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded text-white font-mono"
              style={{ backgroundColor: getEdgeColor(selectedEdge.relationship) }}
            >
              {selectedEdge.relationship}
            </span>
            <button
              type="button"
              onClick={() => setSelectedEdge(null)}
              className="text-slate-400 hover:text-white text-xs p-1"
            >
              ✕
            </button>
          </div>
          <div className="text-xs text-slate-300 font-serif italic mb-2 leading-relaxed">
            "{selectedEdge.evidence || 'No verbatim citation excerpt recorded in record.'}"
          </div>
          <div className="text-[10px] text-slate-500 font-mono flex items-center gap-2">
            <span>Page: {selectedEdge.page || 'N/A'}</span>
            <span>•</span>
            <span className="uppercase text-slate-400">{selectedEdge.verification_status || 'VERIFIED'}</span>
          </div>
        </div>
      )}

      {/* SVG Canvas */}
      <div
        className="w-full h-full cursor-grab active:cursor-grabbing flex items-center justify-center"
        style={{
          transform: `scale(${scale})`,
          transformOrigin: 'center center',
          transition: 'transform 0.15s ease-out',
        }}
      >
        <svg width="800" height="600" viewBox="0 0 800 600" className="overflow-visible">
          <defs>
            <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="28" refY="3.5" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#64748b" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((edge) => {
            const source = nodes.find((n) => n.id === edge.source);
            const target = nodes.find((n) => n.id === edge.target);
            if (!source || !target) return null;

            const isUnresolved = target.id.startsWith('unresolved');
            const color = getEdgeColor(edge.relationship);

            return (
              <g
                key={edge.id}
                className="cursor-pointer group"
                onClick={() => handleEdgeClick(edge)}
              >
                <line
                  x1={source.x}
                  y1={source.y}
                  x2={target.x}
                  y2={target.y}
                  stroke={color}
                  strokeWidth="2"
                  strokeOpacity="0.6"
                  strokeDasharray={isUnresolved ? '4 4' : 'none'}
                  markerEnd="url(#arrowhead)"
                  className="group-hover:stroke-blue-400 group-hover:stroke-opacity-100 transition-all"
                />
                <rect
                  x={(source.x + target.x) / 2 - 32}
                  y={(source.y + target.y) / 2 - 10}
                  width="64"
                  height="20"
                  rx="4"
                  fill="#080c14"
                  stroke="#1e293b"
                  strokeWidth="1"
                  className="group-hover:fill-slate-800 transition-colors"
                />
                <text
                  x={(source.x + target.x) / 2}
                  y={(source.y + target.y) / 2 + 3}
                  fontSize="8"
                  fill="#94a3b8"
                  textAnchor="middle"
                  className="group-hover:fill-white font-mono uppercase font-semibold"
                >
                  {edge.relationship}
                </text>
              </g>
            );
          })}

          {/* Nodes */}
          {nodes.map((node) => {
            const isUnresolved = node.id.startsWith('unresolved');
            return (
              <g
                key={node.id}
                className={isUnresolved ? 'cursor-default' : 'cursor-pointer group'}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => {
                  if (!isUnresolved) onNodeClick(node.id);
                }}
              >
                <rect
                  x="-75"
                  y="-25"
                  width="150"
                  height="50"
                  rx="8"
                  fill={isUnresolved ? '#1e293b' : '#0f172a'}
                  stroke={isUnresolved ? '#475569' : '#3b82f6'}
                  strokeWidth="1.5"
                  className="group-hover:stroke-blue-400 group-hover:fill-slate-800 transition-colors shadow-lg"
                  strokeDasharray={isUnresolved ? '4 4' : 'none'}
                />
                <text
                  x="0"
                  y="-5"
                  fontSize="10"
                  fontWeight="bold"
                  fill={isUnresolved ? '#94a3b8' : '#f1f5f9'}
                  textAnchor="middle"
                  className="font-sans"
                >
                  {node.case_name.length > 20 ? `${node.case_name.substring(0, 20)}...` : node.case_name}
                </text>
                <text x="0" y="10" fontSize="8" fill="#64748b" textAnchor="middle" className="font-mono">
                  {isUnresolved ? 'Unindexed Authority' : `${node.court || 'Court'} • ${node.year || 'Year'}`}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

export default PrecedentGraph;
