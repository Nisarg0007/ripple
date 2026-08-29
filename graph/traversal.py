import networkx as nx
from typing import List, Set, Dict, Tuple, Optional
from collections import deque
from analyzer.models import AnalysisResult, CodeChange
from graph.models import (
    BlastRadiusResult,
    GraphNode,
    ImpactedNode,
    NodeType
)

class ImpactAnalyzer:
    """
    Traverses dependency graph to find downstream blast radius and affected API endpoints.
    """
    def __init__(self, graph: nx.DiGraph):
        self.graph = graph
        # Reverse graph to traverse dependents: if A -> B (A uses B), then B <- A (B impacts A)
        self.reverse_graph = graph.reverse(copy=True)

    def analyze_impact(self, analysis: AnalysisResult) -> BlastRadiusResult:
        directly_changed_files: List[str] = []
        directly_changed_nodes: List[GraphNode] = []
        directly_changed_node_ids: Set[str] = set()

        # 1. Identify directly modified nodes from Git changes
        for change in analysis.git.changes:
            rel_path = change.file_path
            directly_changed_files.append(rel_path)

            file_node_id = f"file:{rel_path}"
            if file_node_id in self.graph:
                node = self._build_graph_node(file_node_id)
                directly_changed_nodes.append(node)
                directly_changed_node_ids.add(file_node_id)

            # Check if specific functions or classes in file were modified
            self._find_modified_symbols(
                rel_path,
                change.modified_lines,
                directly_changed_nodes,
                directly_changed_node_ids
            )

        # Find endpoints defined in modified files
        impacted_endpoints: List[GraphNode] = []
        for rel_path in directly_changed_files:
            self._find_endpoints_in_file(
                rel_path,
                impacted_endpoints
            )

        # If no git changes detected or fresh scan, return empty blast radius
        if not directly_changed_node_ids:
            return BlastRadiusResult(
                directly_changed_files=directly_changed_files,
                directly_changed_nodes=[],
                impacted_nodes=[],
                impacted_endpoints=[],
                total_impacted_count=0,
                max_depth=0
            )

        # 2. Traverse reverse graph via BFS to find all impacted downstream nodes
        impacted_nodes_map: Dict[str, ImpactedNode] = {}
        impacted_endpoints: List[GraphNode] = []

        # Find endpoints defined in modified files
        for rel_path in directly_changed_files:
            self._find_endpoints_in_file(
                rel_path,
                impacted_endpoints
            )

        # Queue items: (node_id, distance, path_list)
        start_node_ids = set(directly_changed_node_ids)
        for ep in impacted_endpoints:
            start_node_ids.add(ep.id)

        queue = deque([(nid, 0, [nid]) for nid in start_node_ids])
        visited: Set[str] = set(start_node_ids)

        max_depth = 0

        while queue:
            curr_id, dist, path = queue.popleft()

            if dist > max_depth:
                max_depth = dist

            # Get predecessors in original graph (successors in reverse_graph)
            dependents = list(self.reverse_graph.successors(curr_id))

            for dep_id in dependents:
                # Ignore containment edges going back to parent file unless intended
                edge_data = self.graph.get_edge_data(dep_id, curr_id) or {}
                edge_type = edge_data.get("type")

                new_dist = dist + 1
                new_path = path + [dep_id]

                if dep_id not in visited:
                    visited.add(dep_id)
                    node = self._build_graph_node(dep_id)

                    impact_type = self._classify_impact_type(node.type, edge_type)

                    impacted_node = ImpactedNode(
                        node=node,
                        distance=new_dist,
                        impact_type=impact_type,
                        path=new_path
                    )

                    impacted_nodes_map[dep_id] = impacted_node

                    if node.type == NodeType.ENDPOINT:
                        impacted_endpoints.append(node)

                    queue.append((dep_id, new_dist, new_path))

        # Deduplicate impacted endpoints from both direct changes and downstream visits
        for dn in directly_changed_nodes:
            if dn.type == NodeType.ENDPOINT and dn not in impacted_endpoints:
                impacted_endpoints.append(dn)

        impacted_nodes_list = sorted(list(impacted_nodes_map.values()), key=lambda x: x.distance)

        return BlastRadiusResult(
            directly_changed_files=directly_changed_files,
            directly_changed_nodes=directly_changed_nodes,
            impacted_nodes=impacted_nodes_list,
            impacted_endpoints=impacted_endpoints,
            total_impacted_count=len(impacted_nodes_list),
            max_depth=max_depth
        )

    def _find_endpoints_in_file(
        self,
        rel_path: str,
        impacted_endpoints: List[GraphNode]
    ):
        for node_id, data in self.graph.nodes(data=True):
            if data.get("file_path") == rel_path and data.get("type") == NodeType.ENDPOINT.value:
                node = self._build_graph_node(node_id)
                if node not in impacted_endpoints:
                    impacted_endpoints.append(node)

    def _find_modified_symbols(
        self,
        rel_path: str,
        modified_lines: List[int],
        directly_changed_nodes: List[GraphNode],
        directly_changed_node_ids: Set[str]
    ):
        if not modified_lines:
            return

        mod_line_set = set(modified_lines)

        for node_id, data in self.graph.nodes(data=True):
            if data.get("file_path") == rel_path and data.get("type") in (NodeType.FUNCTION.value, NodeType.CLASS.value, NodeType.ENDPOINT.value):
                lineno = data.get("lineno")
                end_lineno = data.get("end_lineno") or lineno

                if lineno is not None:
                    # Check overlap with modified lines
                    fn_lines = set(range(lineno, (end_lineno or lineno) + 1))
                    if fn_lines.intersection(mod_line_set):
                        if node_id not in directly_changed_node_ids:
                            node = self._build_graph_node(node_id)
                            directly_changed_nodes.append(node)
                            directly_changed_node_ids.add(node_id)

    def _build_graph_node(self, node_id: str) -> GraphNode:
        data = self.graph.nodes[node_id]
        return GraphNode(
            id=node_id,
            label=data.get("label", node_id),
            type=NodeType(data.get("type", NodeType.FILE.value)),
            file_path=data.get("file_path"),
            lineno=data.get("lineno"),
            end_lineno=data.get("end_lineno"),
            metadata={k: v for k, v in data.items() if k not in ("label", "type", "file_path", "lineno", "end_lineno")}
        )

    def _classify_impact_type(self, node_type: NodeType, edge_type: Optional[str]) -> str:
        if node_type == NodeType.ENDPOINT:
            return "impacted_endpoint"
        elif node_type == NodeType.FILE:
            return "impacted_file"
        elif node_type == NodeType.FUNCTION:
            return "indirect_caller"
        return "dependent_component"
