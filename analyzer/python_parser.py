import ast
from typing import List, Tuple, Optional, Dict, Any
from analyzer.models import SourceFile, ImportInfo, FunctionInfo, ClassInfo, APIEndpoint, HTTPClientCall

HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head", "trace", "api_route"}
CLIENT_HTTP_METHODS = {"get", "post", "put", "delete", "patch", "request"}

class ASTVisitor(ast.NodeVisitor):
    def __init__(self, relative_path: str):
        self.relative_path = relative_path
        self.imports: List[ImportInfo] = []
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.endpoints: List[APIEndpoint] = []
        self.http_calls: List[HTTPClientCall] = []
        self.all_calls: List[str] = []
        self.current_function_calls: Optional[List[str]] = None
        self.current_function_name: str = "<global>"
        self.local_variable_values: Dict[str, ast.AST] = {}

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

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.local_variable_values[target.id] = node.value
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        call_name = self._get_call_name(node.func)
        if call_name:
            self.all_calls.append(call_name)
            if self.current_function_calls is not None:
                self.current_function_calls.append(call_name)

            self._check_http_client_call(node, call_name)
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

        prev_fn_name = self.current_function_name
        self.current_function_name = node.name

        # Extract potential FastAPI endpoints from decorators
        self._check_fastapi_endpoint(node.name, node.decorator_list, node.lineno)

        # Record function call trace
        prev_calls = self.current_function_calls
        self.current_function_calls = []

        for stmt in node.body:
            self.visit(stmt)

        fn_calls = self.current_function_calls
        self.current_function_calls = prev_calls
        self.current_function_name = prev_fn_name

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

    def _check_http_client_call(self, node: ast.Call, call_name: str):
        parts = call_name.lower().split(".")
        method_part = parts[-1]
        if method_part in CLIENT_HTTP_METHODS:
            # e.g., httpx.get, httpx.post, requests.get, requests.post, client.get, client.post
            if len(node.args) > 0:
                method = method_part.upper()
                url_node = node.args[0]
                if method_part == "request" and len(node.args) >= 2:
                    if isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        method = node.args[0].value.upper()
                    url_node = node.args[1]

                path = self._extract_path_from_node(url_node)
                if path:
                    self.http_calls.append(HTTPClientCall(
                        method=method,
                        path=path,
                        source_file=self.relative_path,
                        function=self.current_function_name,
                        lineno=node.lineno
                    ))

    def _extract_path_from_node(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Name) and node.id in self.local_variable_values:
            node = self.local_variable_values[node.id]

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value
            if "://" in val:
                p = val.split("://", 1)[1].split("/", 1)
                return f"/{p[1]}" if len(p) > 1 else "/"
            return val if val.startswith("/") else f"/{val}"

        if isinstance(node, ast.JoinedStr):
            parts = []
            for val in node.values:
                if isinstance(val, ast.Constant) and isinstance(val.value, str):
                    parts.append(val.value)
                elif isinstance(val, ast.FormattedValue):
                    var_name = ""
                    if isinstance(val.value, ast.Name):
                        var_name = val.value.id
                    parts.append(f"{{{var_name or 'param'}}}")

            full_str = "".join(parts)
            if "/" in full_str:
                idx = full_str.find("/")
                return full_str[idx:]
            return full_str
        return None

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
            http_calls=visitor.http_calls,
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
