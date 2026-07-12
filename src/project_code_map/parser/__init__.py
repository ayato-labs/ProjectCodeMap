"""パーサーモジュール"""

from .base import FunctionDef, ParserBase, get_parser, list_parsers, register_parser
from .python import PythonParser
from .php import PHPParser

# 明示的な登録 (インポート時に自動登録されるが念のため)
# PythonParser と PHPParser は各ファイルで register_parser() を呼んでいる