import json
import os
from ui_layout import create_ui

CONFIG_FILE = "config.json"

# デフォルト設定
# app.py のデフォルト設定

DEFAULT_CONFIG = {
    "server_name": "0.0.0.0",
    "server_port": 7867,
    "comfy_url": "http://127.0.0.1:8188",
    "workflow_file": "anima-t2i.json"  # ここを変更
}

def load_config():
    """設定ファイルを読み込む"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                full_config = DEFAULT_CONFIG.copy()
                full_config.update(config)
                return full_config
        except Exception as e:
            print(f"Config load error: {e}")
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

if __name__ == "__main__":
    # 1. 設定の読み込み
    config = load_config()
    
    server_name = config.get("server_name", "0.0.0.0")
    server_port = config.get("server_port", 7865)
    
    print("--- Starting Qwen Image Edit Frontend ---")
    print(f"Target ComfyUI: {config.get('comfy_url')}")
    print(f"Workflow file : {config.get('workflow_file')}")
    print(f"Web UI URL     : http://localhost:{server_port}")
    print("------------------------------------------")

    # 2. UIの作成 (ui_layout.pyのcreate_uiを呼び出す)
    demo = create_ui(config)
    
    # 3. 起動
    demo.launch(
        server_name=server_name, 
        server_port=server_port,
        show_error=True
    )