@echo off
chcp 65001 > nul
title Irodori-TTS 起動バッチ

cd /d "%~dp0"

echo TTS API を起動しています...
start "TTS API" cmd /k "uv run uvicorn api:app --host 0.0.0.0 --port 8000"

echo Gradio UI を起動しています...
start "Gradio UI" cmd /k "uv run python gradio_app_voicedesign.py --server-name 0.0.0.0 --server-port 7868"

echo 両方のサーバーの起動コマンドを送信しました。
pause
