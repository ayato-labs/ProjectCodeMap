@echo off
rem 文字コードをUTF-8に設定（日本語の文字化け対策）
chcp 65001 >nul

set VENV_DIR=.venv

rem 仮想環境の存在チェック
if not exist %VENV_DIR% (
    echo 【エラー】仮想環境（%VENV_DIR%）が見つかりません。
    echo 先に setup.bat を実行して環境を構築してください。
    pause
    exit /b 1
)

echo ==================================================
echo  🗺️  ProjectCodeMap を起動しています...
echo ==================================================

rem 仮想環境をアクティベートして、pyproject.tomlで定義したCLIコマンドを実行
call %VENV_DIR%\Scripts\activate
project-code-map

pause