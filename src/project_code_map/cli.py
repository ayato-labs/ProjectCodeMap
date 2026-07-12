"""CLIエントリーポイント"""

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from .config import Config, load_config
from .scanner import scan_project
from .formatters import get_formatter, FormatType

app = typer.Typer(
    name="project-code-map",
    help="AI駆動開発のためのディレクトリ構造マッピングツール。AIへのコンテキスト伝達を最適化します。",
    add_completion=False,
    rich_markup_mode="rich",
)

console = Console()


def version_callback(value: bool) -> None:
    if value:
        from . import __version__
        console.print(f"ProjectCodeMap v{__version__}")
        raise typer.Exit()


@app.command()
def main(
    root: Path = typer.Argument(
        Path("."), help="スキャン対象のルートディレクトリ", exists=True, file_okay=False, dir_okay=True
    ),
    format: FormatType = typer.Option(
        FormatType.TEXT, "--format", "-f", help="出力形式", case_sensitive=False
    ),
    output: Optional[Path] = typer.Option(
        None, "--output", "-o", help="出力先ファイル (指定しない場合は標準出力)"
    ),
    max_tokens: Optional[int] = typer.Option(
        None, "--max-tokens", help="概算トークン上限で出力を切り詰め"
    ),
    config: Optional[Path] = typer.Option(
        None, "--config", "-c", help="設定ファイルパス (pyproject.toml または .pcmignore)"
    ),
    include_hidden: bool = typer.Option(
        False, "--include-hidden", help="ドットファイル/隠しディレクトリも対象にする"
    ),
    no_gitignore: bool = typer.Option(
        False, "--no-gitignore", help=".gitignore を無視する"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="詳細ログを表示"
    ),
    version: bool = typer.Option(
        False, "--version", callback=version_callback, is_eager=True, help="バージョンを表示して終了"
    ),
) -> None:
    """
    プロジェクトをスキャンし、AIに最適な形式でディレクトリ構造と関数一覧を出力します。
    """
    try:
        cfg = load_config(config)
        if no_gitignore:
            cfg.respect_gitignore = False
        if include_hidden:
            cfg.include_hidden = True
        if max_tokens:
            cfg.max_tokens = max_tokens

        if verbose:
            console.print(f"[dim]Config: {cfg}[/dim]")
            console.print(f"[dim]Scanning: {root.absolute()}[/dim]")

        project_map = scan_project(root, cfg)

        formatter = get_formatter(format)
        result = formatter.format(project_map, cfg)

        if output:
            output.write_text(result, encoding="utf-8")
            console.print(f"[green]✓[/green] Output written to: [bold]{output}[/bold]")
        else:
            console.print(result)

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(Panel(f"[red]Error: {e}[/red]", title="[bold red]Error[/bold red]", border_style="red"))
        if verbose:
            console.print_exception()
        sys.exit(1)


if __name__ == "__main__":
    app()