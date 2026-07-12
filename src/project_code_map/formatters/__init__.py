"""Formatters - Output formatting for project maps"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from ..models import ProjectMap
from ..config import Config


class FormatType(str, Enum):
    """出力形式"""

    TEXT = "text"
    MARKDOWN = "markdown"
    XML = "xml"
    JSON = "json"
    AIDER = "aider"


class FormatterBase(ABC):
    """フォーマッタ基底クラス"""

    @property
    @abstractmethod
    def format_type(self) -> FormatType:
        pass

    @abstractmethod
    def format(self, project_map: ProjectMap, config: Config) -> str:
        pass


# フォーマッタレジストリ
_FORMATTERS: dict[FormatType, FormatterBase] = {}


def register_formatter(formatter: FormatterBase) -> None:
    _FORMATTERS[formatter.format_type] = formatter


def get_formatter(format_type: FormatType | str) -> FormatterBase:
    if isinstance(format_type, str):
        format_type = FormatType(format_type.lower())
    formatter = _FORMATTERS.get(format_type)
    if not formatter:
        raise ValueError(f"Unknown format: {format_type}")
    return formatter


def list_formatters() -> list[FormatType]:
    return list(_FORMATTERS.keys())


# フォーマッタをインポートして自動登録
from . import text, structured  # noqa: F401