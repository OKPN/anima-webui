import gradio as gr
from ui_layout import create_ui
import config_utils
import os
from fastapi import FastAPI, Request
from fastapi.responses import Response
import requests
import uvicorn
import json

app = FastAPI()
TTS_API_URL = "http://127.0.0.1:8000/generate-voice"

@app.post("/api/tts")
async def tts_proxy(request: Request):
    try:
        data = await request.json()
        res = requests.post(TTS_API_URL, json=data, timeout=120)
        res.raise_for_status()
        return Response(content=res.content, media_type="audio/wav")
    except Exception as e:
        return Response(content=json.dumps({"error": str(e)}), status_code=500, media_type="application/json")

if __name__ == "__main__":
    config = config_utils.load_config()
    server_name = config.get("server_name")
    server_port = config.get("server_port")
    
    allowed_paths = []
    
    # 1. バックアップフォルダ
    backup_dir = config.get("backup_output_dir")
    if backup_dir and os.path.exists(backup_dir):
        allowed_paths.append(backup_dir)
        
    # 2. ComfyUI Output (bat推測)
    bat_path = config.get("launch_bat")
    if bat_path:
        comfy_output = os.path.join(os.path.dirname(bat_path), "output")
        if os.path.exists(comfy_output):
            allowed_paths.append(comfy_output)

    # 3. 【追加】ComfyUI Output (明示的設定)
    real_out_path = config.get("comfy_output_dir")
    if real_out_path and os.path.exists(real_out_path):
        allowed_paths.append(real_out_path)

    print(f"--- Starting Anima WebUI v{config_utils.VERSION} ---")
    print(f"Allowed Paths : {allowed_paths}")
    print(f"Web UI URL     : http://localhost:{server_port}")
    print("------------------------------------------")

    # Gradioが外部からの画像読み込みを許可するパスを設定
    if allowed_paths:
        os.environ["GRADIO_ALLOWED_PATHS"] = ",".join(allowed_paths)

    demo = create_ui(config)
    
    # スマホからのアクセス時の通信安定化とタイムアウト防止のためにQueueを有効化
    demo.queue()
    
    gradio_app = gr.mount_gradio_app(app, demo, path="/")
    uvicorn.run(gradio_app, host=server_name, port=server_port)