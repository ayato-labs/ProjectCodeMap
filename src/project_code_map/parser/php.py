"""PHP パーサー (tree-sitter 使用)"""

from typing import Optional

import tree_sitter_php as tsphp
from tree_sitter import Language, Node, Parser, Query

from .base import FunctionDef, ParserBase, register_parser
from ..config import Config

# tree-sitter-php 0.26+ の API に対応
_PHP_LANGUAGE = Language(tsphp.language_php())

_PHP_QUERY = Query(
    _PHP_LANGUAGE,
    """
    [
        (function_definition
            name: (name) @name
            parameters: (formal_parameters) @params
        ) @func
        (method_declaration
            name: (name) @name
            parameters: (formal_parameters) @params
        ) @method
    ]
    """,
)


class PHPParser(ParserBase):
    """PHP コードパーサー (tree-sitter 使用)"""

    @property
    def language_name(self) -> str:
        return "php"

    @property
    def file_extensions(self) -> list[str]:
        return [".php", ".phtml", ".php7", ".php8"]

    def __init__(self):
        self.parser = Parser(_PHP_LANGUAGE)
        self.query = _PHP_QUERY

    def parse(self, content: str, config: Config) -> list[FunctionDef]:
        """PHP ソースコードを解析して関数定義を抽出"""
        tree = self.parser.parse(bytes(content, "utf-8"))
        functions: list[FunctionDef] = []

        captures = self.query.captures(tree.root_node)
        for node, capture_name in captures:
            if capture_name in ("func", "method"):
                func = self._process_function(node, content, capture_name == "method", config)
                if func:
                    functions.append(func)

        return functions

    def _process_function(
        self, node: Node, content: str, is_method: bool, config: Config
    ) -> Optional[FunctionDef]:
        """関数ノードから FunctionDef を構築"""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None

        name = self._get_node_text(name_node, content)
        if not name:
            return None

        # プライベート関数をスキップ
        if name.startswith("_") and not getattr(config, 'include_private', True):
            return None

        params_node = node.child_by_field_name("parameters")
        params = self._get_node_text(params_node, content) if params_node else "()"

        signature = f"{name}{params}"

        # ドックストリング (PHPDoc) 抽出
        docstring = self._extract_phpdoc(node, content, config)

        return FunctionDef(
            name=name,
            signature=signature,
            docstring=docstring,
            line_start=node.start_point[0] + 1,
            line_end=node.end_point[0] + 1,
            is_method=is_method,
            class_name=None,
        )

    def _extract_phpdoc(self, node: Node, content: str, config: Config) -> Optional[str]:
        """PHPDoc コメントを抽出"""
        prev = node.prev_sibling
        while prev:
            if prev.type == "comment":
                text = self._get_node_text(prev, content)
                if text and text.startswith("/**"):
                    return self._truncate_docstring(text.strip(), config.docstring_max_length)
            prev = prev.prev_sibling
        return None

    @staticmethod
    def _get_node_text(node: Optional[Node], content: str) -> Optional[str]:
        if node is None:
            return None
        return content[node.start_byte : node.end_byte]


# 自動登録
register_parser(PHPParser())