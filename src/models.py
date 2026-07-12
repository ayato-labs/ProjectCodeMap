"""データモデル定義"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class FunctionDef:
    """関数定義"""

    name: str
    signature: str
    docstring: Optional[str] = None
    line_start: int = 0
    line_end: int = 0
    is_async: bool = False
    is_method: bool = False
    class_name: Optional[str] = None
    decorators: list[str] = field(default_factory=list)

    @property
    def qualified_name(self) -> str:
        if self.class_name:
            return f"{self.class_name}.{self.name}"
        return self.name


@dataclass
class FileNode:
    """ファイルノード"""

    path: Path
    relative_path: Path
    language: Optional[str] = None
    functions: list[FunctionDef] = field(default_factory=list)
    size_bytes: int = 0
    error: Optional[str] = None


@dataclass
class DirNode:
    """ディレクトリノード"""

    name: str
    path: Path
    relative_path: Path
    files: list[FileNode] = field(default_factory=list)
    subdirs: list["DirNode"] = field(default_factory=list)
    parent: Optional["DirNode"] = None

    @property
    def all_files(self) -> list[FileNode]:
        """再帰的に全ファイルを取得"""
        result = self.files.copy()
        for subdir in self.subdirs:
            result.extend(subdir.all_files)
        return result

    @property
    def all_functions(self) -> list[FunctionDef]:
        """全関数を取得"""
        result = []
        for f in self.files:
            result.extend(f.functions)
        for subdir in self.subdirs:
            result.extend(subdir.all_functions)
        return result


@dataclass
class ProjectMap:
    """プロジェクトマップ全体"""

    root: DirNode
    stats: "ProjectStats" = field(default_factory=lambda: ProjectStats())


@dataclass
class ProjectStats:
    """統計情報"""

    total_files: int = 0
    total_dirs: int = 0
    total_functions: int = 0
    total_size_bytes: int = 0
    languages: dict[str, int] = field(default_factory=dict)
    estimated_tokens: int = 0

    def add_file(self, file: FileNode) -> None:
        self.total_files += 1
        self.total_size_bytes += file.size_bytes
        self.total_functions += len(file.functions)
        if file.language:
            self.languages[file.language] = self.languages.get(file.language, 0) + 1

    def finalize(self) -> None:
        """トークン概算 (粗い見積もり: 1トークン ≈ 4文字)"""
        # ツリー構造 + 関数シグネチャ + ドックストリング の概算
        chars = self.total_size_bytes + self.total_functions * 50
        self.estimated_tokens = max(1, chars // 4)
