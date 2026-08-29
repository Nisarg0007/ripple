from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class FunctionInfo(BaseModel):
    name: str
    lineno: int
    end_lineno: Optional[int] = None
    args: List[str] = Field(default_factory=list)
    calls: List[str] = Field(default_factory=list)  # Function calls made within this function
    decorators: List[str] = Field(default_factory=list)
    is_async: bool = False

class ClassInfo(BaseModel):
    name: str
    lineno: int
    end_lineno: Optional[int] = None
    bases: List[str] = Field(default_factory=list)
    methods: List[FunctionInfo] = Field(default_factory=list)

class ImportInfo(BaseModel):
    module: str  # e.g., 'os', 'fastapi', 'services.user'
    name: Optional[str] = None  # Specific imported item if 'from X import Y'
    alias: Optional[str] = None
    is_from_import: bool = False
    lineno: int

class APIEndpoint(BaseModel):
    method: str  # GET, POST, PUT, DELETE, PATCH, etc.
    path: str  # e.g., '/users/{user_id}'
    file: str  # Relative file path
    function: str  # Handler function name
    lineno: int

class SourceFile(BaseModel):
    path: str  # Relative path within repo
    module_name: str  # Dot-separated Python module path
    imports: List[ImportInfo] = Field(default_factory=list)
    functions: List[FunctionInfo] = Field(default_factory=list)
    classes: List[ClassInfo] = Field(default_factory=list)
    endpoints: List[APIEndpoint] = Field(default_factory=list)
    function_calls: List[str] = Field(default_factory=list)  # All top-level or general function calls
    parse_error: Optional[str] = None

class CodeChange(BaseModel):
    file_path: str
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    modified_lines: List[int] = Field(default_factory=list)

class GitInfo(BaseModel):
    is_git_repo: bool = False
    branch: Optional[str] = None
    commit_hash: Optional[str] = None
    changes: List[CodeChange] = Field(default_factory=list)

class RepositoryInfo(BaseModel):
    root_path: str
    python_file_count: int = 0
    subdirectories: List[str] = Field(default_factory=list)

class AnalysisResult(BaseModel):
    repository: RepositoryInfo
    git: GitInfo
    files: List[SourceFile] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)
