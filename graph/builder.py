import networkx as nx
import re
from typing import Dict, List, Optional
from analyzer.models import AnalysisResult, SourceFile
from graph.models import GraphNode, GraphEdge, NodeType, EdgeType, NetworkGraphExport

class DependencyGraphBuilder:
    """
    Transforms structured AnalysisResult into a directed NetworkX graph.
    
    Edge direction rule:
    Source depends on / uses / contains Target.
    E.g.:
    - File A imports File B -> Edge(A, B, IMPORTS)
    - File A contains Function F -> Edge(A, F, CONTAINS)
    - Function F calls Function G -> Edge(F, G, CALLS)
    - Function F exposes Endpoint E -> Edge(E, F, EXPOSES)
    """
    def __init__(self):
        self.graph = nx.DiGraph()

    def build_graph(self, analysis: AnalysisResult) -> nx.DiGraph:
        self.graph.clear()

        # Index modules for fast lookup (module_name -> file_path)
        module_to_file: Dict[str, str] = {
            f.module_name: f.path for f in analysis.files
        }

        # Index functions/classes (file_path + "::" + name -> node_id)
        function_index: Dict[str, str] = {}
        file_map: Dict[str, SourceFile] = {f.path: f for f in analysis.files}

        # 1. Add File Nodes & Content Nodes
        for sf in analysis.files:
            file_node_id = f"file:{sf.path}"
            self.graph.add_node(
                file_node_id,
                label=sf.path,
                type=NodeType.FILE.value,
                file_path=sf.path,
                module_name=sf.module_name
            )

            # Add Functions
            for fn in sf.functions:
                fn_node_id = f"function:{sf.path}::{fn.name}"
                function_index[f"{sf.path}::{fn.name}"] = fn_node_id
                function_index[fn.name] = fn_node_id  # fallback global lookup

                self.graph.add_node(
                    fn_node_id,
                    label=fn.name,
                    type=NodeType.FUNCTION.value,
                    file_path=sf.path,
                    lineno=fn.lineno,
                    end_lineno=fn.end_lineno,
                    is_async=fn.is_async,
                    args=fn.args
                )
                self.graph.add_edge(file_node_id, fn_node_id, type=EdgeType.CONTAINS.value)

            # Add Classes & Methods
            for cls in sf.classes:
                cls_node_id = f"class:{sf.path}::{cls.name}"
                self.graph.add_node(
                    cls_node_id,
                    label=cls.name,
                    type=NodeType.CLASS.value,
                    file_path=sf.path,
                    lineno=cls.lineno,
                    end_lineno=cls.end_lineno,
                    bases=cls.bases
                )
                self.graph.add_edge(file_node_id, cls_node_id, type=EdgeType.CONTAINS.value)

                for method in cls.methods:
                    method_node_id = f"function:{sf.path}::{cls.name}.{method.name}"
                    function_index[f"{sf.path}::{cls.name}.{method.name}"] = method_node_id
                    function_index[f"{cls.name}.{method.name}"] = method_node_id
                    function_index[method.name] = method_node_id

                    self.graph.add_node(
                        method_node_id,
                        label=f"{cls.name}.{method.name}",
                        type=NodeType.FUNCTION.value,
                        file_path=sf.path,
                        lineno=method.lineno,
                        end_lineno=method.end_lineno,
                        args=method.args
                    )
                    self.graph.add_edge(cls_node_id, method_node_id, type=EdgeType.CONTAINS.value)

            # Add API Endpoints
            for ep in sf.endpoints:
                ep_node_id = f"endpoint:{ep.method}:{ep.path}"
                self.graph.add_node(
                    ep_node_id,
                    label=f"{ep.method} {ep.path}",
                    type=NodeType.ENDPOINT.value,
                    file_path=sf.path,
                    lineno=ep.lineno,
                    method=ep.method,
                    path=ep.path,
                    handler=ep.function
                )
                # Endpoint exposes function
                handler_id = f"function:{sf.path}::{ep.function}"
                if handler_id in self.graph:
                    self.graph.add_edge(ep_node_id, handler_id, type=EdgeType.EXPOSES.value)
                else:
                    self.graph.add_edge(ep_node_id, file_node_id, type=EdgeType.EXPOSES.value)

        # 2. Add Import Edges
        for sf in analysis.files:
            file_node_id = f"file:{sf.path}"
            for imp in sf.imports:
                target_file = module_to_file.get(imp.module)
                if target_file and target_file != sf.path:
                    target_file_node_id = f"file:{target_file}"
                    if target_file_node_id in self.graph:
                        self.graph.add_edge(
                            file_node_id,
                            target_file_node_id,
                            type=EdgeType.IMPORTS.value,
                            imported_name=imp.name
                        )

        # 3. Add Function Call Edges
        for sf in analysis.files:
            all_fns = sf.functions + [m for c in sf.classes for m in c.methods]
            for fn in all_fns:
                fn_node_id = f"function:{sf.path}::{fn.name}" if fn in sf.functions else function_index.get(f"{sf.path}::{fn.name}")
                if not fn_node_id or fn_node_id not in self.graph:
                    continue

                for call_name in fn.calls:
                    target_fn_id = None
                    # First try same file
                    if f"{sf.path}::{call_name}" in function_index:
                        target_fn_id = function_index[f"{sf.path}::{call_name}"]
                    elif call_name in function_index:
                        target_fn_id = function_index[call_name]

                    if target_fn_id and target_fn_id in self.graph and target_fn_id != fn_node_id:
                        self.graph.add_edge(fn_node_id, target_fn_id, type=EdgeType.CALLS.value)

        # 4. Add HTTP Client Call Edges
        # Index server API endpoints: list of (method, path, ep_node_id, file_path)
        server_endpoints = []
        for node_id, data in self.graph.nodes(data=True):
            if data.get("type") == NodeType.ENDPOINT.value:
                server_endpoints.append((
                    data.get("method", "").upper(),
                    data.get("path", ""),
                    node_id,
                    data.get("file_path", "")
                ))

        for sf in analysis.files:
            file_node_id = f"file:{sf.path}"
            for http_call in sf.http_calls:
                caller_fn_node_id = f"function:{sf.path}::{http_call.function}" if http_call.function else file_node_id
                source_node_id = caller_fn_node_id if caller_fn_node_id in self.graph else file_node_id

                # Find matching server endpoint
                for ep_method, ep_path, ep_node_id, ep_file_path in server_endpoints:
                    if ep_method == http_call.method.upper() and self._match_http_paths(http_call.path, ep_path):
                        # Add call edge from client caller -> API Endpoint
                        self.graph.add_edge(
                            source_node_id,
                            ep_node_id,
                            type=EdgeType.CALLS.value,
                            http_method=http_call.method,
                            path=http_call.path
                        )
                        # Add call edge from client file -> server endpoint file
                        if ep_file_path and ep_file_path != sf.path:
                            target_file_node_id = f"file:{ep_file_path}"
                            if target_file_node_id in self.graph:
                                self.graph.add_edge(
                                    file_node_id,
                                    target_file_node_id,
                                    type=EdgeType.CALLS.value,
                                    http_method=http_call.method
                                )

        return self.graph

    def _match_http_paths(self, client_path: str, ep_path: str) -> bool:
        if client_path == ep_path:
            return True
        c_clean = re.sub(r"\{[^}]+\}", "*", client_path).rstrip("/")
        e_clean = re.sub(r"\{[^}]+\}", "*", ep_path).rstrip("/")
        if c_clean == e_clean:
            return True

        c_base = c_clean.split("*")[0].rstrip("/")
        e_base = e_clean.split("*")[0].rstrip("/")
        if c_base and e_base and (c_base == e_base or c_base.startswith(e_base) or e_base.startswith(c_base)):
            return True
        return False

    def export_graph(self) -> NetworkGraphExport:
        nodes: List[GraphNode] = []
        edges: List[GraphEdge] = []

        for node_id, data in self.graph.nodes(data=True):
            nodes.append(GraphNode(
                id=node_id,
                label=data.get("label", node_id),
                type=NodeType(data.get("type", NodeType.FILE.value)),
                file_path=data.get("file_path"),
                lineno=data.get("lineno"),
                end_lineno=data.get("end_lineno"),
                metadata={k: v for k, v in data.items() if k not in ("label", "type", "file_path", "lineno", "end_lineno")}
            ))

        for u, v, data in self.graph.edges(data=True):
            edges.append(GraphEdge(
                source=u,
                target=v,
                type=EdgeType(data.get("type", EdgeType.IMPORTS.value)),
                metadata={k: v for k, v in data.items() if k != "type"}
            ))

        return NetworkGraphExport(nodes=nodes, edges=edges)
