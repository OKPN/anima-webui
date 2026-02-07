import json
import os
import urllib.parse
import shutil
import datetime
from PIL import Image

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
    img_url = item.get("image", "")
    if not img_url: return None

    parsed = urllib.parse.urlparse(img_url)
    params = urllib.parse.parse_qs(parsed.query)
    
    filename = params.get("filename", [None])[0]
    subfolder = params.get("subfolder", [""])[0]
    
    if not filename: return img_url

    basename = os.path.splitext(filename)[0]
    exts = [os.path.splitext(filename)[1], ".png", ".jpg", ".webp", ".jxl"]

    search_dirs = []
    
    # 1. バックアップフォルダ
    backup_dir = config.get("backup_output_dir", "")
    if backup_dir and os.path.exists(backup_dir):
        search_dirs.append(backup_dir)
        if subfolder:
            search_dirs.append(os.path.join(backup_dir, subfolder))

    # 2. ComfyUI Output (Batchファイルからの推測)
    bat_path = config.get("launch_bat", "")
    if bat_path:
        comfy_base = os.path.dirname(bat_path)
        output_dir = os.path.join(comfy_base, "output")
        if os.path.exists(output_dir):
            if subfolder:
                search_dirs.append(os.path.join(output_dir, subfolder))
            else:
                search_dirs.append(output_dir)

    # 3. 【追加】ComfyUI Output (明示的設定)
    real_out_path = config.get("comfy_output_dir", "")
    if real_out_path and os.path.exists(real_out_path):
        if subfolder:
            search_dirs.append(os.path.join(real_out_path, subfolder))
        else:
            search_dirs.append(real_out_path)

    # 走査実行
    for d in search_dirs:
        if not os.path.exists(d): continue
        for e in exts:
            if not e: continue
            target = os.path.join(d, basename + e)
            if os.path.exists(target): return target
            
            target_exact = os.path.join(d, filename)
            if os.path.exists(target_exact): return target_exact

    return img_url

def get_thumbnail_dir():
    thumb_dir = "thumbnails"
    if not os.path.exists(thumb_dir):
        os.makedirs(thumb_dir, exist_ok=True)
    return thumb_dir

def resolve_thumbnail_path(item, config):
    """ギャラリー表示用にサムネイルのパスを解決する。なければ生成する。"""
    full_path = resolve_image_path(item, config)
    
    # ローカルファイルでない、または存在しない場合はそのまま返す
    if not full_path or not isinstance(full_path, str) or not os.path.exists(full_path):
        return full_path
    
    # HTTP URLならそのまま返す
    if full_path.startswith("http"): return full_path

    thumb_dir = get_thumbnail_dir()
    filename = os.path.basename(full_path)
    name, _ = os.path.splitext(filename)
    thumb_filename = f"thumb_{name}.webp"
    thumb_path = os.path.join(thumb_dir, thumb_filename)
    
    if os.path.exists(thumb_path):
        return thumb_path
        
    try:
        with Image.open(full_path) as img:
            img.thumbnail((350, 350))
            img.save(thumb_path, "WEBP", quality=80)
        return thumb_path
    except:
        return full_path

def add_to_history(config, entry, img_info, current_url, pil_image=None):
    history = load_history(config)
    history_entry = entry.copy()
    
    filename = img_info["filename"]
    subfolder = img_info["subfolder"]
    img_type = img_info["type"]
    
    base_url = str(current_url).strip().rstrip("/")
    # URLエンコード処理（スペースなどを安全にする）
    safe_filename = urllib.parse.quote(filename)
    safe_subfolder = urllib.parse.quote(subfolder)
    
    history_entry["image"] = f"{base_url}/view?filename={safe_filename}&subfolder={safe_subfolder}&type={img_type}"
    
    history.insert(0, history_entry)
    with open(get_history_path(config), "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4, ensure_ascii=False)
    
    # 生成直後のPIL画像がある場合は即座にサムネイルを作成
    if pil_image:
        try:
            thumb_dir = get_thumbnail_dir()
            name, _ = os.path.splitext(filename)
            thumb_path = os.path.join(thumb_dir, f"thumb_{name}.webp")
            img_copy = pil_image.copy()
            img_copy.thumbnail((350, 350))
            img_copy.save(thumb_path, "WEBP", quality=80)
        except Exception as e:
            print(f"⚠️ Thumbnail creation failed: {e}")
            
    return history_entry

def backup_history(config):
    path = get_history_path(config)
    if os.path.exists(path):
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{path}.{timestamp}.bak"
            shutil.copy2(path, backup_path)
            return True, f"Backup created: {backup_path}"
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            return False, f"Backup failed: {e}"
    return False, "History file not found."

def save_history_json(config, history):
    path = get_history_path(config)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"❌ Failed to save history: {e}")
        return False

def delete_history_entry(config, history, index):
    try:
        index = int(index)
    except:
        return history

    if 0 <= index < len(history):
        item = history[index]
        img_path = resolve_image_path(item, config)
        
        print(f"[DEBUG] Attempting to delete: {img_path}")

        if img_path and os.path.exists(img_path) and not str(img_path).lower().startswith("http"):
            try:
                os.remove(img_path)
                print(f"🗑️ Deleted image file: {img_path}")
                
                # サムネイルも削除
                thumb_dir = "thumbnails"
                fname = os.path.basename(img_path)
                name, _ = os.path.splitext(fname)
                thumb_path = os.path.join(thumb_dir, f"thumb_{name}.webp")
                if os.path.exists(thumb_path):
                    os.remove(thumb_path)
            except Exception as e:
                print(f"❌ Failed to delete image file: {e}")
        else:
            print(f"⚠️ Image file not found or is remote: {img_path}")

        history.pop(index)
        
        path = config.get("history_file_path", "history.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4, ensure_ascii=False)
            print("✅ History JSON updated.")
        except Exception as e:
            print(f"❌ Failed to save history JSON: {e}")
            
        return history
    return history

def clear_history(config):
    # (変更なし)
    path = config.get("history_file_path", "history.json")
    if os.path.exists(path):
        # バックアップ関数を呼ぶならここで呼ぶ
        try:
            os.remove(path)
            with open(path, "w", encoding="utf-8") as f:
                json.dump([], f)
            return True
        except:
            return False
    return False