# コントリビューションガイド

**ProjectCodeMap** への貢献を検討いただき、ありがとうございます！
バグ報告、機能提案、ドキュメント改善、コード修正など、あらゆる形の貢献を歓迎します。

## 開発環境のセットアップ

```bash
# リポジトリをクローン
git clone https://github.com/ayato-labs/ProjectCodeMap.git
cd ProjectCodeMap

# 依存関係をインストール (uv推奨)
uv sync --dev

# または pip で
pip install -e .[dev]

# 事前コミットフックを設定 (任意だが推奨)
uv run pre-commit install
```

## 開発ワークフロー

1. **Issueを作成/選択** - 作業前に Issue で議論・合意を得てください
2. **ブランチを作成** - `feature/xxx`, `fix/xxx`, `docs/xxx` 等の命名規則で
3. **実装・テスト** - 以下の品質チェックをローカルで通してください
4. **Pull Requestを作成** - テンプレートに従って記入

### 品質チェック (CIと同等)

```bash
# リンティング・フォーマット
uv run ruff check src/
uv run ruff format src/

# 型チェック
uv run mypy src/

# テスト実行
uv run pytest -v
```

全てパスしてから PR を作成してください。

## コーディング規約

- **Python 3.8+** 対応
- **型ヒント必須** (`mypy --strict` に近い設定でチェック)
- **Ruff** によるフォーマット・リンティング準拠
- **Google/NumPyスタイル** のドックストリング
- 公開APIには必ず型注釈とドックストリングを付与

## アーキテクチャ指針

### 新しい言語パーサーを追加する場合
1. `src/project_code_map/parser/` に `base.py` を継承したパーサーを実装
2. `tree-sitter-<language>` を依存に追加
3. `parser/__init__.py` のレジストリに登録
4. テストケースを `tests/parser/test_<language>.py` に追加

### 新しい出力フォーマッタを追加する場合
1. `src/project_code_map/formatters/` にフォーマッタクラスを実装
2. `formatters/__init__.py` のレジストリに登録
3. CLI の `--format` 選択肢に追加

## テスト指針

- **単体テスト**: 各パーサー・フォーマッタ・スキャナの独立した挙動
- **統合テスト**: CLI エントリーポイントからのエンドツーエンド
- **フィクスチャ**: `tests/fixtures/` にサンプルプロジェクトを配置
- **スナップショットテスト**: 出力形式の差分検知に活用

## コミットメッセージ規約

[Conventional Commits](https://www.conventionalcommits.org/) に準拠：

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`, `ci`

例:
```
feat(parser): add TypeScript support via tree-sitter-typescript

- Implement TypeScriptParser class
- Register in parser registry
- Add fixture and snapshot tests

Closes #42
```

## リリースプロセス (メンテナ向け)

1. `CHANGELOG.md` を更新
2. バージョン更新: `uv version [major|minor|patch]`
3. タグ作成: `git tag v$(uv version --short)`
4. `git push --tags` で GitHub Actions が PyPI 公開を実行

## 質問・相談

- 技術的な質問: **GitHub Discussions** または Issue で
- セキュリティ問題: **非公開で** メンテナに直接報告 (`security@ayato-labs.com`)

---

**初めてのコントリビューション歓迎します！**  
"Good first issue" ラベルが付いた Issue から始めるのがおすすめです。