import React, { useState, useEffect } from 'react';
import {
  ProjectItem,
  AnalysisResult,
  CombinedImpactResponse,
  RuntimeGraph,
  DriftResponse
} from './types/api';
import {
  fetchProjects,
  analyzeRepository,
  fetchImpactAnalysis,
  fetchRuntimeTelemetry,
  fetchArchitectureDrift
} from './services/api';
import { OverviewView } from './views/OverviewView';
import { ImpactView } from './views/ImpactView';
import { SystemGraphView } from './views/SystemGraphView';
import { RuntimeView } from './views/RuntimeView';
import { DriftView } from './views/DriftView';
import {
  Activity,
  LayoutDashboard,
  ShieldAlert,
  Network,
  Compass,
  RefreshCw,
  FolderGit2,
  AlertCircle
} from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [projects, setProjects] = useState<ProjectItem[]>([]);
  const [selectedPath, setSelectedPath] = useState<string>('demo_services');

  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [impactData, setImpactData] = useState<CombinedImpactResponse | null>(null);
  const [runtimeData, setRuntimeData] = useState<RuntimeGraph | null>(null);
  const [driftData, setDriftData] = useState<DriftResponse | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    if (selectedPath) {
      loadData(selectedPath);
    }
  }, [selectedPath]);

  const loadProjects = async () => {
    try {
      const items = await fetchProjects();
      setProjects(items);
    } catch (e) {
      console.error('Failed to load project list:', e);
    }
  };

  const loadData = async (path: string) => {
    setLoading(true);
    setError(null);
    try {
      const [ana, imp, run, drf] = await Promise.all([
        analyzeRepository(path),
        fetchImpactAnalysis(path),
        fetchRuntimeTelemetry(path),
        fetchArchitectureDrift(path)
      ]);
      setAnalysis(ana);
      setImpactData(imp);
      setRuntimeData(run);
      setDriftData(drf);
    } catch (err: any) {
      setError(err.message || 'Error connecting to Ripple backend API.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0B0F17] text-slate-100 flex flex-col selection:bg-blue-600 selection:text-white">
      {/* Top Navbar */}
      <header className="border-b border-slate-800/80 bg-[#0F1523]/90 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
          {/* Brand */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center font-black text-white text-lg shadow-lg shadow-blue-600/30">
              R
            </div>
            <div>
              <h1 className="font-bold text-base tracking-tight text-slate-100 flex items-center gap-2">
                <span>Ripple</span>
                <span className="text-[10px] font-mono font-medium px-1.5 py-0.5 bg-blue-950 text-blue-400 border border-blue-800 rounded">
                  v0.1.0
                </span>
              </h1>
              <p className="text-[10px] text-slate-400 font-mono">See how far your changes travel.</p>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="hidden md:flex items-center bg-slate-950/80 p-1 rounded-xl border border-slate-800/80 text-xs font-medium">
            {[
              { id: 'overview', label: 'Overview', icon: LayoutDashboard },
              { id: 'impact', label: 'Impact Analysis', icon: ShieldAlert },
              { id: 'graph', label: 'System Graph', icon: Network },
              { id: 'runtime', label: 'Runtime', icon: Activity },
              { id: 'drift', label: 'Drift', icon: Compass }
            ].map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-3 py-1.5 rounded-lg flex items-center gap-2 transition-all ${
                    isActive
                      ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>

          {/* Repository Selector */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 bg-slate-950 px-3 py-1.5 rounded-xl border border-slate-800 text-xs font-mono">
              <FolderGit2 className="w-3.5 h-3.5 text-blue-400" />
              <select
                value={selectedPath}
                onChange={(e) => setSelectedPath(e.target.value)}
                className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
              >
                {projects.map((p) => (
                  <option key={p.path} value={p.path} className="bg-slate-900 text-slate-200">
                    {p.name} ({p.path})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => loadData(selectedPath)}
              disabled={loading}
              className="p-2 bg-slate-900 hover:bg-slate-800 border border-slate-800 rounded-xl text-slate-300 hover:text-white transition-all disabled:opacity-50"
              title="Refresh analysis"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Error Banner */}
        {error && (
          <div className="mb-6 p-4 bg-rose-950/80 border border-rose-800/80 rounded-xl text-xs text-rose-200 flex items-center gap-3">
            <AlertCircle className="w-5 h-5 text-rose-400 shrink-0" />
            <div>
              <strong className="font-semibold block mb-0.5">Analysis Failed</strong>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Tab Views */}
        {activeTab === 'overview' && (
          <OverviewView
            analysis={analysis}
            impactData={impactData}
            driftData={driftData}
            onNavigate={(tab) => setActiveTab(tab)}
          />
        )}

        {activeTab === 'impact' && <ImpactView impactData={impactData} />}

        {activeTab === 'graph' && (
          <SystemGraphView
            graph={impactData?.graph || null}
            blastRadius={impactData?.impact || null}
          />
        )}

        {activeTab === 'runtime' && <RuntimeView runtimeData={runtimeData} />}

        {activeTab === 'drift' && <DriftView driftData={driftData} />}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-600 font-mono">
        Ripple — LatentForce BuildSprint 2026
      </footer>
    </div>
  );
};
