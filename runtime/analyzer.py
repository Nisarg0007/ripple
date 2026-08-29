import math
from typing import List, Dict, Tuple
from runtime.models import RuntimeObservation, RuntimeEdge, RuntimeGraph

class RuntimeAnalyzer:
    """
    Aggregates runtime observations into service dependencies and telemetry metrics.
    """
    def aggregate_observations(self, observations: List[RuntimeObservation]) -> RuntimeGraph:
        services_set = set()
        edge_buckets: Dict[Tuple[str, str, str], List[RuntimeObservation]] = {}

        for obs in observations:
            if obs.source_service:
                services_set.add(obs.source_service)
            if obs.destination_service and obs.destination_service != "external":
                services_set.add(obs.destination_service)

            # Group key: (source, destination, operation)
            key = (obs.source_service, obs.destination_service, obs.operation)
            if key not in edge_buckets:
                edge_buckets[key] = []
            edge_buckets[key].append(obs)

        edges: List[RuntimeEdge] = []
        for (source, dest, op), obs_group in edge_buckets.items():
            req_count = len(obs_group)
            err_count = sum(1 for o in obs_group if o.is_error)
            durations = [o.duration_ms for o in obs_group]
            avg_lat = sum(durations) / req_count if req_count > 0 else 0.0

            # Calculate p95 latency
            sorted_durations = sorted(durations)
            p95_idx = max(0, math.ceil(0.95 * req_count) - 1)
            p95_lat = sorted_durations[p95_idx] if sorted_durations else 0.0

            edges.append(RuntimeEdge(
                source_service=source,
                destination_service=dest,
                operation=op,
                request_count=req_count,
                error_count=err_count,
                average_latency_ms=round(avg_lat, 2),
                p95_latency_ms=round(p95_lat, 2)
            ))

        return RuntimeGraph(
            services=sorted(list(services_set)),
            edges=sorted(edges, key=lambda e: (e.source_service, e.destination_service)),
            observations_count=len(observations)
        )
