import gradio as gr
import deepl
import config_utils  # 共通ユーティリティをインポート

def translate_prompt(text, direction):
    """DeepLを使用してテキストを翻訳する"""
    if not text:
        return ""
        
    # 最新の設定を読み込む
    config = config_utils.load_config()
    api_key = config.get("DEEPL_API_KEY", "")

    if not api_key or "YOUR" in api_key or "ここに" in api_key:
        return "Error: APIキーが設定されていません。"

    target_lang = "EN-US" if direction == "JA -> EN" else "JA"

    try:
        translator = deepl.Translator(api_key)
        result = translator.translate_text(text, target_lang=target_lang)
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
    # 外部のアコーディオンで管理するため gr.Column のみ維持
    with gr.Column():
        direction_radio = gr.Radio(choices=["JA -> EN", "EN -> EN/JA (英→日)"], value="JA -> EN", label="Translation Direction")
        
        input_text = gr.Textbox(
            label="日本語プロンプト", 
            placeholder="ここに日本語を入力...", 
            lines=3
        )
        output_text = gr.Textbox(
            label="翻訳結果（英文）", 
            lines=3, 
            interactive=False,
        )
        
        with gr.Row():
            clear_btn = gr.Button("クリア", variant="secondary")
            translate_btn = gr.Button("翻訳実行", variant="primary")
        
        def update_labels(direction):
            if direction == "JA -> EN":
                return gr.update(label="日本語プロンプト", placeholder="ここに日本語を入力..."), gr.update(label="翻訳結果（英文）")
            else:
                return gr.update(label="English Prompt", placeholder="Enter English text here..."), gr.update(label="翻訳結果（日本語）")
                
        direction_radio.change(fn=update_labels, inputs=[direction_radio], outputs=[input_text, output_text])

        # イベント紐付け
        translate_btn.click(fn=translate_prompt, inputs=[input_text, direction_radio], outputs=[output_text])
        clear_btn.click(
            fn=lambda: ("", ""),
            inputs=None,
            outputs=[input_text, output_text]
        )
    
    return direction_radio, input_text, output_text

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