import React from 'react';
import { CombinedImpactResponse } from '../types/api';
import { GraphViewer } from '../components/GraphViewer';
import { AlertTriangle, CheckCircle2, ArrowRight, ShieldAlert, FileCode, Server, Layers, Sparkles } from 'lucide-react';

interface ImpactViewProps {
  impactData: CombinedImpactResponse | null;
}

export const ImpactView: React.FC<ImpactViewProps> = ({ impactData }) => {
  if (!impactData) {
    return (
      <div className="p-12 text-center text-slate-500">
        Loading impact analysis...
      </div>
    );
  }

  const { impact, risk_report: risk, graph, explanation } = impactData;

  const levelColorMap = {
    LOW: 'text-emerald-400 bg-emerald-950/80 border-emerald-800',
    MEDIUM: 'text-yellow-400 bg-yellow-950/80 border-yellow-800',
    HIGH: 'text-amber-400 bg-amber-950/80 border-amber-800',
    CRITICAL: 'text-rose-400 bg-rose-950/80 border-rose-800'
  };

  return (
    <div className="space-y-6">
      {/* Risk Banner Header */}
      <div className="bg-slate-900/80 p-6 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-xl">
        <div className="flex items-center gap-5">
          <div className={`p-4 rounded-xl border text-center min-w-[100px] ${levelColorMap[risk.risk_level]}`}>
            <div className="text-3xl font-black font-mono">{risk.total_score}</div>
            <div className="text-[10px] font-bold uppercase tracking-wider mt-0.5">{risk.risk_level}</div>
          </div>

          <div>
            <div className="flex items-center gap-2 text-xs text-slate-400 mb-1">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span>Calculated Blast Radius Risk Score</span>
            </div>
            <h2 className="text-lg font-bold text-slate-100">
              {risk.total_score > 60 ? 'High Downstream Change Impact' : 'Low-to-Moderate Change Impact'}
            </h2>
            <p className="text-xs text-slate-400 mt-1 max-w-lg">
              Ripple analyzed AST dependencies and git changes to determine potential breaking changes.
            </p>
          </div>
        </div>

        {/* Changed vs Impacted Quick Metrics */}
        <div className="flex items-center gap-6 border-t md:border-t-0 md:border-l border-slate-800 pt-4 md:pt-0 md:pl-6 text-xs">
          <div>
            <span className="text-slate-400 block text-[11px]">Direct Files</span>
            <span className="text-lg font-bold font-mono text-rose-400">
              {impact.directly_changed_files.length}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Downstream Impact</span>
            <span className="text-lg font-bold font-mono text-amber-400">
              {impact.total_impacted_count}
            </span>
          </div>
          <div>
            <span className="text-slate-400 block text-[11px]">Affected APIs</span>
            <span className="text-lg font-bold font-mono text-emerald-400">
              {impact.impacted_endpoints.length}
            </span>
          </div>
        </div>
      </div>

      {/* AI Explanation Banner */}
      {explanation && (
        <div className="bg-slate-900/90 p-6 rounded-xl border border-blue-900/40 space-y-3 shadow-lg">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2 font-semibold text-xs text-blue-400 uppercase tracking-wider">
              <Sparkles className="w-4 h-4 text-cyan-400" />
              <span>Why Is This Risky? (Natural Language Explanation)</span>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 bg-slate-950 border border-slate-800 rounded text-slate-400">
              {explanation.is_fallback ? 'Deterministic Fallback' : `AI Powered (${explanation.provider_used})`}
            </span>
          </div>

          <div className="text-sm font-semibold text-slate-100">
            {explanation.summary}
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            {explanation.why_risky}
          </p>
        </div>
      )}

      {/* Main Grid Layout: Interactive Graph + Impact Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Interactive Graph (2 cols) */}
        <div className="lg:col-span-2 space-y-4">
          <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
              <Layers className="w-4 h-4 text-blue-400" />
              <span>Change Blast Radius Map</span>
            </div>
            <div className="flex items-center gap-4 text-[11px] font-mono">
              <span className="flex items-center gap-1.5 text-rose-400">
                <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-ping"></span>
                Direct Change
              </span>
              <span className="flex items-center gap-1.5 text-amber-400">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500"></span>
                Impacted
              </span>
            </div>
          </div>

          <GraphViewer graph={graph} blastRadius={impact} />
        </div>

        {/* Right Column: Risk Factors & Recommendations */}
        <div className="space-y-6">
          {/* Risk Factors Breakdown */}
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-amber-400" />
              <span>Risk Factors Breakdown</span>
            </h3>

            <div className="space-y-2">
              {risk.factors.length > 0 ? (
                risk.factors.map((f, i) => (
                  <div key={i} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs">
                    <div className="flex items-center justify-between font-medium text-slate-200 mb-1">
                      <span>{f.name}</span>
                      <span className="font-mono text-amber-400 font-bold">+{f.score}</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{f.description}</p>
                  </div>
                ))
              ) : (
                <div className="p-4 text-center text-xs text-slate-500">
                  No elevated risk factors detected for this change.
                </div>
              )}
            </div>
          </div>

          {/* Actionable Recommendations */}
          <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              <span>Recommended Pre-Merge Checks</span>
            </h3>

            <div className="space-y-2">
              {risk.recommendations.length > 0 ? (
                risk.recommendations.map((rec, i) => (
                  <div key={i} className="p-3 bg-slate-950/60 rounded-lg border border-slate-800/80 text-xs flex items-start gap-2.5">
                    <ArrowRight className="w-3.5 h-3.5 text-blue-400 shrink-0 mt-0.5" />
                    <span className="text-slate-300">{rec}</span>
                  </div>
                ))
              ) : (
                <div className="p-4 text-center text-xs text-slate-500">
                  No special recommendations required. Standard PR review is sufficient.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Affected Services & Endpoints Lists */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
          <h3 className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <Server className="w-4 h-4 text-blue-400" />
            <span>Affected Microservices & Modules</span>
          </h3>
          <div className="space-y-2 font-mono text-xs">
            {risk.affected_services.length > 0 ? (
              risk.affected_services.map((svc, i) => (
                <div key={i} className="p-2.5 bg-slate-950/50 rounded-lg border border-slate-800 text-slate-300">
                  {svc}
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-xs">No downstream services affected.</div>
            )}
          </div>
        </div>

        <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
          <h3 className="text-xs font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <FileCode className="w-4 h-4 text-emerald-400" />
            <span>Affected API Endpoints</span>
          </h3>
          <div className="space-y-2 font-mono text-xs">
            {impact.impacted_endpoints.length > 0 ? (
              impact.impacted_endpoints.map((ep, i) => (
                <div key={i} className="p-2.5 bg-emerald-950/30 rounded-lg border border-emerald-900/40 text-emerald-300 flex justify-between">
                  <span>{ep.label}</span>
                  <span className="text-slate-500 text-[11px]">{ep.file_path}</span>
                </div>
              ))
            ) : (
              <div className="text-slate-500 text-xs">No API endpoints affected.</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
