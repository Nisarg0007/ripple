import pytest
from analyzer import parse_python_file, AnalysisResult, RepositoryInfo, GitInfo, CodeChange
from graph import DependencyGraphBuilder, ImpactAnalyzer, GraphEngine, NodeType

def test_graph_construction_and_impact_traversal():
    # 1. Mock file contents for a 2-service flow
    db_code = """
def get_db():
    return "db_conn"

def query_user(user_id: int):
    conn = get_db()
    return {"id": user_id, "name": "Alice"}
"""

    api_code = """
from db import query_user
from fastapi import FastAPI

app = FastAPI()

@app.get("/users/{user_id}")
def read_user(user_id: int):
    return query_user(user_id)
"""

    sf_db = parse_python_file("db.py", db_code, "db")
    sf_api = parse_python_file("api.py", api_code, "api")

    analysis = AnalysisResult(
        repository=RepositoryInfo(root_path="/tmp/mock", python_file_count=2, subdirectories=[]),
        git=GitInfo(
            is_git_repo=True,
            branch="main",
            commit_hash="abc",
            changes=[
                CodeChange(file_path="db.py", change_type="modified", modified_lines=[5, 6])  # Modifies query_user
            ]
        ),
        files=[sf_db, sf_api],
        summary={"python_files": 2}
    )

    builder = DependencyGraphBuilder()
    graph = builder.build_graph(analysis)

    # Verify graph nodes exist
    assert "file:db.py" in graph
    assert "file:api.py" in graph
    assert "endpoint:GET:/users/{user_id}" in graph

    analyzer = ImpactAnalyzer(graph)
    blast_radius = analyzer.analyze_impact(analysis)

    # Directly modified file: db.py
    assert "db.py" in blast_radius.directly_changed_files

    # Function query_user should be directly changed
    changed_labels = [n.label for n in blast_radius.directly_changed_nodes]
    assert "query_user" in changed_labels

    # Impacted endpoints: GET /users/{user_id} should be affected downstream!
    impacted_ep_labels = [ep.label for ep in blast_radius.impacted_endpoints]
    assert "GET /users/{user_id}" in impacted_ep_labels

    # Total impacted count should be > 0
    assert blast_radius.total_impacted_count >= 1

def test_graph_export():
    code = """
def hello(): pass
"""
    sf = parse_python_file("hello.py", code, "hello")
    analysis = AnalysisResult(
        repository=RepositoryInfo(root_path="/tmp", python_file_count=1),
        git=GitInfo(is_git_repo=False),
        files=[sf]
    )

    engine = GraphEngine()
    export = engine.get_graph_export(analysis)

    assert len(export.nodes) >= 2  # File node + Function node
    node_types = {n.type for n in export.nodes}
    assert NodeType.FILE in node_types
    assert NodeType.FUNCTION in node_types
