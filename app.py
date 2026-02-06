import gradio as gr
from ui_layout import create_ui
import config_utils
import os

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

    demo = create_ui(config)
    
    demo.launch(
        server_name=server_name, 
        server_port=server_port,
        show_error=True,
        allowed_paths=allowed_paths,
        theme=gr.themes.Default(primary_hue="blue")
    )