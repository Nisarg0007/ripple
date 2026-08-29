import React from 'react';
import { DriftResponse } from '../types/api';
import { AlertOctagon, CheckCircle2, HelpCircle, ArrowRight, Compass } from 'lucide-react';

interface DriftViewProps {
  driftData: DriftResponse | null;
}

export const DriftView: React.FC<DriftViewProps> = ({ driftData }) => {
  if (!driftData) {
    return (
      <div className="p-12 text-center text-slate-500">
        Loading architecture drift analysis...
      </div>
    );
  }

  const { drift_report: drift } = driftData;

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-slate-900/80 p-6 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-rose-400 mb-1">
            <Compass className="w-4 h-4" />
            <span>Architecture Drift Analysis</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">Static Code vs Runtime Reality</h2>
          <p className="text-xs text-slate-400 mt-1">
            Detecting unmapped dynamic calls, unrecorded HTTP integrations, and missing static imports.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-4 py-2 bg-slate-950 rounded-xl border border-slate-800 text-xs font-mono">
            <span className="text-slate-500 block text-[10px]">Unmapped Drift Calls</span>
            <span className="text-rose-400 font-bold text-lg">{drift.runtime_only_dependencies.length}</span>
          </div>
        </div>
      </div>

      {/* 3 Categories Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Category 1: Runtime-Only Drift (ALERT) */}
        <div className="bg-slate-900/60 p-5 rounded-xl border border-rose-900/40 space-y-4">
          <div className="flex items-center gap-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
            <AlertOctagon className="w-4 h-4" />
            <span>Runtime-Only Drift ({drift.runtime_only_dependencies.length})</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Observed in live OpenTelemetry traces but missing from static code AST graph.
          </p>

          <div className="space-y-2.5">
            {drift.runtime_only_dependencies.length > 0 ? (
              drift.runtime_only_dependencies.map((item, idx) => (
                <div key={idx} className="p-3 bg-rose-950/30 rounded-lg border border-rose-900/50 text-xs space-y-1 font-mono">
                  <div className="flex items-center gap-2 text-rose-200 font-bold">
                    <span>{item.source}</span>
                    <ArrowRight className="w-3 h-3 text-rose-400" />
                    <span>{item.target}</span>
                  </div>
                  <p className="text-[11px] font-sans text-rose-300/80">{item.description}</p>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-xs text-slate-500 bg-slate-950/50 rounded-lg border border-slate-800">
                No architecture drift detected. All runtime calls match static dependencies!
              </div>
            )}
          </div>
        </div>

        {/* Category 2: Verified Dependencies */}
        <div className="bg-slate-900/60 p-5 rounded-xl border border-emerald-900/40 space-y-4">
          <div className="flex items-center gap-2 text-emerald-400 text-xs font-bold uppercase tracking-wider">
            <CheckCircle2 className="w-4 h-4" />
            <span>Verified Dependencies ({drift.verified_dependencies.length})</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Confirmed by both static code imports and live OpenTelemetry traces.
          </p>

          <div className="space-y-2.5">
            {drift.verified_dependencies.length > 0 ? (
              drift.verified_dependencies.map((item, idx) => (
                <div key={idx} className="p-3 bg-emerald-950/30 rounded-lg border border-emerald-900/50 text-xs space-y-1 font-mono">
                  <div className="flex items-center gap-2 text-emerald-200 font-bold">
                    <span>{item.source}</span>
                    <ArrowRight className="w-3 h-3 text-emerald-400" />
                    <span>{item.target}</span>
                  </div>
                  <p className="text-[11px] font-sans text-emerald-300/80">{item.description}</p>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-xs text-slate-500 bg-slate-950/50 rounded-lg border border-slate-800">
                No overlapping static and runtime dependencies observed yet.
              </div>
            )}
          </div>
        </div>

        {/* Category 3: Static-Only Dependencies */}
        <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 space-y-4">
          <div className="flex items-center gap-2 text-slate-400 text-xs font-bold uppercase tracking-wider">
            <HelpCircle className="w-4 h-4 text-slate-500" />
            <span>Static-Only ({drift.static_only_dependencies.length})</span>
          </div>
          <p className="text-[11px] text-slate-400">
            Declared in code imports, but not yet exercised in active trace telemetry.
          </p>

          <div className="space-y-2.5 max-h-[380px] overflow-y-auto pr-1">
            {drift.static_only_dependencies.length > 0 ? (
              drift.static_only_dependencies.map((item, idx) => (
                <div key={idx} className="p-3 bg-slate-950/50 rounded-lg border border-slate-800 text-xs space-y-1 font-mono">
                  <div className="flex items-center gap-2 text-slate-300 font-medium">
                    <span>{item.source}</span>
                    <ArrowRight className="w-3 h-3 text-slate-600" />
                    <span>{item.target}</span>
                  </div>
                  <p className="text-[11px] font-sans text-slate-500">{item.description}</p>
                </div>
              ))
            ) : (
              <div className="p-4 text-center text-xs text-slate-500 bg-slate-950/50 rounded-lg border border-slate-800">
                All static dependencies have been observed at runtime!
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
