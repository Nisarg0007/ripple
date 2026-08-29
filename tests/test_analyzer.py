import os
import tempfile
import subprocess
import pytest
from analyzer import RepositoryAnalyzer, parse_python_file

def test_python_parser_imports_functions_classes_endpoints():
    code = """
import os
from typing import List, Optional
from fastapi import FastAPI, APIRouter

app = FastAPI()
router = APIRouter()

class UserService:
    def __init__(self, db):
        self.db = db

    def get_user(self, user_id: int):
        return self.db.find(user_id)

@app.get("/users/{user_id}")
def read_user(user_id: int):
    service = UserService(None)
    return service.get_user(user_id)

@router.post("/payments")
async def create_payment(amount: float):
    return {"status": "ok"}
"""
    sf = parse_python_file("services/user.py", code, "services.user")

    assert sf.parse_error is None
    # 1. Check imports
    modules = [imp.module for imp in sf.imports]
    assert "os" in modules
    assert "typing" in modules
    assert "fastapi" in modules

    # 2. Check classes
    assert len(sf.classes) == 1
    cls = sf.classes[0]
    assert cls.name == "UserService"
    assert len(cls.methods) == 2
    method_names = [m.name for m in cls.methods]
    assert "__init__" in method_names
    assert "get_user" in method_names

    # 3. Check functions
    fn_names = [f.name for f in sf.functions]
    assert "read_user" in fn_names
    assert "create_payment" in fn_names

    # 4. Check FastAPI endpoints
    assert len(sf.endpoints) == 2
    ep_map = {ep.function: (ep.method, ep.path) for ep in sf.endpoints}
    assert ep_map["read_user"] == ("GET", "/users/{user_id}")
    assert ep_map["create_payment"] == ("POST", "/payments")

def test_syntax_errors_handled_gracefully():
    invalid_code = "def broken_function(:"
    sf = parse_python_file("broken.py", invalid_code, "broken")
    assert sf.parse_error is not None
    assert "SyntaxError" in sf.parse_error

def test_multi_file_repository_scan():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create subdirectories and files
        os.makedirs(os.path.join(tmpdir, "services", "user"))
        os.makedirs(os.path.join(tmpdir, "services", "payment"))

        user_code = """
from fastapi import FastAPI
app = FastAPI()

@app.get("/users")
def list_users():
    return []
"""
        payment_code = """
from fastapi import FastAPI
app = FastAPI()

@app.post("/payments")
def process_payment():
    return {}
"""
        non_python_file = os.path.join(tmpdir, "README.md")
        with open(non_python_file, "w") as f:
            f.write("# Demo Repo")

        with open(os.path.join(tmpdir, "services", "user", "main.py"), "w") as f:
            f.write(user_code)

        with open(os.path.join(tmpdir, "services", "payment", "main.py"), "w") as f:
            f.write(payment_code)

        analyzer = RepositoryAnalyzer(tmpdir)
        res = analyzer.analyze()

        assert res.summary["python_files"] == 2
        assert res.summary["endpoints"] == 2
        assert res.summary["functions"] == 2
        assert "services" in res.repository.subdirectories

def test_git_changed_files_detection():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Initialize git repo in tempdir
        subprocess.run(["git", "init"], cwd=tmpdir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=tmpdir, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=tmpdir, check=True)

        file1 = os.path.join(tmpdir, "main.py")
        with open(file1, "w") as f:
            f.write("def foo(): pass\n")

        subprocess.run(["git", "add", "main.py"], cwd=tmpdir, check=True)
        subprocess.run(["git", "commit", "-m", "initial"], cwd=tmpdir, check=True)

        # Modify main.py
        with open(file1, "a") as f:
            f.write("def bar(): pass\n")

        analyzer = RepositoryAnalyzer(tmpdir)
        res = analyzer.analyze()

        assert res.git.is_git_repo is True
        assert len(res.git.changes) == 1
        assert res.git.changes[0].file_path == "main.py"
        assert res.git.changes[0].change_type in ("modified", "added")
        assert len(res.git.changes[0].modified_lines) > 0
