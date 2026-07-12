"""Python パーサー (tree-sitter 使用)"""

from typing import Optional

import tree_sitter_python as tspython
from tree_sitter import Language, Node, Parser, Query, QueryCursor

from ..config import Config
from .base import FunctionDef, ParserBase, register_parser

# tree-sitter-python 0.26+ の API に対応
_PY_LANGUAGE = Language(tspython.language())

# Separate queries to avoid tree-sitter query engine bug with multiple patterns + predicates
# Working format: use list syntax [...] to combine multiple patterns
_PY_FUNC_QUERY = """
[
  (function_definition
    name: (identifier) @name
    parameters: (parameters) @params
    body: (_) @body
  ) @func_def
  (decorated_definition
    (function_definition
      name: (identifier) @name
      parameters: (parameters) @params
      body: (_) @body
    ) @func_def
  )
]
"""

_PY_CLASS_QUERY = """
(
  (class_definition
    name: (identifier) @class_name
    body: (block) @class_body
  ) @class
)
"""

_PY_PARSER = Parser(_PY_LANGUAGE)
_PY_FUNC_QUERY_OBJ = Query(_PY_LANGUAGE, _PY_FUNC_QUERY)
_PY_CLASS_QUERY_OBJ = Query(_PY_LANGUAGE, _PY_CLASS_QUERY)


def _extract_functions_from_block(
    node: Node, content: str, class_name: Optional[str]
) -> list[FunctionDef]:
    """ブロックノードから関数定義を抽出（クラスのメソッド用）"""
    functions: list[FunctionDef] = []
    for child in node.children:
        if child.type == "function_definition":
            # Skip private methods
            name_node = child.child_by_field_name("name")
            if name_node:
                name = (name_node.text or b"").decode("utf-8")
                if name.startswith("_"):
                    continue


            is_async = any(c.type == "async" for c in child.children)
            func_def = PythonParser._extract_function_static(
                child, (child.text or b"").decode("utf-8"), class_name, is_async
            )
            if func_def:
                functions.append(func_def)
        elif child.type == "decorated_definition":
            # Handle decorated methods
            func_node = child.child_by_field_name("definition")
            if func_node and func_node.type == "function_definition":
                name_node = func_node.child_by_field_name("name")
                if name_node:
                    name = (name_node.text or b"").decode("utf-8")
                    if not name.startswith("_"):
                        is_async = any(c.type == "async" for c in func_node.children)
                        func_def = PythonParser._extract_function_static(
                            func_node, (func_node.text or b"").decode("utf-8"), class_name, is_async
                        )
                        if func_def:
                            functions.append(func_def)
    return functions


class PythonParser(ParserBase):
    @property
    def language_name(self) -> str:
        return "python"

    @property
    def file_extensions(self) -> list[str]:
        return [".py", ".pyw", ".pyi"]

    def parse(self, content: str, config: Config) -> list[FunctionDef]:
        tree = _PY_PARSER.parse(bytes(content, "utf-8"))

        # Run function query
        func_cursor = QueryCursor(_PY_FUNC_QUERY_OBJ)
        func_captures = func_cursor.captures(tree.root_node)

        # Run class query
        class_cursor = QueryCursor(_PY_CLASS_QUERY_OBJ)
        class_captures = class_cursor.captures(tree.root_node)

        functions: list[FunctionDef] = []
        current_class: Optional[str] = None

        # Combine and sort all captures by line number
        all_nodes: list[tuple[int, Node, str]] = []

        for capture_name, nodes in func_captures.items():
            for node in nodes:
                all_nodes.append((node.start_point[0], node, capture_name))

        for capture_name, nodes in class_captures.items():
            for node in nodes:
                all_nodes.append((node.start_point[0], node, capture_name))

        all_nodes.sort(key=lambda x: x[0])

        for _, node, capture_name in all_nodes:
            if capture_name in ("class",):
                class_name_node = node.child_by_field_name("name")
                if class_name_node:
                    current_class = (class_name_node.text or b"").decode("utf-8")

                # Extract methods from class body
                class_body = node.child_by_field_name("body")
                if class_body:
                    methods = _extract_functions_from_block(class_body, content, current_class)
                    for _method in methods:
                        # Methods are already processed with correct class_name
                        pass

            elif capture_name in ("func_def",):
                # Handle both function_definition and decorated_definition
                if node.type == "decorated_definition":
                    # Get the inner function_definition
                    func_node = node.child_by_field_name("definition")
                else:
                    func_node = node

                if func_node is None:
                    continue

                # Skip private functions (starting with _)
                name_node = func_node.child_by_field_name("name")
                if name_node:
                    name = (name_node.text or b"").decode("utf-8")
                    if name.startswith("_"):
                        continue

                # async function has 'async' child
                is_async = any(child.type == "async" for child in func_node.children)
                func_def = self._extract_function(func_node, content, current_class, is_async)
                if func_def:
                    functions.append(func_def)

        return functions

    @staticmethod
    def _extract_function_static(
        node: Node, content: str, class_name: Optional[str], is_async: bool
    ) -> Optional[FunctionDef]:
        """静的メソッドとして関数定義を抽出（クラスメソッド用）"""
        name_node = node.child_by_field_name("name")
        params_node = node.child_by_field_name("parameters")

        if not name_node:
            return None

        name = (name_node.text or b"").decode("utf-8")
        params = (params_node.text or b"").decode("utf-8") if params_node else "()"

        # ドックストリング抽出
        docstring = PythonParser._extract_docstring_static(node, content)

        # シグネチャ構築
        signature = f"{'async ' if is_async else ''}{name}{params}"

        return FunctionDef(
            name=name,
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_async=is_async,
            is_method=class_name is not None,
            class_name=class_name,
        )

    def _extract_function(
        self, node: Node, content: str, class_name: Optional[str], is_async: bool
    ) -> Optional[FunctionDef]:
        return self._extract_function_static(node, content, class_name, is_async)

    @staticmethod
    def _extract_docstring_static(node: Node, content: str) -> Optional[str]:
        """関数/クラスの直後の文字列リテラルをドックストリングとして抽出"""
        body = node.child_by_field_name("body")
        if not body:
            return None

        # ブロック内の最初の文
        for child in body.children:
            if child.type == "expression_statement":
                expr = child.child(0)
                if expr and expr.type == "string":
                    return PythonParser._truncate_docstring(
                        (expr.text or b"").decode("utf-8").strip("\"'"), 200
                    )

            elif child.type != "comment":
                break
        return None

    def _extract_docstring(self, node: Node, content: str) -> Optional[str]:
        return self._extract_docstring_static(node, content)


register_parser(PythonParser())
