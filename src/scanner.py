"""プロジェクトスキャナ"""

from pathlib import Path
from typing import Optional

from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

from .config import Config
from .models import DirNode, FileNode, ProjectMap, ProjectStats
from .parser import ParserBase, get_parser


def _load_ignore_file(root: Path, filename: str) -> Optional[PathSpec]:
    """指定された無視ファイルを読み込み PathSpec を生成"""
    ignore_file = root / filename
    if not ignore_file.exists():
        return None

    patterns = []
    for line in ignore_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            patterns.append(line)

    if not patterns:
        return None

    return PathSpec.from_lines(GitWildMatchPattern, patterns)


def _should_exclude(
    path: Path,
    root: Path,
    config: Config,
    specs: list[PathSpec],
    exclude_log_dirs: set[str],
) -> bool:
    """除外判定"""
    # 無視ファイル自体は常に除外
    if path.name in (".gitignore", ".pcmignore"):
        return True

    # 隠しファイル/ディレクトリ
    if not config.include_hidden and path.name.startswith("."):
        return True

    # 明示的除外パターン
    for pattern in config.exclude_patterns:
        if path.match(pattern):
            return True

    # ログディレクトリ
    if path.name in exclude_log_dirs:
        return True

    # 無視ファイル (.gitignore, .pcmignore) ベース
    if config.respect_gitignore:
        rel = path.relative_to(root)
        rel_str = str(rel)
        if path.is_dir():
            rel_str += "/"
        for spec in specs:
            if spec.match_file(rel_str):
                return True

    return False


def scan_project(root: Path, config: Config) -> ProjectMap:
    """プロジェクトをスキャンして ProjectMap を構築"""
    root = root.resolve()

    # 無視ファイルを読み込み
    specs: list[PathSpec] = []
    if config.respect_gitignore:
        for filename in (".gitignore", ".pcmignore"):
            spec = _load_ignore_file(root, filename)
            if spec:
                specs.append(spec)

    exclude_log_dirs = {"log", "logs", ".logs"}

    # パーサーを事前初期化（言語名でキー管理）
    parsers: dict[str, ParserBase] = {}
    for lang in config.languages:
        parser = get_parser(lang)
        if parser:
            parsers[lang] = parser

    # ルートディレクトリノード
    root_node = DirNode(
        name=root.name,
        path=root,
        relative_path=Path("."),
    )

    stats = ProjectStats()

    def _walk(current_path: Path, parent_dir: DirNode) -> None:
        try:
            entries = list(current_path.iterdir())
        except (PermissionError, OSError):
            return

        for entry in entries:
            if _should_exclude(entry, root, config, specs, exclude_log_dirs):
                continue

            if entry.is_dir():
                if not config.follow_symlinks and entry.is_symlink():
                    continue

                subdir = DirNode(
                    name=entry.name,
                    path=entry,
                    relative_path=entry.relative_to(root),
                    parent=parent_dir,
                )
                parent_dir.subdirs.append(subdir)
                stats.total_dirs += 1
                _walk(entry, subdir)

            elif entry.is_file():
                file_node = _process_file(entry, root, config, parsers)
                if file_node:
                    parent_dir.files.append(file_node)
                    stats.add_file(file_node)

    _walk(root, root_node)
    stats.finalize()

    return ProjectMap(root=root_node, stats=stats)


def _process_file(
    file_path: Path, root: Path, config: Config, parsers: dict[str, ParserBase]
) -> Optional[FileNode]:
    """単一ファイルを処理"""
    try:
        stat = file_path.stat()
        if stat.st_size > config.max_file_size_kb * 1024:
            return None
    except OSError:
        return None

    rel_path = file_path.relative_to(root)
    ext = file_path.suffix.lower()

    # 拡張子から言語名を推定
    language = _ext_to_language(ext)
    parser = parsers.get(language) if language else None
    if not parser:
        # 解析非対応言語もファイルとして記録
        return FileNode(
            path=file_path,
            relative_path=rel_path,
            language=None,
            size_bytes=stat.st_size,
        )

    try:
        functions = parser.parse_file(file_path, config)
        return FileNode(
            path=file_path,
            relative_path=rel_path,
            language=parser.language_name,
            functions=functions,
            size_bytes=stat.st_size,
        )
    except Exception as e:
        return FileNode(
            path=file_path,
            relative_path=rel_path,
            language=parser.language_name,
            size_bytes=stat.st_size,
            error=str(e),
        )


def _ext_to_language(ext: str) -> Optional[str]:
    """拡張子から言語名を推定"""
    mapping = {
        ".py": "python",
        ".pyw": "python",
        ".pyi": "python",
        ".php": "php",
        ".phtml": "php",
        ".php7": "php",
        ".php8": "php",
    }
    return mapping.get(ext)
