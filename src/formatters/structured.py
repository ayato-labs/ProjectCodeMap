"""XML/JSON/Aider formatters"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom

from ..config import Config
from ..models import DirNode, ProjectMap
from . import FormatterBase, FormatType, register_formatter


class XMLFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.XML

    def format(self, project_map: ProjectMap, config: Config) -> str:
        root = ET.Element("project_map")
        root.set("root", str(project_map.root.path))

        structure = ET.SubElement(root, "structure")
        self._add_dir_element(structure, project_map.root)

        functions_elem = ET.SubElement(root, "functions")
        for file_node in project_map.root.all_files:
            if not file_node.functions:
                continue
            file_elem = ET.SubElement(functions_elem, "file")
            file_elem.set("path", str(file_node.relative_path))
            file_elem.set("language", file_node.language or "unknown")

            for func in file_node.functions:
                func_elem = ET.SubElement(file_elem, "function")
                func_elem.set("name", func.name)
                func_elem.set("signature", func.signature)
                if func.is_async:
                    func_elem.set("async", "true")
                if func.is_method and func.class_name:
                    func_elem.set("class", func.class_name)
                if func.docstring:
                    func_elem.set("docstring", func.docstring)

        stats = ET.SubElement(root, "stats")
        s = project_map.stats
        stats.set("total_files", str(s.total_files))
        stats.set("total_dirs", str(s.total_dirs))
        stats.set("total_functions", str(s.total_functions))
        stats.set("estimated_tokens", str(s.estimated_tokens))

        rough = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough)
        return reparsed.toprettyxml(indent="  ")

    def _add_dir_element(self, parent: ET.Element, dir_node: DirNode) -> None:
        dir_elem = ET.SubElement(parent, "directory")
        dir_elem.set("name", dir_node.name)
        dir_elem.set("path", str(dir_node.relative_path))

        for f in dir_node.files:
            file_elem = ET.SubElement(dir_elem, "file")
            file_elem.set("name", f.relative_path.name)
            if f.functions:
                file_elem.set("functions", str(len(f.functions)))

        for sub in dir_node.subdirs:
            self._add_dir_element(dir_elem, sub)


class JSONFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.JSON

    def format(self, project_map: ProjectMap, config: Config) -> str:
        data = {
            "root": str(project_map.root.path),
            "structure": self._dir_to_dict(project_map.root),
            "functions": self._functions_to_list(project_map),
            "stats": {
                "total_files": project_map.stats.total_files,
                "total_dirs": project_map.stats.total_dirs,
                "total_functions": project_map.stats.total_functions,
                "estimated_tokens": project_map.stats.estimated_tokens,
            },
        }
        return json.dumps(data, indent=2, ensure_ascii=False)

    def _dir_to_dict(self, dir_node: DirNode) -> dict:
        return {
            "name": dir_node.name,
            "path": str(dir_node.relative_path),
            "files": [
                {
                    "name": f.relative_path.name,
                    "language": f.language,
                    "functions": len(f.functions),
                    "size": f.size_bytes,
                }
                for f in dir_node.files
            ],
            "subdirectories": [self._dir_to_dict(s) for s in dir_node.subdirs],
        }

    def _functions_to_list(self, project_map: ProjectMap) -> list[dict]:
        result = []
        for file_node in project_map.root.all_files:
            if not file_node.functions:
                continue
            file_data = {
                "path": str(file_node.relative_path),
                "language": file_node.language,
                "functions": [
                    {
                        "name": f.name,
                        "signature": f.signature,
                        "async": f.is_async,
                        "method": f.is_method,
                        "class": f.class_name,
                        "docstring": f.docstring,
                        "line_start": f.line_start,
                        "line_end": f.line_end,
                    }
                    for f in file_node.functions
                ],
            }
            result.append(file_data)
        return result


class AiderFormatter(FormatterBase):
    """Aider 互換の Repo Map 形式"""

    @property
    def format_type(self) -> FormatType:
        return FormatType.AIDER

    def format(self, project_map: ProjectMap, config: Config) -> str:
        lines = []
        for file_node in project_map.root.all_files:
            if not file_node.functions:
                continue

            rel = str(file_node.relative_path).replace("\\", "/")
            lines.append(f"{rel}:")

            for func in file_node.functions:
                indent = "  "
                if func.is_method and func.class_name:
                    indent += f"{func.class_name}."
                sig = func.signature
                if func.is_async:
                    sig = f"async {sig}"
                lines.append(f"{indent}{sig}")

        return "\n".join(lines)


register_formatter(XMLFormatter())
register_formatter(JSONFormatter())
register_formatter(AiderFormatter())
