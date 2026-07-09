@echo off
chcp 65001 >nul

echo ==================================================
echo  仮想環境のデリート＆インサートを開始します (uv直置き版)
echo ==================================================

set VENV_DIR=.venv

where uv >nul 2>nul
if errorlevel 1 (
    echo 【エラー】uv コマンドが見つかりません。
    pause
    exit /b 1
)

if exist %VENV_DIR% (
    echo [1/2] 既存の仮想環境（%VENV_DIR%）を削除中...
    rmdir /s /q %VENV_DIR%
)

echo [2/2] uv を使って新しい仮想環境を作成＆ライブラリをインストール中...
uv venv %VENV_DIR%
if errorlevel 1 (
    echo 【エラー】仮想環境の作成に失敗しました。
    pause
    exit /b 1
)

rem 依存ライブラリ（pathspec）を仮想環境にインストール
uv pip install pathspec

rem プロジェクト自体を編集可能モードでインストール（CLIコマンドを登録）
uv pip install -e .

echo ==================================================
echo  セットアップが完了しました！
echo  run.bat を実行してツールを起動してください。
echo ==================================================
pause