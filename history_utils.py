# history_utils.py
import json
import os

def get_history_path(config):
    # config.json に "history_file_path" の指定があればそれを使用
    # なければアプリ直下の history.json を使う
    return config.get("history_file_path", "history.json")

def load_history(config):
    path = get_history_path(config)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def add_to_history(config, entry, img_info):
    """画像ファイルは作らず、ComfyUIへの参照と全設定値をJSONに記録する"""
    history = load_history(config)
    
    history_entry = entry.copy()
    comfy_url = config.get("comfy_url", "http://127.0.0.1:8188")
    
    # ギャラリー表示用のURLをComfyUIのAPI経由で作成
    filename = img_info["filename"]
    subfolder = img_info["subfolder"]
    img_type = img_info["type"]
    history_entry["image"] = f"{comfy_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
    
    history.insert(0, history_entry)
    
    with open(get_history_path(config), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
    
    return history_entry

def clear_history(config):
    path = get_history_path(config)
    if os.path.exists(path):
        os.remove(path)