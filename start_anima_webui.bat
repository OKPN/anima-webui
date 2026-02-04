@echo off
:: 冒頭のエラー表示を消去し、パス移動の警告を抑制 [cite: 1]
cls
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d %~dp0 2>nul [cite: 1]

:: --- 設定エリア ---
set VENV_NAME=venv
set PYTHON_SCRIPT=app.py
:: ------------------

title Anima WebUI Launcher

echo ========================================================
echo    Anima WebUI 起動ツール
echo ========================================================

:: 1. 仮想環境のチェック [cite: 1]
if exist "%VENV_NAME%" (
    echo [INFO] 仮想環境が見つかりました。起動準備をします...
    goto :START_APP
)

echo [INFO] 初回起動: 仮想環境を作成しています...
python -m venv %VENV_NAME%
if errorlevel 1 goto :ERROR_PYTHON 

echo [INFO] ライブラリをインストールしています (初回のみ)...
"%VENV_NAME%\Scripts\python.exe" -m pip install --upgrade pip
echo [INFO] 必要なパッケージをインストール中: gradio, requests, Pillow, deepl...
"%VENV_NAME%\Scripts\pip.exe" install -r requirements.txt

echo.
echo [INFO] 環境構築完了！ [cite: 5]

:START_APP
:: 2. アプリケーションの起動 [cite: 2]
echo.
echo [START] 仮想環境を使って %PYTHON_SCRIPT% を起動します... [cite: 2]
echo --------------------------------------------------------
echo ※ 終了するにはこの画面を閉じるか、Ctrl+C を押してください。
echo.
"%VENV_NAME%\Scripts\python.exe" %PYTHON_SCRIPT% [cite: 3]

if errorlevel 1 goto :ERROR_APP

echo.
echo アプリケーションを正常に終了しました。
pause
exit

:ERROR_PYTHON
echo.
echo --------------------------------------------------------
echo [ERROR] Python が見つからないか、実行に失敗しました。
echo.
echo ▼ 対処方法: [cite: 4]
echo 1. Python 3.12 がインストールされているか確認してください。 [cite: 4]
echo 2. 未インストールの場合は、公式サイトから 3.12.x を入手してください。 [cite: 4]
echo    URL: https://www.python.org/downloads/windows/ [cite: 4]
echo.
echo ★重要★ [cite: 5]
echo インストーラー実行時、画面下の [cite: 5]
echo [Add Python to PATH] に必ずチェックを入れてください。 [cite: 5]
echo --------------------------------------------------------
pause
exit

:ERROR_APP
echo.
echo [ERROR] アプリが異常終了しました。
echo 上記のエラーメッセージを確認してください。
pause
exit