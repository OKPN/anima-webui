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

    # 拡張子を除いたベース名を取得 (例: "sample")
    basename = os.path.splitext(filename)[0]
    # 試行する拡張子のリスト
    exts = [os.path.splitext(filename)[1], ".jxl", ".webp", ".png", ".jpg"]

    # 探索先リスト
    search_dirs = []
    bat_path = config.get("launch_bat", "")
    if bat_path:
        search_dirs.append(os.path.join(os.path.dirname(bat_path), "output", subfolder))
    
    backup_dir = config.get("backup_output_dir", "")
    if backup_dir:
        search_dirs.append(backup_dir)

    # 冗長検索: 各ディレクトリで、各拡張子を試す
    for d in search_dirs:
        if not os.path.exists(d): continue
        for e in exts:
            if not e: continue
            target = os.path.join(d, basename + e)
            if os.path.exists(target):
                return target # 最初に見つかった形式を返す

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

def delete_history_entry(config, index):
    """
    指定されたインデックスの履歴エントリと、その物理画像ファイルを同時に削除する
    """
    history = load_history(config) #
    if 0 <= index < len(history):
        item = history[index]
        
        # 1. 物理ファイルの特定と削除
        img_path = resolve_image_path(item, config) #
        # URL(http://...) ではなくローカルパスが返ってきた場合のみ削除を実行
        if img_path and os.path.exists(img_path) and not img_path.startswith("http"):
            try:
                os.remove(img_path)
                print(f"🗑️ Physical file deleted: {img_path}")
            except Exception as e:
                print(f"❌ Failed to delete file: {e}")

        # 2. JSON からエントリを削除
        history.pop(index)
        
        # 3. 履歴ファイルを更新
        path = get_history_path(config) #
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        return history
    return None