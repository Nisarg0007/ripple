from typing import Optional, List, Dict, Any
from runtime.models import RuntimeObservation, RuntimeGraph, ArchitectureDriftReport
from runtime.collector import TraceCollector
from runtime.analyzer import RuntimeAnalyzer
from runtime.drift import ArchitectureDriftDetector
from graph.models import NetworkGraphExport

class RuntimeEngine:
    """
    High-level facade for OpenTelemetry runtime trace collection, aggregation, and drift detection.
    """
    def __init__(self, collector_path: Optional[str] = None):
        if collector_path:
            self.collector = TraceCollector(storage_path=collector_path)
        else:
            self.collector = TraceCollector()
        self.analyzer = RuntimeAnalyzer()
        self.drift_detector = ArchitectureDriftDetector()

    def record_trace(self, observation: RuntimeObservation):
        self.collector.record_observation(observation)

    def ingest_otlp_spans(self, otlp_json: Dict[str, Any]):
        self.collector.ingest_otlp_json(otlp_json)

    def get_runtime_graph(self) -> RuntimeGraph:
        observations = self.collector.get_observations()
        return self.analyzer.aggregate_observations(observations)

    def detect_architecture_drift(self, static_graph_export: NetworkGraphExport) -> ArchitectureDriftReport:
        runtime_graph = self.get_runtime_graph()
        return self.drift_detector.compare(static_graph_export, runtime_graph)

    def clear_runtime_data(self):
        self.collector.clear()
