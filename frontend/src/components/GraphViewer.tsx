import React, { useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  Handle,
  Position,
  Node,
  Edge,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { NetworkGraphExport, BlastRadiusResult } from '../types/api';

interface GraphViewerProps {
  graph?: NetworkGraphExport;
  blastRadius?: BlastRadiusResult;
  filterType?: string;
  searchTerm?: string;
}

const CustomNode = ({ data }: { data: any }) => {
  const isDirect = data.isDirect;
  const isImpacted = data.isImpacted;

  let bgClass = "bg-slate-800/90 border-slate-700 text-slate-200";
  if (data.type === 'endpoint') {
    bgClass = "bg-emerald-950/80 border-emerald-600/60 text-emerald-200";
  } else if (data.type === 'function') {
    bgClass = "bg-blue-950/80 border-blue-600/60 text-blue-200";
  } else if (data.type === 'class') {
    bgClass = "bg-purple-950/80 border-purple-600/60 text-purple-200";
  }

  if (isDirect) {
    bgClass = "bg-rose-950/90 border-rose-500 text-rose-100 ring-2 ring-rose-500/50 shadow-lg shadow-rose-950/50 animate-pulse";
  } else if (isImpacted) {
    bgClass = "bg-amber-950/90 border-amber-500 text-amber-100 ring-2 ring-amber-500/40 shadow-md shadow-amber-950/40";
  }

  return (
    <div className={`px-3 py-2 rounded-lg border text-xs font-mono backdrop-blur-sm transition-all shadow-sm ${bgClass}`}>
      <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2" />
      <div className="flex items-center gap-1.5">
        <span className="opacity-60 text-[10px] uppercase tracking-wider font-semibold">
          {data.type}
        </span>
        <span className="font-medium truncate max-w-[180px]">{data.label}</span>
      </div>
      {data.subtext && (
        <div className="text-[10px] opacity-50 truncate mt-0.5 max-w-[180px]">
          {data.subtext}
        </div>
      )}
      <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

export const GraphViewer: React.FC<GraphViewerProps> = ({
  graph,
  blastRadius,
  filterType = 'all',
  searchTerm = ''
}) => {
  const { nodes, edges } = useMemo(() => {
    if (!graph || !graph.nodes) return { nodes: [], edges: [] };

    const directNodeIds = new Set(
      (blastRadius?.directly_changed_nodes || []).map((n) => n.id)
    );
    const impactedNodeIds = new Set(
      (blastRadius?.impacted_nodes || []).map((n) => n.node.id)
    );

    // Filter nodes
    let filteredGraphNodes = graph.nodes;
    if (filterType !== 'all') {
      filteredGraphNodes = filteredGraphNodes.filter((n) => n.type === filterType);
    }
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filteredGraphNodes = filteredGraphNodes.filter((n) =>
        n.label.toLowerCase().includes(term) || (n.file_path && n.file_path.toLowerCase().includes(term))
      );
    }

    const nodeSet = new Set(filteredGraphNodes.map((n) => n.id));

    // Layout positioning in grid
    const cols = 5;
    const xGap = 240;
    const yGap = 100;

    const rfNodes: Node[] = filteredGraphNodes.map((gn, idx) => {
      const col = idx % cols;
      const row = Math.floor(idx / cols);

      return {
        id: gn.id,
        type: 'custom',
        position: { x: col * xGap + 40, y: row * yGap + 40 },
        data: {
          label: gn.label,
          type: gn.type,
          subtext: gn.file_path,
          isDirect: directNodeIds.has(gn.id),
          isImpacted: impactedNodeIds.has(gn.id)
        }
      };
    });

    const rfEdges: Edge[] = graph.edges
      .filter((e) => nodeSet.has(e.source) && nodeSet.has(e.target))
      .map((ge, idx) => {
        let strokeColor = '#334155';
        if (ge.type === 'exposes') strokeColor = '#10B981';
        if (ge.type === 'calls') strokeColor = '#3B82F6';
        if (ge.type === 'imports') strokeColor = '#64748B';

        return {
          id: `edge-${idx}-${ge.source}-${ge.target}`,
          source: ge.source,
          target: ge.target,
          animated: ge.type === 'calls' || ge.type === 'exposes',
          style: { stroke: strokeColor, strokeWidth: 1.5 },
          markerEnd: { type: MarkerType.ArrowClosed, color: strokeColor }
        };
      });

    return { nodes: rfNodes, edges: rfEdges };
  }, [graph, blastRadius, filterType, searchTerm]);

  if (!graph || graph.nodes.length === 0) {
    return (
      <div className="h-64 flex flex-col items-center justify-center text-slate-500 bg-slate-900/50 rounded-xl border border-slate-800">
        <p className="text-sm">No dependency graph nodes found.</p>
      </div>
    );
  }

  return (
    <div className="h-[520px] w-full bg-[#0d131f] rounded-xl border border-slate-800 overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        fitView
        className="bg-transparent"
      >
        <Background color="#1E293B" gap={16} size={1} />
        <Controls />
      </ReactFlow>
    </div>
  );
};
