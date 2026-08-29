import os
from typing import List, Tuple
from analyzer.models import RepositoryInfo, SourceFile
from analyzer.python_parser import parse_python_file

EXCLUDE_DIRS = {
    ".git", ".venv", "venv", "env", "__pycache__", "node_modules",
    ".pytest_cache", ".idea", ".vscode", "dist", "build", "egg-info"
}

class RepositoryScanner:
    def __init__(self, root_path: str):
        self.root_path = os.path.abspath(root_path)

    def scan_repository(self) -> Tuple[RepositoryInfo, List[SourceFile]]:
        if not os.path.exists(self.root_path):
            raise ValueError(f"Directory path does not exist: {self.root_path}")

        python_files: List[SourceFile] = []
        subdirectories = set()

        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Exclude virtualenvs, hidden dirs, node_modules etc
            dirnames[:] = [d for d in dirnames if d not in EXCLUDE_DIRS and not d.startswith(".")]

            rel_dir = os.path.relpath(dirpath, self.root_path)
            if rel_dir != ".":
                first_part = rel_dir.split(os.sep)[0]
                subdirectories.add(first_part.replace("\\", "/"))

            for filename in filenames:
                if filename.endswith(".py"):
                    full_path = os.path.join(dirpath, filename)
                    rel_path = os.path.relpath(full_path, self.root_path).replace("\\", "/")
                    
                    # Convert file path to module name (e.g. services/payment/main.py -> services.payment.main)
                    module_parts = rel_path[:-3].split("/")
                    if module_parts[-1] == "__init__":
                        module_name = ".".join(module_parts[:-1]) if len(module_parts) > 1 else "__init__"
                    else:
                        module_name = ".".join(module_parts)

                    source_file = self._process_file(full_path, rel_path, module_name)
                    python_files.append(source_file)

        repo_info = RepositoryInfo(
            root_path=self.root_path,
            python_file_count=len(python_files),
            subdirectories=sorted(list(subdirectories))
        )

        return repo_info, python_files

    def _process_file(self, full_path: str, rel_path: str, module_name: str) -> SourceFile:
        try:
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            return parse_python_file(rel_path, content, module_name)
        except Exception as e:
            return SourceFile(
                path=rel_path,
                module_name=module_name,
                parse_error=f"Failed to read file: {str(e)}"
            )
