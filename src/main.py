import os
import argparse
from pathlib import Path
import pathspec

import tree_sitter_python
import tree_sitter_php
from tree_sitter import Language, Parser, Query, QueryCursor


# ── 言語設定 ──────────────────────────────────────────
# 拡張子 -> (言語ローダー, tree-sitter クエリ)
# クエリで @name にマッチしたノードが関数名として抽出される
_LANG_CONFIG = {
    ".py": (
        lambda: Language(tree_sitter_python.language()),
        "(function_definition name: (identifier) @name)",
    ),
    ".php": (
        lambda: Language(tree_sitter_php.language_php()),
        "(function_definition name: (name) @name) (method_declaration name: (name) @name)",
    ),
}

# (Language, Query, Parser) のキャッシュ（言語ごとに1つずつ）
_lang_cache = {}

def _get_lang_resources(ext):
    if ext not in _lang_cache:
        config = _LANG_CONFIG.get(ext)
        if not config:
            return None
        lang_loader, query_str = config
        lang = lang_loader()
        parser = Parser(lang)
        query = Query(lang, query_str)
        _lang_cache[ext] = (lang, query, parser)
    return _lang_cache[ext]


def load_gitignore(root_path: Path):
    """ .gitignore を読み込んで pathspec オブジェクトを返す """
    gitignore_path = root_path / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
        # 空行やコメント（#）を除外したルールを作成
        return pathspec.PathSpec.from_lines("gitwildmatch", lines)
    return None

def extract_functions(file_path: Path) -> list:
    """ tree-sitter を使って関数名の一覧を抽出する """
    ext = file_path.suffix.lower()
    resources = _get_lang_resources(ext)
    if resources is None:
        return []
    _, query, parser = resources
    try:
        with open(file_path, "rb") as f:
            code = f.read()
        tree = parser.parse(code)
        cursor = QueryCursor(query)
        captures = cursor.captures(tree.root_node)
        names = []
        for cap_name, nodes in captures.items():
            for node in nodes:
                if node.text:
                    names.append(node.text.decode("utf-8"))
        return names
    except Exception:
        return ["解析エラー"]

def scan_directory(target_dir_str: str):
    target_path = Path(target_dir_str).resolve()
    if not target_path.exists() or not target_path.is_dir():
        print(f"エラー: 指定されたディレクトリが見つかりません: {target_path}")
        return

    # ルートの.gitignoreを読み込む
    spec = load_gitignore(target_path)
    result = [f"[プロジェクト構造と関数一覧] 対象パス: {target_path}"]

    # 💡 常に除外したいログフォルダ名のセット
    exclude_log_dirs = {"log", "logs", ".logs"}

    # os.walkで全探索
    for root, dirs, files in os.walk(target_path):
        current_dir_path = Path(root)
        
        # 1. ディレクトリ全体の除外判定
        # 💡 [変更] .gitなどのドット開始フォルダに加え、log/logs/.logsフォルダを常に除外
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in exclude_log_dirs]
        
        # .gitignore がある場合はさらにフィルタリング
        if spec:
            dirs[:] = [
                d for d in dirs 
                if not spec.match_file(str((current_dir_path / d).relative_to(target_path)) + "/")
            ]

        # 階層（インデント）の計算
        rel_path = current_dir_path.relative_to(target_path)
        level = 0 if rel_path == Path(".") else len(rel_path.parts)
        
        if level > 0:
            result.append(f"{'  ' * level}- {current_dir_path.name}/")

        # 2. ファイルの除外判定と関数抽出
        for file in files:
            file_path = current_dir_path / file
            rel_file_str = str(file_path.relative_to(target_path))

            # .gitignoreにマッチするファイルはスキップ
            if spec and spec.match_file(rel_file_str):
                continue

            # 関数解析可能な言語（_LANG_CONFIG に登録済み）のみ関数抽出を行う
            file_prefix = "  " * (level + 1)
            _, ext = os.path.splitext(file)
            if ext.lower() in _LANG_CONFIG:
                funcs = extract_functions(file_path)
                if funcs:
                    result.append(f"{file_prefix}- {file} (関数: {', '.join(funcs)})")
                else:
                    result.append(f"{file_prefix}- {file} (関数なし)")
            else:
                # テキストファイルや設定ファイルなども構造維持のために出力
                result.append(f"{file_prefix}- {file}")

    return "\n".join(result)


def main():
    """CLIエントリーポイント用のメイン関数"""
    import sys
    print("==================================================")
    print("      [ProjectCodeMap] へようこそ", flush=True)
    print("==================================================")
    
    user_input = input("解析したいフォルダの絶対パスを入力してください:\n> ")
    target_directory = user_input.strip().strip('"').strip("'")
    
    if not target_directory:
        print("【ProjectCodeMap】エラー: パスが入力されませんでした。処理を中断します。")
    else:
        output_text = scan_directory(target_directory)
        if output_text:
            print(output_text)
            output_filename = "project_code_map_output.txt"
            with open(output_filename, "w", encoding="utf-8") as out:
                out.write(output_text)
            print(f"\n[ProjectCodeMap] 完了！ 結果を '{output_filename}' に保存しました。")

# コマンドラインから直接スクリプトとして叩かれた場合にも動くようにする
if __name__ == "__main__":
    main()
