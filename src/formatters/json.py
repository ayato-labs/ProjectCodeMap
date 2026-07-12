"""JSON フォーマッタ"""

import json

from ..config import Config
from ..models import ProjectMap, DirNode
from . import FormatterBase, FormatType, register_formatter


class JsonFormatter(FormatterBase):
    @property
    def format_type(self) -> FormatType:
        return FormatType.JSON

    def format(self, project_map: ProjectMap, config: Config) -> str:
        data = {
            "structure": self._serialize_dir(project_map.root),
            "stats": {
                "total_files": project_map.stats.total_files,
                "total_dirs": project_map.stats.total_dirs,
                "total_functions": project_map.stats.total_functions,
                "total_size_bytes": project_map.stats.total_size_bytes,
                "languages": project_map.stats.languages,
                "estimated_tokens": project_map.stats.estimated_tokens,
            },
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _serialize_dir(self, node: DirNode) -> dict:
        return {
            "name": node.name,
            "path": str(node.relative_path),
            "files": [
                {
                    "name": f.relative_path.name,
                    "path": str(f.relative_path),
                    "language": f.language,
                    "size_bytes": f.size_bytes,
                    "functions": [
                        {
                            "name": fn.name,
                            "signature": fn.signature,
                            "docstring": fn.docstring,
                            "line_start": fn.line_start,
                            "line_end": fn.line_end,
                        }
                        for fn in f.functions
                    ],
                }
                for f in node.files
            ],
            "subdirs": [self._serialize_dir(d) for d in node.subdirs],
        }


register_formatter(JsonFormatter())
