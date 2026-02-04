import json
import os

def get_history_path(config):
    return config.get("history_file_path", "history.json")

def load_history(config):
    path = get_history_path(config)
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def add_to_history(config, entry, img_info, current_url):
    """
    current_url: UIから渡されたURLを使用し、空白を除去して保存
    """
    history = load_history(config)
    history_entry = entry.copy()
    
    # ComfyUIの画像を直接参照
    filename = img_info["filename"]
    subfolder = img_info["subfolder"]
    img_type = img_info["type"]
    
    # URLの空白を徹底的に除去し、末尾スラッシュもクリーニング
    base_url = str(current_url).strip().rstrip("/")
    history_entry["image"] = f"{base_url}/view?filename={filename}&subfolder={subfolder}&type={img_type}"
    
    history.insert(0, history_entry)
    with open(get_history_path(config), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
    return history_entry

def clear_history(config):
    path = get_history_path(config)
    if os.path.exists(path):
        os.remove(path)