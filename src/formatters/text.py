"""Text/Markdown formatters"""

from ..config import Config
from ..models import ProjectMap, DirNode
from . import FormatterBase, FormatType, register_formatter


class TextFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.TEXT

    def format(self, project_map: ProjectMap, config: Config) -> str:
        lines = []
        lines.append("=" * 60)
        lines.append("Project Code Map")
        lines.append("=" * 60)
        lines.append("")

        lines.append("## Directory Structure")
        lines.append("")
        self._render_dir(project_map.root, lines, 0)

        lines.append("")
        lines.append("-" * 40)
        lines.append("")

        lines.append("## Function Index")
        lines.append("")

        for file_node in project_map.root.all_files:
            if not file_node.functions:
                continue
            rel = file_node.relative_path
            lines.append(f"### {rel}")
            for func in file_node.functions:
                sig = func.signature
                if func.is_async:
                    sig = f"async {sig}"
                if func.is_method and func.class_name:
                    sig = f"{func.class_name}.{sig}"
                lines.append(f"- `{sig}`")
                if func.docstring:
                    doc = func.docstring.replace("\n", " ")
                    lines.append(f"  > {doc}")
            lines.append("")

        stats = project_map.stats
        lines.append("-" * 40)
        lines.append(f"Total files: {stats.total_files}")
        lines.append(f"Total directories: {stats.total_dirs}")
        lines.append(f"Total functions: {stats.total_functions}")
        lines.append(f"Estimated tokens: ~{stats.estimated_tokens:,}")

        return "\n".join(lines)

    def _render_dir(self, dir_node: DirNode, lines: list[str], level: int) -> None:
        indent = "  " * level
        if level == 0:
            lines.append(f"{indent}{dir_node.name}/")
        else:
            lines.append(f"{indent}├── {dir_node.name}/")

        for f in dir_node.files:
            func_info = f" ({len(f.functions)} funcs)" if f.functions else ""
            lines.append(f"{indent}│   ├── {f.relative_path.name}{func_info}")

        for i, sub in enumerate(dir_node.subdirs):
            is_last = i == len(dir_node.subdirs) - 1
            prefix = "└──" if is_last else "├──"
            lines.append(f"{indent}│   {prefix} {sub.name}/")


class MarkdownFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.MARKDOWN

    def format(self, project_map: ProjectMap, config: Config) -> str:
        lines = []
        lines.append("# Project Code Map")
        lines.append("")
        lines.append(f"**Root**: `{project_map.root.path}`")
        lines.append("")

        lines.append("## Directory Structure")
        lines.append("")
        lines.append("```")
        self._render_dir_md(project_map.root, lines, 0, True)
        lines.append("```")
        lines.append("")

        lines.append("## Function Index")
        lines.append("")

        for file_node in project_map.root.all_files:
            if not file_node.functions:
                continue
            lines.append(f"### `{file_node.relative_path}`")
            lines.append("")
            for func in file_node.functions:
                sig = func.signature
                if func.is_async:
                    sig = f"async {sig}"
                if func.is_method and func.class_name:
                    sig = f"{func.class_name}.{sig}"
                lines.append(f"- `{sig}`")
                if func.docstring:
                    lines.append(f"  > {func.docstring}")
            lines.append("")

        stats = project_map.stats
        lines.append("---")
        lines.append(f"- **Files**: {stats.total_files}")
        lines.append(f"- **Directories**: {stats.total_dirs}")
        lines.append(f"- **Functions**: {stats.total_functions}")
        lines.append(f"- **Estimated Tokens**: ~{stats.estimated_tokens:,}")

        return "\n".join(lines)

    def _render_dir_md(self, dir_node: DirNode, lines: list[str], level: int, is_last: bool) -> None:
        indent = "  " * level
        prefix = "└── " if is_last else "├── "
        lines.append(f"{indent}{prefix}{dir_node.name}/")

        for i, f in enumerate(dir_node.files):
            func_info = f" ({len(f.functions)} funcs)" if f.functions else ""
            file_prefix = "    " if is_last else "│   "
            is_last_file = i == len(dir_node.files) - 1 and not dir_node.subdirs
            file_prefix += "└── " if is_last_file else "├── "
            lines.append(f"{indent}{file_prefix}{f.relative_path.name}{func_info}")

        for i, sub in enumerate(dir_node.subdirs):
            is_last_sub = i == len(dir_node.subdirs) - 1
            sub_indent = "  " * level
            sub_indent += "    " if is_last else "│   "
            self._render_dir_md(sub, lines, level + 1, is_last_sub)


register_formatter(TextFormatter())
register_formatter(MarkdownFormatter())
