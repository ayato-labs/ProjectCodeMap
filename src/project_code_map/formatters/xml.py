"""XML フォーマッタ (トークン効率重視)"""

import xml.etree.ElementTree as ET
from xml.dom import minidom

from . import FormatterBase, FormatType, register_formatter
from ..models import ProjectMap
from ..config import Config


class XmlFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.XML

    def format(self, project_map: ProjectMap, config: Config) -> str:
        root = ET.Element("project_map")

        # 構造
        structure = ET.SubElement(root, "structure")
        self._serialize_dir(project_map.root, structure)

        # 統計
        stats = ET.SubElement(root, "stats")
        ET.SubElement(stats, "total_files").text = str(project_map.stats.total_files)
        ET.SubElement(stats, "total_dirs").text = str(project_map.stats.total_dirs)
        ET.SubElement(stats, "total_functions").text = str(project_map.stats.total_functions)
        ET.SubElement(stats, "total_size_bytes").text = str(project_map.stats.total_size_bytes)
        ET.SubElement(stats, "estimated_tokens").text = str(project_map.stats.estimated_tokens)

        languages = ET.SubElement(stats, "languages")
        for lang, count in project_map.stats.languages.items():
            ET.SubElement(languages, "language", name=lang).text = str(count)

        # プリティプリント
        rough = ET.tostring(root, encoding="unicode")
        reparsed = minidom.parseString(rough)
        return reparsed.toprettyxml(indent="  ")

    def _serialize_dir(self, node, parent):
        dir_elem = ET.SubElement(parent, "directory", name=node.name)

        for f in node.files:
            file_elem = ET.SubElement(dir_elem, "file", name=f.relative_path.name, path=str(f.relative_path))
            if f.language:
                file_elem.set("language", f.language)
            if f.functions:
                for fn in f.functions:
                    func_elem = ET.SubElement(file_elem, "function", name=fn.name)
                    if fn.signature:
                        func_elem.set("signature", fn.signature)
                    if fn.docstring:
                        func_elem.set("docstring", fn.docstring[:200])
                    func_elem.set("line_start", str(fn.line_start))
                    func_elem.set("line_end", str(fn.line_end))

        for subdir in node.subdirs:
            self._serialize_dir(subdir, dir_elem)


register_formatter(XmlFormatter())