from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class FunctionDef:
    """関数定義の情報"""

    name: str
    signature: str
    docstring: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    is_async: bool = False
    is_method: bool = False
    class_name: Optional[str] = None
    decorators: list[str] = None

    def __post_init__(self):
        if self.decorators is None:
            self.decorators = []


class ParserBase(ABC):
    """言語パーサーの基底クラス"""

    @property
    @abstractmethod
    def language_name(self) -> str:
        """言語名 (python, php, etc.)"""
        pass

    @property
    @abstractmethod
    def file_extensions(self) -> list[str]:
        """対応する拡張子リスト"""
        pass

    @abstractmethod
    def parse(self, content: str, config: "Config") -> list[FunctionDef]:
        """ソースコードを解析して関数定義リストを返す"""
        pass

    def parse_file(self, file_path: "Path", config: "Config") -> list[FunctionDef]:
        """ファイルを読み込んで解析 (デフォルト実装)"""
        content = file_path.read_text(encoding="utf-8")
        return self.parse(content, config)

    def _truncate_docstring(self, docstring: str, max_len: int) -> Optional[str]:
        """ドックストリングを指定長で切り詰め"""
        if not docstring:
            return None
        docstring = docstring.strip()
        if len(docstring) > max_len:
            return docstring[:max_len] + "..."
        return docstring


# パーサーレジストリ
_PARSERS: dict[str, ParserBase] = {}


def register_parser(parser: ParserBase) -> None:
    """パーサーを登録"""
    for ext in parser.file_extensions:
        _PARSERS[ext] = parser
    _PARSERS[parser.language_name] = parser


def get_parser(language: str) -> Optional[ParserBase]:
    """言語名または拡張子からパーサーを取得"""
    return _PARSERS.get(language)


def list_parsers() -> list[str]:
    """利用可能な言語一覧"""
    return sorted(set(p.language_name for p in _PARSERS.values()))