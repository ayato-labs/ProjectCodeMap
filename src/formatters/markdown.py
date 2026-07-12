"""Markdown フォーマッタ"""

from ..config import Config
from ..models import ProjectMap, DirNode
from . import FormatterBase, FormatType, register_formatter


class MarkdownFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.MARKDOWN

    def format(self, project_map: ProjectMap, config: Config) -> str:
        lines = ["# Project Code Map", ""]

        # 構造ツリー
        lines.append("## Directory Structure")
        lines.append("")
        lines.append("```")
        lines.extend(self._format_tree(project_map.root, 0))
        lines.append("```")
        lines.append("")

        # 関数インデックス
        lines.append("## Function Index")
        lines.append("")
        self._format_functions(project_map.root, lines)

        # 統計
        lines.append("")
        lines.append("## Statistics")
        lines.append("")
        lines.append(f"- **Total files**: {project_map.stats.total_files}")
        lines.append(f"- **Total directories**: {project_map.stats.total_dirs}")
        lines.append(f"- **Total functions**: {project_map.stats.total_functions}")
        lines.append(f"- **Estimated tokens**: {project_map.stats.estimated_tokens}")
        lines.append(
            "- **Languages**: "
            + ", ".join(f"{k}({v})" for k, v in project_map.stats.languages.items())
        )

        return "\n".join(lines)

    def _format_tree(self, node: DirNode, level: int) -> list[str]:
        indent = "  " * level
        lines = []

        if level == 0:
            lines.append(f"{node.name}/")
        else:
            lines.append(f"{indent}- {node.name}/")

        for f in node.files:
            if f.error:
                lines.append(f"{indent}  - {f.relative_path.name} ❌ [{f.error}]")
            elif f.functions:
                func_names = ", ".join(fn.name for fn in f.functions)
                lines.append(f"{indent}  - {f.relative_path.name} ({func_names})")
            else:
                lines.append(f"{indent}  - {f.relative_path.name}")

        for subdir in node.subdirs:
            lines.extend(self._format_tree(subdir, level + 1))

        return lines

    def _format_functions(self, node: DirNode, lines: list[str]) -> None:
        for f in node.files:
            if f.functions:
                lines.append(f"### {f.relative_path}")
                for fn in f.functions:
                    sig = fn.signature
                    if fn.docstring:
                        sig += f"  # {fn.docstring[:80]}..."
                    lines.append(f"- `{sig}`")
                lines.append("")

        for subdir in node.subdirs:
            self._format_functions(subdir, lines)


register_formatter(MarkdownFormatter())
