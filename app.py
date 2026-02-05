# app.py
import gradio as gr
from ui_layout import create_ui
import config_utils
import os

if __name__ == "__main__":
    # 1. 設定の読み込み
    config = config_utils.load_config()
    
    server_name = config.get("server_name")
    server_port = config.get("server_port")
    
    # 【v1.2.5】許可するパスのリストを作成
    allowed_paths = []
    
    # バックアップフォルダを許可リストに追加
    backup_dir = config.get("backup_output_dir")
    if backup_dir and os.path.exists(backup_dir):
        allowed_paths.append(backup_dir)
        
    # ComfyUIの本来のoutputフォルダも（バッチファイルの場所から推測して）追加
    bat_path = config.get("launch_bat")
    if bat_path:
        comfy_output = os.path.join(os.path.dirname(bat_path), "output")
        if os.path.exists(comfy_output):
            allowed_paths.append(comfy_output)

    # 起動ログの表示
    print(f"--- Starting Anima WebUI v{config_utils.VERSION} ---")
    print(f"Allowed Paths : {allowed_paths}") # デバッグ用
    print(f"Web UI URL     : http://localhost:{server_port}")
    print("------------------------------------------")

    # 2. UIの作成
    demo = create_ui(config)
    
    # 3. 起動 (allowed_paths を指定してセキュリティエラーを回避)
    demo.launch(
        server_name=server_name, 
        server_port=server_port,
        show_error=True,
        allowed_paths=allowed_paths, # ここが重要
        theme=gr.themes.Default(primary_hue="blue")
    )