import {
  ProjectItem,
  AnalysisResult,
  CombinedImpactResponse,
  RuntimeGraph,
  DriftResponse,
  NetworkGraphExport
} from '../types/api';

const API_BASE = '/api';

export async function fetchProjects(): Promise<ProjectItem[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  const data = await res.json();
  return data.projects;
}

export async function analyzeRepository(path: string): Promise<AnalysisResult> {
  const res = await fetch(`${API_BASE}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to analyze repository');
  }
  return res.json();
}

export async function fetchImpactAnalysis(path: string): Promise<CombinedImpactResponse> {
  const res = await fetch(`${API_BASE}/impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch impact analysis');
  }
  return res.json();
}

export async function fetchRuntimeTelemetry(path: string): Promise<RuntimeGraph> {
  const res = await fetch(`${API_BASE}/runtime`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch runtime telemetry');
  }
  return res.json();
}

export async function fetchArchitectureDrift(path: string): Promise<DriftResponse> {
  const res = await fetch(`${API_BASE}/drift`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch architecture drift');
  }
  return res.json();
}

export async function fetchRepositoryGraph(path: string): Promise<NetworkGraphExport> {
  const res = await fetch(`${API_BASE}/graph?path=${encodeURIComponent(path)}`);
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || 'Failed to fetch graph');
  }
  return res.json();
}
