export interface ProjectItem {
  name: string;
  path: string;
  description: string;
}

export interface ImportInfo {
  module: string;
  name?: string;
  alias?: string;
  is_from_import: boolean;
  lineno: number;
}

export interface FunctionInfo {
  name: string;
  lineno: number;
  end_lineno?: number;
  args: string[];
  calls: string[];
  decorators: string[];
  is_async: boolean;
}

export interface ClassInfo {
  name: string;
  lineno: number;
  end_lineno?: number;
  bases: string[];
  methods: FunctionInfo[];
}

export interface APIEndpoint {
  method: string;
  path: string;
  file: string;
  function: string;
  lineno: number;
}

export interface SourceFile {
  path: string;
  module_name: string;
  imports: ImportInfo[];
  functions: FunctionInfo[];
  classes: ClassInfo[];
  endpoints: APIEndpoint[];
  function_calls: string[];
  parse_error?: string;
}

export interface CodeChange {
  file_path: string;
  change_type: string;
  modified_lines: number[];
}

export interface GitInfo {
  is_git_repo: boolean;
  branch?: string;
  commit_hash?: string;
  changes: CodeChange[];
}

export interface RepositoryInfo {
  root_path: string;
  python_file_count: number;
  subdirectories: string[];
}

export interface AnalysisResult {
  repository: RepositoryInfo;
  git: GitInfo;
  files: SourceFile[];
  summary: Record<string, number>;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'file' | 'module' | 'function' | 'class' | 'endpoint';
  file_path?: string;
  lineno?: number;
  end_lineno?: number;
  metadata?: Record<string, any>;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: 'imports' | 'contains' | 'calls' | 'exposes' | 'inherits';
  metadata?: Record<string, any>;
}

export interface NetworkGraphExport {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ImpactedNode {
  node: GraphNode;
  distance: number;
  impact_type: string;
  path: string[];
}

export interface BlastRadiusResult {
  directly_changed_files: string[];
  directly_changed_nodes: GraphNode[];
  impacted_nodes: ImpactedNode[];
  impacted_endpoints: GraphNode[];
  total_impacted_count: number;
  max_depth: number;
}

export interface RiskFactor {
  name: string;
  description: string;
  score: number;
  severity: 'info' | 'low' | 'medium' | 'high' | 'critical';
}

export interface RiskReport {
  total_score: number;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  factors: RiskFactor[];
  directly_changed_files: string[];
  directly_changed_nodes: string[];
  impacted_nodes: string[];
  affected_services: string[];
  affected_endpoints: string[];
  recommendations: string[];
  is_breaking_change: boolean;
}

export interface CombinedImpactResponse {
  analysis: AnalysisResult;
  impact: BlastRadiusResult;
  risk_report: RiskReport;
  graph: NetworkGraphExport;
}

export interface RuntimeEdge {
  source_service: string;
  destination_service: string;
  operation: string;
  request_count: number;
  error_count: number;
  average_latency_ms: number;
  p95_latency_ms: number;
}

export interface RuntimeGraph {
  services: string[];
  edges: RuntimeEdge[];
  observations_count: number;
}

export interface DriftItem {
  source: string;
  target: string;
  operation?: string;
  drift_type: 'static_only' | 'runtime_only' | 'verified';
  description: string;
}

export interface ArchitectureDriftReport {
  verified_dependencies: DriftItem[];
  static_only_dependencies: DriftItem[];
  runtime_only_dependencies: DriftItem[];
  drift_score: number;
}

export interface DriftResponse {
  static_graph: NetworkGraphExport;
  runtime_graph: RuntimeGraph;
  drift_report: ArchitectureDriftReport;
}
