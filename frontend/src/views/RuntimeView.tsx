import React from 'react';
import { RuntimeGraph } from '../types/api';
import { Activity, Server, ArrowRight, Zap, AlertCircle, Clock } from 'lucide-react';

interface RuntimeViewProps {
  runtimeData: RuntimeGraph | null;
}

export const RuntimeView: React.FC<RuntimeViewProps> = ({ runtimeData }) => {
  if (!runtimeData) {
    return (
      <div className="p-12 text-center text-slate-500">
        Loading runtime telemetry...
      </div>
    );
  }

  const { services, edges, observations_count } = runtimeData;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900/80 p-6 rounded-xl border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-1">
            <Activity className="w-4 h-4" />
            <span>OpenTelemetry Runtime Intelligence</span>
          </div>
          <h2 className="text-xl font-bold text-slate-100">Observed Service Telemetry</h2>
          <p className="text-xs text-slate-400 mt-1">
            Live service-to-service call patterns, request volumes, error rates, and latencies from distributed traces.
          </p>
        </div>

        <div className="bg-slate-950 px-4 py-3 rounded-xl border border-slate-800 text-xs font-mono flex items-center gap-4">
          <div>
            <span className="text-slate-500 block text-[10px]">Traces Captured</span>
            <span className="text-emerald-400 font-bold text-base">{observations_count}</span>
          </div>
          <div className="border-l border-slate-800 pl-4">
            <span className="text-slate-500 block text-[10px]">Services Tracked</span>
            <span className="text-blue-400 font-bold text-base">{services.length}</span>
          </div>
        </div>
      </div>

      {/* Services List */}
      <div className="bg-slate-900/60 p-5 rounded-xl border border-slate-800">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
          <Server className="w-4 h-4 text-blue-400" />
          <span>Active Microservices in Mesh</span>
        </h3>
        <div className="flex flex-wrap gap-2">
          {services.length > 0 ? (
            services.map((svc, i) => (
              <span key={i} className="px-3 py-1.5 bg-slate-950 rounded-lg border border-slate-800 text-xs font-mono text-slate-200 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                {svc}
              </span>
            ))
          ) : (
            <span className="text-xs text-slate-500">No runtime microservices observed yet.</span>
          )}
        </div>
      </div>

      {/* Observed Service Edges Grid */}
      <div className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-2">
          <Zap className="w-4 h-4 text-amber-400" />
          <span>Observed Inter-Service Dependencies & Metrics</span>
        </h3>

        {edges.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {edges.map((e, idx) => (
              <div key={idx} className="bg-slate-900/80 p-5 rounded-xl border border-slate-800 space-y-4 hover:border-slate-700 transition-all">
                <div className="flex items-center justify-between font-mono text-xs border-b border-slate-800/80 pb-3">
                  <div className="flex items-center gap-2 text-slate-200 font-semibold">
                    <span className="text-blue-400">{e.source_service}</span>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500" />
                    <span className="text-emerald-400">{e.destination_service}</span>
                  </div>
                  <span className="text-[11px] text-slate-400 font-sans px-2 py-0.5 bg-slate-950 rounded border border-slate-800">
                    {e.operation}
                  </span>
                </div>

                <div className="grid grid-cols-3 gap-3 text-xs font-mono">
                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 text-[10px] block font-sans">Calls</span>
                    <span className="text-slate-200 font-bold text-sm">{e.request_count}</span>
                  </div>

                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 text-[10px] block font-sans">Errors</span>
                    <span className={`font-bold text-sm ${e.error_count > 0 ? 'text-rose-400' : 'text-slate-400'}`}>
                      {e.error_count}
                    </span>
                  </div>

                  <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/60">
                    <span className="text-slate-500 text-[10px] block font-sans">Avg Latency</span>
                    <span className="text-emerald-400 font-bold text-sm">{e.average_latency_ms} ms</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500 bg-slate-900/40 rounded-xl border border-slate-800 text-xs">
            No runtime service dependencies captured yet. Run tests or exercise microservices to generate OpenTelemetry traces.
          </div>
        )}
      </div>
    </div>
  );
};
