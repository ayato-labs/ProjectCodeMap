"""設定管理"""

from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseModel):
    """実行時設定"""

    # 入力制御
    respect_gitignore: bool = True
    include_hidden: bool = False

    # 除外パターン (.pcmignore / .gitignore 互換)
    exclude_patterns: list[str] = Field(default_factory=list)

    # ファイルサイズ制限
    max_file_size_kb: int = 500

    # 出力制御
    max_tokens: Optional[int] = None
    max_functions_per_file: int = 50

    # 解析制御
    languages: list[str] = Field(default_factory=lambda: ["python", "php"])
    include_docstrings: bool = True
    docstring_max_length: int = 200

    # 走査制御
    follow_symlinks: bool = False


class Settings(BaseSettings):
    """設定ファイル読み込み (pyproject.toml [tool.project-code-map])"""

    model_config = SettingsConfigDict(
        env_prefix="PCM_",
        toml_file="pyproject.toml",
        extra="ignore",
    )

    respect_gitignore: bool = True
    include_hidden: bool = False
    exclude_patterns: list[str] = []
    max_file_size_kb: int = 500
    max_tokens: Optional[int] = None
    max_functions_per_file: int = 50
    languages: list[str] = ["python", "php"]
    include_docstrings: bool = True
    docstring_max_length: int = 200
    follow_symlinks: bool = False


def load_config(config_path: Optional[Path] = None) -> Config:
    """設定を読み込み、Configオブジェクトを生成"""
    settings = Settings()

    # .pcmignore または .gitignore から追加パターンを読み込み
    extra_patterns = []
    for ignore_file in [".pcmignore", ".gitignore"]:
        if config_path:
            ignore_path = config_path.parent / ignore_file
        else:
            ignore_path = Path.cwd() / ignore_file
        if ignore_path.exists():
            content = ignore_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    extra_patterns.append(line)

    return Config(
        respect_gitignore=settings.respect_gitignore,
        include_hidden=settings.include_hidden,
        exclude_patterns=settings.exclude_patterns + extra_patterns,
        max_file_size_kb=settings.max_file_size_kb,
        max_tokens=settings.max_tokens,
        max_functions_per_file=settings.max_functions_per_file,
        languages=settings.languages,
        include_docstrings=settings.include_docstrings,
        docstring_max_length=settings.docstring_max_length,
        follow_symlinks=settings.follow_symlinks,
    )
