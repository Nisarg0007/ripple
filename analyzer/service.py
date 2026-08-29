from typing import Optional
from analyzer.models import AnalysisResult
from analyzer.repository import RepositoryScanner
from analyzer.git import GitInspector

class RepositoryAnalyzer:
    """
    Main orchestration service for analyzing a local repository.
    Combines AST inspection with Git information.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def analyze(self, base_ref: Optional[str] = None) -> AnalysisResult:
        scanner = RepositoryScanner(self.repo_path)
        repo_info, files = scanner.scan_repository()

        git_inspector = GitInspector(self.repo_path)
        git_info = git_inspector.get_git_info(base_ref=base_ref)

        total_functions = sum(
            len(f.functions) + sum(len(c.methods) for c in f.classes)
            for f in files
        )
        total_classes = sum(len(f.classes) for f in files)
        total_endpoints = sum(len(f.endpoints) for f in files)
        total_imports = sum(len(f.imports) for f in files)

        summary = {
            "python_files": repo_info.python_file_count,
            "functions": total_functions,
            "classes": total_classes,
            "endpoints": total_endpoints,
            "imports": total_imports,
            "changed_files": len(git_info.changes)
        }

        return AnalysisResult(
            repository=repo_info,
            git=git_info,
            files=files,
            summary=summary
        )
