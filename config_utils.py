import json
import os
import pandas as pd

# アプリのバージョン定数
APP_NAME = "Anima T2I WebUI"
VERSION = "2.0.0" # Update Version
CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "version": VERSION,
    "app_name": APP_NAME,
    "server_name": "0.0.0.0",
    "server_port": 7861,
    "comfy_url": "http://127.0.0.1:8188",
    "workflow_file": "anima-t2i.json",
    "launch_bat": "",
    "comfy_output_dir": "", # 【追加】ComfyUIの本来のOutputパスを明示指定
    "backup_output_dir": "", 
    "DEEPL_API_KEY": "",
    "default_negative_prompt": "worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, extra arms, extra legs, bad anatomy, missing limb, bad hands, extra fingers, extra digits, bad fingers, bad legs, extra legs, bad feet, ",
    "quality_tags_list": ["masterpiece", "best quality", "good quality", "normal quality", "score_9", "score_8", "score_7", "score_6", "score_5", "score_4"],
    "default_quality_tags": ["masterpiece", "best quality", "score_9", "score_8", "score_7"],
    "decade_tags_list": ["2020s", "2010s", "2000s", "1990s", "1980s"],
    "default_decade_tags": [],
    "time_period_tags_list": ["newest", "recent", "mid", "early", "old"],
    "default_time_period_tags": [],
    "meta_tags_list": ["highres", "absurdres", "anime screenshot", "jpeg artifacts", "official art"],
    "default_meta_tags": [],
    "safety_tags_list": ["safe", "sensitive", "nsfw", "explicit"],
    "default_safety_tags": ["safe"],
    "custom_tags_list": ["1girl","dynamic pose", "cinematic lighting", "high contrast", "vibrant colors"],
    "default_custom_tags": [],
    "resolution_presets": {
        "1024x1024": [1024, 1024],
        "1152x896": [1152, 896],
        "896x1152": [896, 1152],
        "1536x1536 (1:1)": [1536, 1536],
        "1792x1344 (4:3)": [1792, 1344],
        "1344x1792 (3:4)": [1344, 1792],
        "1920x1280 (3:2)": [1920, 1280],
        "1280x1920 (2:3)": [1280, 1920],
        "2048x1152 (16:9)": [2048, 1152],
        "1152x2048 (9:16)": [1152, 2048]
    },
    "default_resolution": "1152x896",
    "cfg_steps_presets": {
        "Standard": [4.0, 30],
        "Fast (LCM/Turbo)": [1.0, 12],
        "High Detail": [7.0, 50],
        "Creative": [8.0, 40]
    },
    "default_cfg_steps": "Standard",
    "tags_csv_path": "danbooru_tags.csv",
    "external_link_name": "Catbox.moe",
    "external_link_url": "https://catbox.moe/"
}

def load_config():
    config = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # 既存の設定を読み込む際、辞書項目（プリセット類）はマージする
                for key, value in user_config.items():
                    if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                        merged_dict = config[key].copy()
                        merged_dict.update(value)
                        config[key] = merged_dict
                    else:
                        config[key] = value
        except Exception:
            pass
    return config

def save_config(config_data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        return True
    except:
        return False

# 【修正】引数に real_out_path を追加
def update_and_save_config_v2(
    url, bat_path, backup_path, real_out_path, workflow_file,
    q_list, q_def, d_list, d_def, t_list, t_def, m_list, m_def, s_list, s_def, c_list, c_def, tags_path,
    res_df, cfg_steps_df, neg_prompt, ext_name, ext_url, server_port
):
    try:
        config = load_config()
        
        config["comfy_url"] = url
        config["launch_bat"] = bat_path
        config["backup_output_dir"] = backup_path
        config["comfy_output_dir"] = real_out_path # 【追加】
        config["workflow_file"] = workflow_file
        config["tags_csv_path"] = tags_path
        config["default_negative_prompt"] = neg_prompt
        config["external_link_name"] = ext_name
        config["external_link_url"] = ext_url
        config["server_port"] = int(server_port)
        
        config["quality_tags_list"] = q_list
        config["default_quality_tags"] = q_def
        config["decade_tags_list"] = d_list
        config["default_decade_tags"] = d_def
        config["time_period_tags_list"] = t_list
        config["default_time_period_tags"] = t_def
        config["meta_tags_list"] = m_list
        config["default_meta_tags"] = m_def
        config["safety_tags_list"] = s_list
        config["default_safety_tags"] = s_def
        config["custom_tags_list"] = c_list
        config["default_custom_tags"] = c_def
        
        new_res = {}
        for _, row in res_df.iterrows():
            new_res[row["Name"]] = [int(row["Width"]), int(row["Height"])]
        config["resolution_presets"] = new_res
        
        new_cfg_steps = {}
        for _, row in cfg_steps_df.iterrows():
            new_cfg_steps[row["Name"]] = [float(row["CFG"]), int(row["Steps"])]
        config["cfg_steps_presets"] = new_cfg_steps
        
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
            
        return True
    except Exception as e:
        print(f"Error saving config: {e}")
        return False