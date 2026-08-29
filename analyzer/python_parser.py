import ast
from typing import List, Tuple, Optional
from analyzer.models import SourceFile, ImportInfo, FunctionInfo, ClassInfo, APIEndpoint

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace", "api_route"}

class ASTVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.imports: List[ImportInfo] = []
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.endpoints: List[APIEndpoint] = []
        self.all_calls: List[str] = []
        self.current_function_calls: Optional[List[str]] = None

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.append(ImportInfo(
                module=alias.name,
                alias=alias.asname,
                is_from_import=False,
                lineno=node.lineno
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        for alias in node.names:
            self.imports.append(ImportInfo(
                module=module,
                name=alias.name,
                alias=alias.asname,
                is_from_import=True,
                lineno=node.lineno
            ))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        call_name = self._get_call_name(node.func)
        if call_name:
            self.all_calls.append(call_name)
            if self.current_function_calls is not None:
                self.current_function_calls.append(call_name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        bases = [self._get_call_name(base) or "object" for base in node.bases]
        class_methods: List[FunctionInfo] = []

        # Store previous context
        outer_calls = self.current_function_calls

        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method_info = self._parse_function(item)
                class_methods.append(method_info)

        self.current_function_calls = outer_calls

        self.classes.append(ClassInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, 'end_lineno', None),
            bases=bases,
            methods=class_methods
        ))
        
        # We process class body statements (avoid double visiting methods)
        for item in node.body:
            if not isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.visit(item)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        fn_info = self._parse_function(node)
        self.functions.append(fn_info)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        fn_info = self._parse_function(node)
        self.functions.append(fn_info)

    def _parse_function(self, node: ast.AST) -> FunctionInfo:
        is_async = isinstance(node, ast.AsyncFunctionDef)
        args = [arg.arg for arg in node.args.args]
        decorators = [self._get_call_name(d) for d in node.decorator_list if self._get_call_name(d)]

        # Extract potential FastAPI endpoints from decorators
        self._check_fastapi_endpoint(node.name, node.decorator_list, node.lineno)

        # Record function call trace
        prev_calls = self.current_function_calls
        self.current_function_calls = []

        for stmt in node.body:
            self.visit(stmt)

        fn_calls = self.current_function_calls
        self.current_function_calls = prev_calls

        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, 'end_lineno', None),
            args=args,
            calls=fn_calls or [],
            decorators=decorators,
            is_async=is_async
        )

    def _check_fastapi_endpoint(self, fn_name: str, decorator_list: List[ast.expr], lineno: int):
        for dec in decorator_list:
            # Decorator can be a Call like @app.get("/users") or @router.post("/pay")
            if isinstance(dec, ast.Call):
                func_node = dec.func
                if isinstance(func_node, ast.Attribute):
                    method_name = func_node.attr.lower()
                    if method_name in HTTP_METHODS:
                        # Extract path from first argument if string literal
                        path = "/"
                        if dec.args:
                            first_arg = dec.args[0]
                            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                                path = first_arg.value
                        
                        self.endpoints.append(APIEndpoint(
                            method=method_name.upper(),
                            path=path,
                            file=self.relative_path,
                            function=fn_name,
                            lineno=lineno
                        ))

    def _get_call_name(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            val = self._get_call_name(node.value)
            return f"{val}.{node.attr}" if val else node.attr
        elif isinstance(node, ast.Call):
            return self._get_call_name(node.func)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

def parse_python_file(relative_path: str, content: str, module_name: str) -> SourceFile:
    try:
        tree = ast.parse(content, filename=relative_path)
        visitor = ASTVisitor(relative_path)
        visitor.visit(tree)

        return SourceFile(
            path=relative_path,
            module_name=module_name,
            imports=visitor.imports,
            functions=visitor.functions,
            classes=visitor.classes,
            endpoints=visitor.endpoints,
            function_calls=visitor.all_calls,
            parse_error=None
        )
    except SyntaxError as e:
        return SourceFile(
            path=relative_path,
            module_name=module_name,
            parse_error=f"SyntaxError: {str(e)}"
        )
    except Exception as e:
        return SourceFile(
            path=relative_path,
            module_name=module_name,
            parse_error=f"Error parsing AST: {str(e)}"
        )
