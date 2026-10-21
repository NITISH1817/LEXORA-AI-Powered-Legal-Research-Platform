import React, { useState, useMemo, useRef } from 'react';
import { ZoomIn, ZoomOut, Maximize, GitFork, X } from 'lucide-react';
import Badge from './ui/Badge';

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
  const [selectedEdge, setSelectedEdge] = useState<any | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Compute node positions using clean useMemo to avoid synchronous setState cascades
  const { nodes, edges } = useMemo(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
      return { nodes: [], edges: [] };
    }

    const centerX = 400;
    const centerY = 300;
    const radius = Math.min(230, Math.max(140, graphData.nodes.length * 18));

    const mappedNodes = graphData.nodes.map((node: any, i: number) => {
      if (i === 0) return { ...node, x: centerX, y: centerY, isRoot: true };

      const angle = ((i - 1) * (2 * Math.PI)) / Math.max(graphData.nodes.length - 1, 1);
      return {
        ...node,
        x: Math.round(centerX + radius * Math.cos(angle)),
        y: Math.round(centerY + radius * Math.sin(angle)),
        isRoot: false,
      };
    });

    return {
      nodes: mappedNodes,
      edges: graphData.edges || [],
    };
  }, [graphData]);

  const getEdgeColor = (relationship: string) => {
    switch (relationship?.toUpperCase()) {
      case 'FOLLOWS':
        return '#10b981'; // emerald-500
      case 'APPLIES':
        return '#3b82f6'; // blue-500
      case 'DISTINGUISHES':
        return '#f59e0b'; // amber-500
      case 'OVERRULES':
        return '#ef4444'; // rose-500
      case 'REVERSES':
        return '#ec4899'; // pink-500
      case 'CITES':
      case 'REFERENCES':
      default:
        return '#64748b'; // slate-500
    }
  };

  const handleEdgeClick = (edge: any) => {
    setSelectedEdge(edge);
    if (onEdgeClick) onEdgeClick(edge.id);
  };

  const handleZoom = (delta: number) => {
    setScale((prev) => Math.min(2.5, Math.max(0.5, +(prev + delta).toFixed(2))));
  };

  const resetZoom = () => {
    setScale(1);
  };

  if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center text-slate-500 gap-3 bg-[#080c14] p-8">
        <GitFork size={40} className="text-slate-700" />
        <h3 className="text-sm font-semibold text-slate-300">No Precedent Network Data</h3>
        <p className="text-xs text-slate-500 max-w-sm text-center leading-relaxed font-sans">
          No citation relationships have been indexed between this authority and other cases in the active database.
        </p>
      </div>
    );
  }

  // Node lookup map for edge coordinate resolution
  const nodeMap = new Map<string, any>(nodes.map((n: any) => [String(n.id), n]));

  return (
    <div
      ref={containerRef}
      className="relative w-full h-full bg-[#080c14] overflow-hidden select-none font-sans"
    >
      {/* Controls Bar */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-2 bg-slate-900/90 p-1.5 rounded-xl border border-slate-800 backdrop-blur-md shadow-xl text-xs">
        {onDepthChange && (
          <div className="flex items-center gap-1 border-r border-slate-800 pr-2 mr-1">
            <span className="text-[10px] uppercase font-bold text-slate-500 px-1 font-mono">
              Depth:
            </span>
            {[1, 2, 3, 4].map((d) => (
              <button
                key={d}
                type="button"
                onClick={() => onDepthChange(d)}
                className={`px-2 py-0.5 rounded font-mono text-[11px] font-semibold transition-colors ${
                  depth === d
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`}
                title={`Expand citation graph to depth ${d}`}
              >
                {d}
              </button>
            ))}
          </div>
        )}

        <button
          type="button"
          onClick={() => handleZoom(0.15)}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          title="Zoom In"
          aria-label="Zoom In"
        >
          <ZoomIn size={15} />
        </button>
        <button
          type="button"
          onClick={() => handleZoom(-0.15)}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          title="Zoom Out"
          aria-label="Zoom Out"
        >
          <ZoomOut size={15} />
        </button>
        <button
          type="button"
          onClick={resetZoom}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors"
          title="Reset View"
          aria-label="Reset View"
        >
          <Maximize size={15} />
        </button>
      </div>

      {/* Relationship Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-slate-900/90 backdrop-blur-md border border-slate-800 rounded-xl p-3 shadow-xl text-[11px]">
        <div className="font-bold text-slate-400 uppercase tracking-wider mb-2 text-[10px] font-mono">
          Relationship Keys
        </div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-0.5 bg-emerald-500 rounded" />
            <span className="text-slate-300">Follows</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-0.5 bg-blue-500 rounded" />
            <span className="text-slate-300">Applies</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-0.5 bg-amber-500 rounded" />
            <span className="text-slate-300">Distinguishes</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-0.5 bg-rose-500 rounded" />
            <span className="text-slate-300">Overrules</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-0.5 bg-pink-500 rounded" />
            <span className="text-slate-300">Reverses</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-0.5 bg-slate-500 rounded" />
            <span className="text-slate-300">Cites / Refs</span>
          </div>
        </div>
      </div>

      {/* Edge Evidence Drawer */}
      {selectedEdge && (
        <div className="absolute top-4 left-4 z-20 max-w-sm bg-slate-900/95 border border-slate-800 rounded-2xl p-5 shadow-2xl backdrop-blur-md">
          <div className="flex items-start justify-between gap-3 mb-2">
            <div>
              <div className="flex items-center gap-1.5 text-[10px] font-mono font-bold uppercase tracking-wider mb-1">
                <span className="text-slate-500">Citation Edge</span>
                <Badge
                  variant={
                    selectedEdge.verification_status === 'VERIFIED' ? 'success' : 'neutral'
                  }
                  size="sm"
                >
                  {selectedEdge.verification_status || 'VERIFIED'}
                </Badge>
              </div>
              <h4 className="font-bold text-slate-100 text-xs">
                Relationship: <span style={{ color: getEdgeColor(selectedEdge.relationship) }}>{selectedEdge.relationship}</span>
              </h4>
            </div>

            <button
              type="button"
              onClick={() => setSelectedEdge(null)}
              className="p-1 text-slate-400 hover:text-white rounded"
              aria-label="Close edge inspector"
            >
              <X size={15} />
            </button>
          </div>

          {selectedEdge.evidence ? (
            <div className="mt-3 p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 text-xs text-slate-300 font-serif italic leading-relaxed">
              "{selectedEdge.evidence}"
            </div>
          ) : (
            <p className="mt-2 text-xs text-slate-500 italic">
              Cited authority referenced without explicit verbatim extract.
            </p>
          )}

          {selectedEdge.page && (
            <div className="mt-2 text-[10px] text-slate-500 font-mono">
              Citation location: Page {selectedEdge.page}
            </div>
          )}
        </div>
      )}

      {/* SVG Canvas */}
      <svg
        className="w-full h-full cursor-grab active:cursor-grabbing"
        viewBox="0 0 800 600"
        style={{ transform: `scale(${scale})`, transformOrigin: 'center center' }}
      >
        <defs>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* Render Edges */}
        <g className="edges">
          {edges.map((edge: any) => {
            const sourceNode = nodeMap.get(String(edge.source));
            const targetNode = nodeMap.get(String(edge.target));
            if (!sourceNode || !targetNode) return null;

            const edgeColor = getEdgeColor(edge.relationship);
            const isSelected = selectedEdge?.id === edge.id;

            return (
              <g
                key={edge.id || `${edge.source}-${edge.target}`}
                onClick={() => handleEdgeClick(edge)}
                className="cursor-pointer group"
              >
                <line
                  x1={sourceNode.x}
                  y1={sourceNode.y}
                  x2={targetNode.x}
                  y2={targetNode.y}
                  stroke={edgeColor}
                  strokeWidth={isSelected ? 3 : 1.5}
                  strokeDasharray={edge.relationship === 'DISTINGUISHES' ? '4,4' : undefined}
                  className="transition-all opacity-70 group-hover:opacity-100"
                />

                {/* Relationship label pill in middle of line */}
                <circle
                  cx={(sourceNode.x + targetNode.x) / 2}
                  cy={(sourceNode.y + targetNode.y) / 2}
                  r={8}
                  fill="#0f172a"
                  stroke={edgeColor}
                  strokeWidth={1}
                />
              </g>
            );
          })}
        </g>

        {/* Render Nodes */}
        <g className="nodes">
          {nodes.map((node: any) => {
            const isRoot = node.isRoot;

            return (
              <g
                key={node.id}
                transform={`translate(${node.x}, ${node.y})`}
                onClick={() => onNodeClick(String(node.id))}
                className="cursor-pointer group"
              >
                {/* Node Outer Ring */}
                <circle
                  r={isRoot ? 26 : 18}
                  fill={isRoot ? '#1e3a8a' : '#0f172a'}
                  stroke={isRoot ? '#3b82f6' : '#334155'}
                  strokeWidth={isRoot ? 3 : 1.5}
                  className="transition-all group-hover:stroke-blue-400 group-hover:scale-110"
                />

                {/* Node Center Dot */}
                <circle
                  r={isRoot ? 10 : 6}
                  fill={isRoot ? '#60a5fa' : node.indexed ? '#94a3b8' : '#e2e8f0'}
                  className="group-hover:fill-white transition-colors"
                />

                {/* Node Label Text */}
                <text
                  y={isRoot ? 38 : 28}
                  textAnchor="middle"
                  fill="#e2e8f0"
                  fontSize={isRoot ? '12px' : '10px'}
                  fontWeight={isRoot ? 'bold' : 'normal'}
                  className="font-sans group-hover:fill-blue-400 transition-colors pointer-events-none drop-shadow-md"
                >
                  {node.case_name?.length > 24
                    ? `${node.case_name.substring(0, 22)}...`
                    : node.case_name || `Case #${node.id}`}
                </text>

                {node.year && (
                  <text
                    y={isRoot ? 50 : 38}
                    textAnchor="middle"
                    fill="#64748b"
                    fontSize="9px"
                    fontFamily="monospace"
                    className="pointer-events-none"
                  >
                    ({node.year})
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
};

export default PrecedentGraph;
