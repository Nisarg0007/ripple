import networkx as nx
from analyzer.models import AnalysisResult
from graph.builder import DependencyGraphBuilder
from graph.traversal import ImpactAnalyzer
from graph.models import BlastRadiusResult, NetworkGraphExport

class GraphEngine:
    """
    High-level facade for graph building, impact traversal, and visualization export.
    """
    def __init__(self):
        self.builder = DependencyGraphBuilder()

    def analyze_repository_impact(self, analysis: AnalysisResult) -> BlastRadiusResult:
        graph = self.builder.build_graph(analysis)
        analyzer = ImpactAnalyzer(graph)
        return analyzer.analyze_impact(analysis)

    def get_graph_export(self, analysis: AnalysisResult) -> NetworkGraphExport:
        self.builder.build_graph(analysis)
        return self.builder.export_graph()
