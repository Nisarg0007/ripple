import React from 'react';
import { AnalysisResult, CombinedImpactResponse, DriftResponse } from '../types/api';
import { Server, FileCode, Code, Layers, Globe, ShieldAlert, GitBranch, ArrowUpRight } from 'lucide-react';

interface OverviewViewProps {
  analysis: AnalysisResult | null;
  impactData: CombinedImpactResponse | null;
  driftData: DriftResponse | null;
  onNavigate: (tab: string) => void;
}

export const OverviewView: React.FC<OverviewViewProps> = ({
  analysis,
  impactData,
  driftData,
  onNavigate
}) => {
  if (!analysis) {
    return (
      <div className="p-8 text-center text-slate-500">
        Loading system overview...
      </div>
    );
  }

  const summary = analysis.summary || {};
  const riskReport = impactData?.risk_report;
  const driftReport = driftData?.drift_report;

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-gradient-to-r from-blue-950/40 via-slate-900 to-slate-900 p-6 rounded-xl border border-blue-900/30 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-blue-400 mb-1">
            <GitBranch className="w-3.5 h-3.5" />
            <span>Branch: {analysis.git.branch || 'main'}</span>
            <span className="text-slate-600">•</span>
            <span>{analysis.repository.root_path}</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">System Dependency Overview</h2>
          <p className="text-xs text-slate-400 mt-1 max-w-xl">
            Static AST analysis combined with live OpenTelemetry runtime tracing for complete change visibility.
          </p>
        </div>

        <button
          onClick={() => onNavigate('impact')}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-medium flex items-center gap-2 transition-all shadow-lg shadow-blue-600/20 self-start md:self-auto"
        >
          <span>Analyze Change Impact</span>
          <ArrowUpRight className="w-4 h-4" />
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Server className="w-3.5 h-3.5 text-blue-400" />
            <span>Services</span>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {analysis.repository.subdirectories.length || 1}
          </div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <FileCode className="w-3.5 h-3.5 text-cyan-400" />
            <span>Files</span>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {summary.python_files || 0}
          </div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Code className="w-3.5 h-3.5 text-indigo-400" />
            <span>Functions</span>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {summary.functions || 0}
          </div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Layers className="w-3.5 h-3.5 text-purple-400" />
            <span>Classes</span>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {summary.classes || 0}
          </div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <Globe className="w-3.5 h-3.5 text-emerald-400" />
            <span>APIs</span>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {summary.endpoints || 0}
          </div>
        </div>

        <div className="bg-slate-900/60 p-4 rounded-xl border border-slate-800">
          <div className="flex items-center gap-2 text-slate-400 text-xs mb-1">
            <GitBranch className="w-3.5 h-3.5 text-amber-400" />
            <span>Imports</span>
          </div>
          <div className="text-2xl font-bold text-slate-100 font-mono">
            {summary.imports || 0}
          </div>
        </div>
      </div>

      {/* Summary Cards Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Risk Card */}
        <div className="bg-slate-900/60 p-6 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <ShieldAlert className="w-4 h-4 text-rose-400" />
                <span>Change Risk Score</span>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                riskReport?.risk_level === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border border-rose-800' :
                riskReport?.risk_level === 'HIGH' ? 'bg-amber-950 text-amber-300 border border-amber-800' :
                riskReport?.risk_level === 'MEDIUM' ? 'bg-yellow-950 text-yellow-300 border border-yellow-800' :
                'bg-emerald-950 text-emerald-300 border border-emerald-800'
              }`}>
                {riskReport?.risk_level || 'LOW'}
              </span>
            </div>

            <div className="flex items-baseline gap-3 my-2">
              <span className="text-4xl font-extrabold text-slate-100 font-mono">
                {riskReport?.total_score || 0}
              </span>
              <span className="text-sm text-slate-500 font-mono">/ 100</span>
            </div>

            <p className="text-xs text-slate-400 mt-2">
              Calculated based on downstream component impact, affected API contracts, and dependency propagation depth.
            </p>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">
              Impacted Endpoints: <strong className="text-slate-200">{impactData?.impact.impacted_endpoints.length || 0}</strong>
            </span>
            <button
              onClick={() => onNavigate('impact')}
              className="text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
            >
              View Full Blast Radius →
            </button>
          </div>
        </div>

        {/* Drift Summary Card */}
        <div className="bg-slate-900/60 p-6 rounded-xl border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-400">
                <Globe className="w-4 h-4 text-cyan-400" />
                <span>Architecture Drift Status</span>
              </div>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                {driftReport?.runtime_only_dependencies.length || 0} Drift Alerts
              </span>
            </div>

            <div className="space-y-2 my-2">
              <div className="text-xs text-slate-300 flex justify-between py-1 border-b border-slate-800/60">
                <span>Verified Dependencies:</span>
                <span className="font-mono text-emerald-400">{driftReport?.verified_dependencies.length || 0}</span>
              </div>
              <div className="text-xs text-slate-300 flex justify-between py-1 border-b border-slate-800/60">
                <span>Runtime-Only Dependencies (Unmapped):</span>
                <span className="font-mono text-rose-400">{driftReport?.runtime_only_dependencies.length || 0}</span>
              </div>
              <div className="text-xs text-slate-300 flex justify-between py-1">
                <span>Static-Only Dependencies:</span>
                <span className="font-mono text-slate-400">{driftReport?.static_only_dependencies.length || 0}</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-slate-800/80 flex items-center justify-between text-xs">
            <span className="text-slate-400">Comparing AST code graph vs live OTLP telemetry</span>
            <button
              onClick={() => onNavigate('drift')}
              className="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
            >
              View Drift Analysis →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
