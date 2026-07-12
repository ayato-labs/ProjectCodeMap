"""Parser package - Language parsers for code analysis"""

# Import language parsers to trigger auto-registration
from . import php, python  # noqa: F401
from .base import (
    FunctionDef,
    ParserBase,
    get_parser,
    list_parsers,
    register_parser,
)

__all__ = [
    "ParserBase",
    "FunctionDef",
    "register_parser",
    "get_parser",
    "list_parsers",
]
