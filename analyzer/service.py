import os
from typing import Optional
from analyzer.models import AnalysisResult, CodeChange
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

        # Normalize change paths relative to repo_info.root_path
        git_root = git_inspector.get_git_root()
        normalized_changes = []
        for change in git_info.changes:
            abs_change_path = os.path.abspath(os.path.join(git_root, change.file_path))
            try:
                rel_to_scan = os.path.relpath(abs_change_path, repo_info.root_path).replace("\\", "/")
                if not rel_to_scan.startswith(".."):
                    normalized_changes.append(CodeChange(
                        file_path=rel_to_scan,
                        change_type=change.change_type,
                        modified_lines=change.modified_lines
                    ))
            except ValueError:
                pass

        git_info.changes = normalized_changes

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
