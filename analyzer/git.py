import os
import subprocess
import re
from typing import List, Optional, Tuple
from analyzer.models import GitInfo, CodeChange

class GitInspector:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def _run_git(self, args: List[str]) -> Tuple[int, str]:
        try:
            res = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            return res.returncode, res.stdout.strip()
        except FileNotFoundError:
            return -1, ""
        except Exception:
            return -1, ""

    def get_git_info(self, base_ref: Optional[str] = None) -> GitInfo:
        # Check if inside git work tree
        code, is_inside = self._run_git(["rev-parse", "--is-inside-work-tree"])
        if code != 0 or is_inside != "true":
            return GitInfo(is_git_repo=False)

        # Current branch
        _, branch = self._run_git(["rev-parse", "--abbrev-ref", "HEAD"])
        # Commit hash
        _, commit_hash = self._run_git(["rev-parse", "HEAD"])

        changes = self.get_changes(base_ref)

        return GitInfo(
            is_git_repo=True,
            branch=branch or "HEAD",
            commit_hash=commit_hash or None,
            changes=changes
        )

    def get_changes(self, base_ref: Optional[str] = None) -> List[CodeChange]:
        # Get status of modified/added/deleted files
        changes: List[CodeChange] = []
        
        # Uncommitted / working tree changes
        code, status_out = self._run_git(["status", "--porcelain"])
        if code == 0 and status_out:
            for line in status_out.splitlines():
                if len(line) >= 3:
                    st = line[:2].strip()
                    file_path = line[2:].strip().replace("\\", "/")

                    change_type = "modified"
                    if "A" in st or "?" in st:
                        change_type = "added"
                    elif "D" in st:
                        change_type = "deleted"
                    elif "R" in st:
                        change_type = "renamed"

                    modified_lines = self._get_modified_lines(file_path)
                    changes.append(CodeChange(
                        file_path=file_path,
                        change_type=change_type,
                        modified_lines=modified_lines
                    ))

        # If base_ref provided, compare against base branch
        if base_ref:
            code, diff_out = self._run_git(["diff", "--name-status", base_ref])
            if code == 0 and diff_out:
                existing_files = {c.file_path for c in changes}
                for line in diff_out.splitlines():
                    parts = line.split(maxsplit=1)
                    if len(parts) == 2:
                        st, file_path = parts[0], parts[1].replace("\\", "/")
                        if file_path not in existing_files:
                            change_type = "modified"
                            if st.startswith("A"):
                                change_type = "added"
                            elif st.startswith("D"):
                                change_type = "deleted"
                            elif st.startswith("R"):
                                change_type = "renamed"

                            modified_lines = self._get_modified_lines(file_path, base_ref)
                            changes.append(CodeChange(
                                file_path=file_path,
                                change_type=change_type,
                                modified_lines=modified_lines
                            ))

        return changes

    def _get_modified_lines(self, file_path: str, base_ref: Optional[str] = None) -> List[int]:
        args = ["diff", "-U0"]
        if base_ref:
            args.append(base_ref)
        args.append("--")
        args.append(file_path)

        code, diff_output = self._run_git(args)
        if code != 0 or not diff_output:
            return []

        modified_lines = []
        # Parse diff hunk headers @@ -a,b +c,d @@
        pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
        for line in diff_output.splitlines():
            match = pattern.match(line)
            if match:
                start_line = int(match.group(1))
                count = int(match.group(2)) if match.group(2) is not None else 1
                if count == 0:
                    continue
                modified_lines.extend(range(start_line, start_line + count))

        return sorted(list(set(modified_lines)))
