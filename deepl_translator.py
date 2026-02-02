import gradio as gr
import deepl
import json
import os

# --- 設定ファイルの管理 ---
CONFIG_FILE = "config.json"

def load_config():
    """config.jsonから設定を読み込む"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        default_config = {"DEEPL_API_KEY": ""}
        save_config(default_config)
        return default_config

def save_config(config_data):
    """config.jsonに設定を保存する"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)

config = load_config()

def translate_prompt(text):
    if not text:
        return ""
    current_config = load_config()
    api_key = current_config.get("DEEPL_API_KEY", "")

    if not api_key or "ここに" in api_key:
        return "Error: APIキーが設定されていません。"

    try:
        translator = deepl.Translator(api_key)
        result = translator.translate_text(text, target_lang="EN-US")
        return result.text
    except Exception as e:
        return f"Error: {str(e)}"

def update_api_key(new_key):
    config["DEEPL_API_KEY"] = new_key
    save_config(config)
    return f"APIキーを保存しました: {new_key[:4]}****"

# --- UIモジュール部分 (レイアウト変更版) ---

def create_translation_ui():
    """翻訳メイン UI (API設定を含まない)"""
    with gr.Column():
        gr.Markdown("### 🇯🇵→🇺🇸 DeepL Prompt Bridge")
        
        input_ja = gr.Textbox(
            label="日本語プロンプト", 
            placeholder="ここに日本語を入力...", 
            lines=3
        )
        output_en = gr.Textbox(
            label="翻訳結果（英文）", 
            lines=3, 
            interactive=False,
        )
        
        with gr.Row():
            clear_btn = gr.Button("クリア", variant="secondary")
            translate_btn = gr.Button("翻訳実行", variant="primary")
        
        # イベント紐付け
        translate_btn.click(fn=translate_prompt, inputs=[input_ja], outputs=[output_en])
        clear_btn.click(
            fn=lambda: ("", ""),
            inputs=None,
            outputs=[input_ja, output_en]
        )
    
    return input_ja, output_en

def create_api_key_ui():
    """APIキー設定専用の UI"""
    with gr.Accordion("APIキー設定", open=False):
        key_input = gr.Textbox(
            label="DeepL API Key", 
            value=config.get("DEEPL_API_KEY", ""),
            type="password"
        )
        save_btn = gr.Button("キーを保存して更新", variant="secondary", size="sm")
        status_msg = gr.Markdown("")
        
        save_btn.click(fn=update_api_key, inputs=[key_input], outputs=[status_msg])