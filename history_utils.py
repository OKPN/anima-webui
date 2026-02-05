import json
import os
import urllib.parse
import shutil
import datetime # 【追加】時刻取得用

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

def resolve_image_path(item, config):
    """
    画像が ComfyUI の output にあれば URL を返し、
    移動済み（Nextcloud等）ならローカルパスを返すフォールバック関数
    """
    img_url = item.get("image", "")
    if not img_url: return None

    # URLからファイル名とサブフォルダを抽出
    parsed = urllib.parse.urlparse(img_url)
    params = urllib.parse.parse_qs(parsed.query)
    filename = params.get("filename", [None])[0]
    subfolder = params.get("subfolder", [""])[0]

    if not filename: return img_url

    # 1. ComfyUI 本体の output フォルダを launch_bat から推測
    bat_path = config.get("launch_bat", "")
    if bat_path:
        comfy_dir = os.path.dirname(bat_path)
        # ComfyUIの構造に合わせて 'output' フォルダを探す
        original_file_path = os.path.join(comfy_dir, "output", subfolder, filename)
        
        # 物理的に存在すれば API URL のまま返す
        if os.path.exists(original_file_path):
            return img_url

    # 2. 本来の場所にない場合、Nextcloud 側のバックアップフォルダを探す
    backup_dir = config.get("backup_output_dir", "C:/Nextcloud/Anima_Backup") # 要設定
    backup_file_path = os.path.join(backup_dir, filename) # 移動時はフラットに保存する前提
    
    if os.path.exists(backup_file_path):
        # 見つかればローカルパスを返す (Gradioは直接読み込み可能)
        return backup_file_path

    # 3. どこにもなければそのままの URL (表示はエラーになる) を返す
    return img_url

# ...既存の add_to_history 等...

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

def backup_history(config):
    """
    履歴を削除せずに、タイムスタンプ付きのバックアップを作成する
    """
    path = get_history_path(config)
    if os.path.exists(path):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{path}.{timestamp}.bak"
            shutil.copy2(path, backup_path)
            return backup_path
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return None
    return None

def clear_history(config):
    """
    タイムスタンプ付きでバックアップを作成してから履歴を削除する安全な実装
    """
    path = get_history_path(config)
    if os.path.exists(path):
        try:
            # backup_historyを再利用して安全性を確保
            backup_path = backup_history(config)
            if backup_path:
                os.remove(path)
                print(f"✅ History cleared. Backup created: {backup_path}")
                return True
        except Exception as e:
            print(f"❌ Error during clearing history: {e}")
            return False
    return False