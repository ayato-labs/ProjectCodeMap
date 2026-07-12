"""ProjectCodeMap 基本テスト"""

import tempfile
from pathlib import Path

import pytest

from project_code_map import scan_project
from project_code_map.config import Config


def test_scan_simple_project():
    """シンプルなプロジェクトのスキャンテスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # テスト用ファイル作成
        (root / "main.py").write_text(
            '''
def hello(name: str) -> str:
    """挨拶を返す"""
    return f"Hello, {name}!"

class Greeter:
    def greet(self, name: str) -> str:
        return f"Hi, {name}"

async def async_hello(name: str) -> str:
    return f"Hello async, {name}"
''',
            encoding="utf-8",
        )

        (root / "utils.py").write_text(
            '''
def helper(x: int) -> int:
    return x * 2
''',
            encoding="utf-8",
        )

        # サブディレクトリ
        subdir = root / "sub"
        subdir.mkdir()
        (subdir / "inner.py").write_text(
            "def inner_func() -> None:\n    pass\n",
            encoding="utf-8",
        )

        config = Config()
        project_map = scan_project(root, config)

        # 基本検証
        assert project_map.stats.total_files == 3
        assert project_map.stats.total_functions >= 4  # hello, greet, async_hello, helper, inner_func

        # 関数が正しく抽出されているか
        all_funcs = project_map.root.all_functions
        func_names = {f.name for f in all_funcs}
        assert "hello" in func_names
        assert "greet" in func_names
        assert "async_hello" in func_names
        assert "helper" in func_names
        assert "inner_func" in func_names


def test_gitignore_exclusion():
    """.gitignore による除外テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "main.py").write_text("def main(): pass\n")
        (root / "ignored.py").write_text("def ignored(): pass\n")
        (root / ".gitignore").write_text("ignored.py\n")

        config = Config(respect_gitignore=True)
        project_map = scan_project(root, config)

        assert project_map.stats.total_files == 1
        func_names = {f.name for f in project_map.root.all_functions}
        assert "main" in func_names
        assert "ignored" not in func_names


def test_pcmignore_exclusion():
    """.pcmignore による除外テスト"""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        (root / "main.py").write_text("def main(): pass\n")
        (root / "secret.py").write_text("def secret(): pass\n")
        (root / ".pcmignore").write_text("secret.py\n")

        config = Config()
        project_map = scan_project(root, config)

        assert project_map.stats.total_files == 1
        func_names = {f.name for f in project_map.root.all_functions}
        assert "main" in func_names
        assert "secret" not in func_names


def test_format_text():
    """Text フォーマッタのテスト"""
    from project_code_map.formatters import get_formatter, FormatType

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("def test(): pass\n")

        config = Config()
        project_map = scan_project(root, config)

        formatter = get_formatter(FormatType.TEXT)
        output = formatter.format(project_map, config)

        assert "test.py" in output
        assert "test" in output


def test_format_json():
    """JSON フォーマッタのテスト"""
    from project_code_map.formatters import get_formatter, FormatType
    import json

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("def test(): pass\n")

        config = Config()
        project_map = scan_project(root, config)

        formatter = get_formatter(FormatType.JSON)
        output = formatter.format(project_map, config)

        data = json.loads(output)
        assert data["stats"]["total_files"] == 1
        assert len(data["functions"]) == 1
        assert data["functions"][0]["functions"][0]["name"] == "test"


def test_format_xml():
    """XML フォーマッタのテスト"""
    from project_code_map.formatters import get_formatter, FormatType
    import xml.etree.ElementTree as ET

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("def test(): pass\n")

        config = Config()
        project_map = scan_project(root, config)

        formatter = get_formatter(FormatType.XML)
        output = formatter.format(project_map, config)

        xml_root = ET.fromstring(output)
        assert xml_root.tag == "project_map"
        assert xml_root.find(".//function[@name='test']") is not None


def test_format_aider():
    """Aider フォーマッタのテスト"""
    from project_code_map.formatters import get_formatter, FormatType

    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "test.py").write_text("def test(): pass\n")

        config = Config()
        project_map = scan_project(root, config)

        formatter = get_formatter(FormatType.AIDER)
        output = formatter.format(project_map, config)

        assert "test.py:" in output
        assert "  test" in output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])