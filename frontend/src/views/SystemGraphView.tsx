import React, { useState } from 'react';
import { NetworkGraphExport, BlastRadiusResult } from '../types/api';
import { GraphViewer } from '../components/GraphViewer';
import { Filter, Search, Network } from 'lucide-react';

interface SystemGraphViewProps {
  graph: NetworkGraphExport | null;
  blastRadius: BlastRadiusResult | null;
}

export const SystemGraphView: React.FC<SystemGraphViewProps> = ({ graph, blastRadius }) => {
  const [filterType, setFilterType] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  return (
    <div className="space-y-6">
      <div className="bg-slate-900/80 p-6 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-400 mb-1">
            <Network className="w-4 h-4" />
            <span>Static Dependency Graph</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">Discovered Architecture Topology</h2>
          <p className="text-xs text-slate-400 mt-1">
            Visualizing files, API endpoints, functions, and imports discovered via AST parsing.
          </p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search symbol or file..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="flex items-center bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs">
            <Filter className="w-3.5 h-3.5 text-slate-500 mx-2" />
            {['all', 'file', 'endpoint', 'function', 'class'].map((t) => (
              <button
                key={t}
                onClick={() => setFilterType(t)}
                className={`px-2.5 py-1 rounded-md capitalize text-[11px] font-medium transition-all ${
                  filterType === t
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Graph Render */}
      <GraphViewer
        graph={graph || undefined}
        blastRadius={blastRadius || undefined}
        filterType={filterType}
        searchTerm={searchTerm}
      />
    </div>
  );
};
