# ProjectCodeMap

[![PyPI Version](https://img.shields.io/pypi/v/project-code-map.svg)](https://pypi.org/project/project-code-map/)
[![Python Versions](https://img.shields.io/pypi/pyversions/project-code-map.svg)](https://pypi.org/project/project-code-map/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/ayato-labs/ProjectCodeMap/actions/workflows/ci.yml/badge.svg)](https://github.com/ayato-labs/ProjectCodeMap/actions/workflows/ci.yml)
[![Code Style: Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

**AI駆動開発（AIDD）における「コンテキスト伝達の壁」を突破する、リポジトリ構造マッピングツール。**

WebのAIチャット（ChatGPT, Claude, Gemini等）やAI IDE（Cursor, Cline, Aider等）にプロジェクト全体を理解させたいとき、「ディレクトリ構造をどう伝えるか」で毎回苦労していませんか？  
`ProjectCodeMap` は、プロジェクトをスキャンし、**LLMが最小トークンで最大の文脈を把握できる形式（ツリー構造＋関数シグネチャ＋依存関係）** で出力します。

## 解決する課題

| 従来の悩み | ProjectCodeMapでの解決 |
|---|---|
| ツリー構造を手動でコピペしてトークンを浪費する | **トークン効率の良い構造化出力（Text/JSON/XML/Markdown）** でワンショット注入 |
| 関数名しか見えず、責任境界がAIに伝わらない | **tree-sitterによるAST解析**でシグネチャ＋ドックストリング要約を自動抽出 |
| `node_modules` や `__pycache__` 等のノイズが混入する | **`.gitignore`準拠・独自設定（`.pcmignore`）で高精度な除外** |
| AI IDEごとに設定方法がバラバラ | **Aider / Cursor / Cline 等の標準プロトコル対応出力オプション** を内蔵 |

## インストール

### 即座に実行（推奨: `uv` / `pipx`）
```bash
# インストール不要で即実行 (uv)
uvx project-code-map

# または 専用環境にインストール (pipx)
pipx install project-code-map
project-code-map
```

### 開発・プロジェクトローカル導入
```bash
# プロジェクトの dev 依存に追加
pip install --editable .[dev]
# または poetry/uv 等で
uv add --dev project-code-map
```

## クイックスタート

```bash
# 1. プロジェクトルートで実行
project-code-map

# 2. AIに最適な形式で出力してファイル保存 (XMLはトークン効率が良い)
project-code-map --format xml > context.xml

# 3. 生成された context.xml をAIチャットに貼り付け、または Cursor/Cline のカスタム指示に設定
```

## 出力形式の例

### デフォルト（人間可読・Markdownツリー）
```markdown
# Project Code Map

## Directory Structure
project_root/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── scanner.py      # scan_project, FileNode
│   │   └── parser.py       # parse_python, extract_functions
│   └── cli.py              # main entry point
├── tests/
│   └── test_scanner.py
├── pyproject.toml
└── README.md

## Function Index (src/)
### src/core/scanner.py
- `scan_project(root: Path, config: Config) -> ProjectMap`
- `filter_ignored(files: list[Path], patterns: list[str]) -> list[Path]`

### src/core/parser.py
- `parse_python(content: str) -> list[FunctionDef]`
- `extract_docstring(node: ast.AST) -> str | None`
```

### AI注入用（XML・トークン効率重視）
```xml
<project_map>
  <structure>
    <dir name="src">
      <dir name="core">
        <file name="scanner.py">
          <function name="scan_project" signature="scan_project(root: Path, config: Config) -> ProjectMap" docstring="Recursively scans project root..." />
          <function name="filter_ignored" signature="filter_ignored(files: list[Path], patterns: list[str]) -> list[Path]" docstring="Filters files based on gitignore patterns..." />
        </file>
      </dir>
    </dir>
  </structure>
  <stats>
    <files_total>42</files_total>
    <functions_total>128</functions_total>
    <tokens_estimate>3.2k</tokens_estimate>
  </stats>
</project_map>
```

## AIツール連携ガイド（ワークフロー統合）

### Aider (CLI AI Pair Programming)
```bash
# リポジトリマップとして自動利用させる
project-code-map --format aider > .aider.repo-map
aider --read-map .aider.repo-map
```

### Cursor (IDE)
1. `project-code-map --format xml > .cursor/context.xml`
2. **Settings → Rules → Custom Instructions** に以下を追加：
   ```
   @.cursor/context.xml を参照してプロジェクト全体構造を把握してください。
   ```

### Cline (VS Code Extension)
1. `project-code-map --format markdown > .cline/project_map.md`
2. `.clinerules` またはタスク指示で：
   > プロジェクト構造は `.cline/project_map.md` に定義されています。必ず参照してからコード生成を行ってください。

### 汎用LLM (ChatGPT / Claude / Gemini Web UI)
```bash
# トークン制限に合わせてサイズ調整
project-code-map --format xml --max-tokens 8000 > context.xml
```
生成された `context.xml` をプロンプトの冒頭に貼り付け：
> 「以下のプロジェクトマップを参照し、XXXのバグ修正案を提示してください。」

## 設定カスタマイズ

プロジェクトルートに `.pcmignore` または `pyproject.toml` の `[tool.project-code-map]` セクションで設定可能。

### `.pcmignore` (`.gitignore` 互換シンタックス)
```gitignore
# デフォルト除外に追加
*.generated.py
docs/
*.snap
```

### `pyproject.toml` での詳細設定
```toml
[tool.project-code-map]
# 解析対象言語 (tree-sitter対応分)
languages = ["python", "php"]

# 出力制御
max_file_size_kb = 500
max_functions_per_file = 50
include_docstrings = true
docstring_max_length = 200

# 除外パターン (正規表現も可)
exclude_patterns = [
    "**/migrations/**",
    "**/fixtures/**",
    "**/*.test.py"
]

# 出力デフォルト
default_format = "xml"
default_max_tokens = 8000
```

## CLI リファレンス

```bash
project-code-map [OPTIONS]

Options:
  -r, --root PATH              スキャン対象ルートディレクトリ (default: .)
  -f, --format [text|json|xml|markdown|aider]  出力形式 (default: text)
  -o, --output FILE            出力先ファイル (default: stdout)
  --max-tokens INT             概算トークン上限で出力を切り詰め
  --config FILE                設定ファイル指定 (default: pyproject.toml / .pcmignore)
  --include-hidden             ドットファイル/隠しディレクトリも対象にする
  --no-gitignore               .gitignore を無視する
  -v, --verbose                詳細ログ
  --version                    バージョン表示
  -h, --help                   ヘルプ表示
```

## 開発・コントリビューション

### 環境構築
```bash
git clone https://github.com/ayato-labs/ProjectCodeMap.git
cd ProjectCodeMap
uv sync --dev  # または pip install -e .[dev]
```

### テスト・リンティング実行
```bash
# 全チェック (CIと同等)
uv run ruff check .
uv run ruff format --check .
uv run mypy src/
uv run pytest -v
```

### リリース手順 (Maintainer用)
```bash
# バージョン更新後
uv build
uv publish  upload dist/*
git tag v$(uv version --short)
git push --tags
```

## アーキテクチャ概要

```
project-code-map
├── src/project_code_map/
│   ├── __init__.py
│   ├── cli.py              # Typer CLI エントリーポイント
│   ├── config.py           # 設定読み込み (pydantic + pyproject.toml)
│   ├── scanner.py          # ファイルシステム走査 + .gitignore/.pcmignore 適用
│   ├── parser/             # 言語別パーサー (tree-sitter ラッパー)
│   │   ├── __init__.py
│   │   ├── base.py         # 共通インターフェース
│   │   ├── python.py       # Python AST 抽出
│   │   └── php.py          # PHP AST 抽出
│   ├── formatters/         # 出力フォーマッタ
│   │   ├── __init__.py
│   │   ├── text.py
│   │   ├── json.py
│   │   ├── xml.py
│   │   ├── markdown.py
│   │   └── aider.py
│   └── models.py           # データクラス
├── tests/
├── pyproject.toml
└── .github/workflows/ci.yml
```

## 依存関係 (主要)
- **`tree-sitter` / `tree-sitter-python` / `tree-sitter-php`**: 高速・堅牢なAST解析
- **`pathspec`**: `.gitignore` パターンマッチング (Git互換)
- **`pydantic`**: 設定バリデーション
- **`typer`**: モダンなCLI構築
- **`rich`**: コンソール出力

## ライセンス
MIT License - 詳細は [LICENSE](LICENSE) を参照。

## 謝辞
- [Aider](https://github.com/Aider-AI/aider) の Repo Map 概念に着想を得ています。
- [tree-sitter](https://tree-sitter.github.io/tree-sitter/) コミュニティに感謝。

---

**Star ⭐ していただけると開発の励みになります！**  
Issue・PR・質問・要望は [GitHub Issues](https://github.com/ayato-labs/ProjectCodeMap/issues) までお気軽に。