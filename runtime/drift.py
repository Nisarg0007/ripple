from typing import Set, Tuple, List
from graph.models import NetworkGraphExport, NodeType, EdgeType
from runtime.models import RuntimeGraph, ArchitectureDriftReport, DriftItem

class ArchitectureDriftDetector:
    """
    Compares Static Graph vs Runtime Graph to discover architectural drift and unmapped calls.
    """
    def compare(self, static_export: NetworkGraphExport, runtime_graph: RuntimeGraph) -> ArchitectureDriftReport:
        # Extract static service-to-service / file-to-file relationships
        static_edges: Set[Tuple[str, str]] = set()

        # Build module/file to service name normalization
        for edge in static_export.edges:
            src = self._normalize_service_name(edge.source)
            tgt = self._normalize_service_name(edge.target)
            if src and tgt and src != tgt:
                static_edges.add((src, tgt))

        # Extract runtime service-to-service relationships
        runtime_edges: Set[Tuple[str, str]] = set()
        runtime_edge_ops = {}
        for edge in runtime_graph.edges:
            src = self._normalize_service_name(edge.source_service)
            tgt = self._normalize_service_name(edge.destination_service)
            if src and tgt and src != tgt and tgt != "external":
                runtime_edges.add((src, tgt))
                runtime_edge_ops[(src, tgt)] = edge.operation

        verified: List[DriftItem] = []
        static_only: List[DriftItem] = []
        runtime_only: List[DriftItem] = []

        # 1. Check runtime edges against static
        for (src, tgt) in runtime_edges:
            op = runtime_edge_ops.get((src, tgt))
            if (src, tgt) in static_edges or self._is_service_match(src, tgt, static_edges):
                verified.append(DriftItem(
                    source=src,
                    target=tgt,
                    operation=op,
                    drift_type="verified",
                    description=f"Dependency {src} -> {tgt} confirmed by both static analysis and runtime traces"
                ))
            else:
                runtime_only.append(DriftItem(
                    source=src,
                    target=tgt,
                    operation=op,
                    drift_type="runtime_only",
                    description=f"Runtime Drift detected: {src} calls {tgt} at runtime, but static analysis has no matching import/client edge"
                ))

        # 2. Check static edges for unobserved dependencies
        verified_pairs = {(v.source, v.target) for v in verified}
        for (src, tgt) in static_edges:
            if (src, tgt) not in verified_pairs and not self._is_pair_in_verified(src, tgt, verified_pairs):
                static_only.append(DriftItem(
                    source=src,
                    target=tgt,
                    drift_type="static_only",
                    description=f"Static dependency {src} -> {tgt} defined in code, but no live runtime traces observed yet"
                ))

        total_deps = len(verified) + len(static_only) + len(runtime_only)
        drift_count = len(runtime_only)
        drift_score = int((drift_count / total_deps * 100)) if total_deps > 0 else 0

        return ArchitectureDriftReport(
            verified_dependencies=verified,
            static_only_dependencies=static_only,
            runtime_only_dependencies=runtime_only,
            drift_score=drift_score
        )

    def _normalize_service_name(self, name: str) -> str:
        clean = name.replace("file:", "").replace("service:", "").replace(".py", "")
        clean = clean.replace("_service", "").replace("-service", "").replace("demo_services.", "").replace("demo-services.", "")
        parts = clean.split("/")
        last = parts[-1] if parts else clean
        return last.split(".")[0].lower()

    def _is_service_match(self, src: str, tgt: str, static_edges: Set[Tuple[str, str]]) -> bool:
        for (s, t) in static_edges:
            if (src in s or s in src) and (tgt in t or t in tgt):
                return True
        return False

    def _is_pair_in_verified(self, src: str, tgt: str, verified_pairs: Set[Tuple[str, str]]) -> bool:
        for (s, t) in verified_pairs:
            if (src in s or s in src) and (tgt in t or t in tgt):
                return True
        return False
