# app.py
import gradio as gr
from ui_layout import create_ui
import config_utils

if __name__ == "__main__":
    # 1. 設定の読み込み
    config = config_utils.load_config()
    
    server_name = config.get("server_name")
    server_port = config.get("server_port")
    
    # 起動ログの表示
    print("--- Starting Anima WebUI ---")
    print(f"Target ComfyUI: {config.get('comfy_url')}")
    print(f"Workflow file : {config.get('workflow_file')}")
    print(f"Web UI URL     : http://localhost:{server_port}")
    print("------------------------------------------")

    # 2. UIの作成 (ui_layout.py側で title 引数を Blocks に記述している前提)
    demo = create_ui(config)
    
    # 3. 起動 (Gradio 6.0 規約: theme は必ず launch() 内に記述)
    demo.launch(
        server_name=server_name, 
        server_port=server_port,
        show_error=True,
        theme=gr.themes.Default(primary_hue="blue")
    )