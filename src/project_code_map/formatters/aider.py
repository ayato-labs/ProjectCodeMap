"""Aider 互換リポジトリマップフォーマッタ"""

from . import FormatterBase, FormatType, register_formatter
from ..models import ProjectMap
from ..config import Config


class AiderFormatter(FormatterBase):
    """Aider の --read-map 形式に近い出力"""

    @property
    def format_type(self) -> FormatType:
        return FormatType.AIDER

    def format(self, project_map: ProjectMap, config: Config) -> str:
        lines = []

        for f in project_map.root.all_files:
            if not f.functions:
                continue

            rel_path = str(f.relative_path).replace("\\", "/")
            lines.append(f"{rel_path}:")

            for fn in f.functions:
                indent = "  "
                if fn.class_name:
                    indent += f"{fn.class_name}."
                indent += fn.name

                if fn.is_async:
                    indent = "async " + indent

                lines.append(indent)

        return "\n".join(lines)


register_formatter(AiderFormatter())