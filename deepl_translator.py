import gradio as gr
import deepl
import config_utils  # 共通ユーティリティをインポート

def translate_prompt(text):
    """DeepLを使用してテキストを翻訳する"""
    if not text:
        return ""
        
    # 最新の設定を読み込む
    config = config_utils.load_config()
    api_key = config.get("DEEPL_API_KEY", "")

    if not api_key or "YOUR" in api_key or "ここに" in api_key:
        return "Error: APIキーが設定されていません。"

    try:
        translator = deepl.Translator(api_key)
        result = translator.translate_text(text, target_lang="EN-US")
        return result.text
    except Exception as e:
        return f"Error: {str(e)}"

def update_api_key(new_key):
    """APIキーを共通設定ファイルに保存する"""
    config = config_utils.load_config()
    config["DEEPL_API_KEY"] = new_key
    
    if config_utils.save_config(config):
        return f"✅ APIキーを保存しました: {new_key[:4]}****"
    else:
        return "❌ 保存に失敗しました"

# --- UIモジュール部分 ---

def create_translation_ui():
    """翻訳メイン UI (日本語入力と翻訳結果表示)"""
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
    """APIキー設定専用の UI (アコーディオン内)"""
    config = config_utils.load_config()
    
    with gr.Accordion("APIキー設定", open=False):
        key_input = gr.Textbox(
            label="DeepL API Key", 
            value=config.get("DEEPL_API_KEY", ""),
            type="password"
        )
        save_btn = gr.Button("キーを保存して更新", variant="secondary", size="sm")
        status_msg = gr.Markdown("")
        
        save_btn.click(fn=update_api_key, inputs=[key_input], outputs=[status_msg])