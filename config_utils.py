import json
import os
import pandas as pd

# アプリのバージョン定数 (ここを Single Source of Truth にする)
VERSION = "1.1.1"
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "version": VERSION, # 設定データとしても持たせておく
    "server_name": "0.0.0.0",
    "server_port": 7867,
    "comfy_url": "http://127.0.0.1:8188",
    "workflow_file": "anima-t2i.json",
    "launch_bat": "",
    "DEEPL_API_KEY": "",
    "default_negative_prompt": "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, extra arms, extra legs, bad anatomy, missing limb, bad hands, extra fingers, extra digits, bad fingers, bad legs, extra legs, bad feet, ",
    "quality_tags_list": [
        "masterpiece", "best quality", "good quality", "normal quality",
        "score_9", "score_8", "score_7", "score_6", "score_5", "score_4"
    ],
    "default_quality_tags": ["masterpiece", "best quality", "score_9", "score_8", "score_7"],
    "safety_tags_list": ["safe", "sensitive", "nsfw", "explicit"],
    "default_safety_tags": ["safe"],
    "resolution_presets": {
        "1024x1024": [1024, 1024],
        "1152x896": [1152, 896],
        "896x1152": [896, 1152]
    },
    "default_resolution": "1152x896"
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                config.update(user_config)
                # ファイル側のバージョンが古くても、定数側を優先して表示させたい場合はここで更新
                config["version"] = VERSION 
        except Exception as e:
            print(f"Config load error: {e}")
    return config

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Config save error: {e}")
        return False

def update_and_save_config(url, bat_path, q_tags_str, s_tags_str, res_df, neg_prompt):
    config = load_config()
    config["comfy_url"] = url
    config["launch_bat"] = bat_path
    config["default_negative_prompt"] = neg_prompt
    config.update({
        "quality_tags_list": [t.strip() for t in q_tags_str.split(",") if t.strip()],
        "safety_tags_list": [t.strip() for t in s_tags_str.split(",") if t.strip()]
    })
    
    new_res = {}
    for _, row in res_df.iterrows():
        name = str(row["Name"]).strip()
        if name and row["Width"] and row["Height"]:
            try:
                new_res[name] = [int(row["Width"]), int(row["Height"])]
            except (ValueError, TypeError):
                continue
    config["resolution_presets"] = new_res
    return save_config(config)