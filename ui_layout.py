import gradio as gr
import ui_handlers
import deepl_translator
import system_manager
import config_utils
import comfy_utils
import history_utils 
import ui_javascript
import pandas as pd
from urllib.parse import urlparse
import requests
import os
import glob
import ai_chat_manager

def get_lora_list(config):
    """ComfyUIから利用可能なLoRAのリストを取得する。API経由を試み、失敗した場合はファイルシステムをスキャンする。"""
    loras = ["None"]
    bat_path = config.get("launch_bat")
    comfy_url = config.get("comfy_url", "").strip().rstrip("/")

    # 1. API経由での取得を試みる
    if comfy_url:
        try:
            response = requests.get(f"{comfy_url}/models/loras", timeout=2)
            response.raise_for_status()
            loras.extend(response.json())
            print("✅ LoRA list fetched from ComfyUI API.")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not fetch LoRA list from API ({e}), falling back to file scan.")
            # APIからの取得に失敗した場合、ファイルシステムスキャンにフォールバック
            if bat_path:
                base_dir = os.path.dirname(bat_path)
                possible_paths = [
                    os.path.join(base_dir, "models", "loras"),
                    os.path.join(base_dir, "ComfyUI", "models", "loras"),
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        files = glob.glob(os.path.join(p, "**", "*.safetensors"), recursive=True)
                        loras += [os.path.relpath(f, p) for f in files]
                        break
    
    # ユーザーリクエストに応じて候補を追加
    loras.append("wkamura.safetensors")
    return sorted(list(set(loras)))

def get_checkpoint_list(config):
    """ComfyUIから利用可能なCheckpointのリストを取得する。API経由を試み、失敗した場合はファイルシステムをスキャンする。"""
    ckpts = ["None"]
    bat_path = config.get("launch_bat")
    comfy_url = config.get("comfy_url", "").strip().rstrip("/")

    if comfy_url:
        try:
            response = requests.get(f"{comfy_url}/models/checkpoints", timeout=2)
            response.raise_for_status()
            ckpts.extend(response.json())
            print("✅ Checkpoint list fetched from ComfyUI API.")
        except requests.exceptions.RequestException as e:
            print(f"⚠️ Could not fetch Checkpoint list from API ({e}), falling back to file scan.")
            if bat_path:
                base_dir = os.path.dirname(bat_path)
                possible_paths = [
                    os.path.join(base_dir, "models", "checkpoints"),
                    os.path.join(base_dir, "ComfyUI", "models", "checkpoints"),
                    os.path.join(base_dir, "models", "diffusion_models"),
                    os.path.join(base_dir, "ComfyUI", "models", "diffusion_models"),
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        files = glob.glob(os.path.join(p, "**", "*.safetensors"), recursive=True)
                        ckpts += [os.path.relpath(f, p) for f in files]
    return sorted(list(set(ckpts)))

def get_controlnet_list(config):
    """ComfyUIから利用可能なControlNetのリストを取得する"""
    cn_models = ["None"]
    bat_path = config.get("launch_bat")
    comfy_url = config.get("comfy_url", "").strip().rstrip("/")

    if comfy_url:
        try:
            response = requests.get(f"{comfy_url}/models/controlnet", timeout=2)
            response.raise_for_status()
            cn_models.extend(response.json())
        except requests.exceptions.RequestException as e:
            if bat_path:
                base_dir = os.path.dirname(bat_path)
                possible_paths = [
                    os.path.join(base_dir, "models", "controlnet"),
                    os.path.join(base_dir, "ComfyUI", "models", "controlnet"),
                ]
                for p in possible_paths:
                    if os.path.exists(p):
                        files = glob.glob(os.path.join(p, "**", "*.safetensors"), recursive=True) + glob.glob(os.path.join(p, "**", "*.pth"), recursive=True)
                        cn_models += [os.path.relpath(f, p) for f in files]
                        break
    return sorted(list(set(cn_models)))

def update_lora_strength(name, current_str):
    """LoRA選択時に強度を自動調整する"""
    if name == "None":
        return 0.0
    if current_str == 0.0:
        return 1.0
    return current_str

def create_ui(config):
    # --- 1. 設定の取得 ---
    app_name = config.get("app_name", "Gradio")
    version = config_utils.VERSION
    RESOLUTION_PRESETS = config.get("resolution_presets", {})
    default_res_key = config.get("default_resolution", "1152x896")
    initial_res = RESOLUTION_PRESETS.get(default_res_key, [1152, 896])
    default_w, default_h = initial_res[0], initial_res[1]

    CFG_STEPS_PRESETS = config.get("cfg_steps_presets", {
        "Standard": [5.0, 30],
        "Fast (LCM/Turbo)": [2.0, 15],
        "High Detail": [7.0, 50]
    })
    default_cfg_steps_key = config.get("default_cfg_steps", "Standard")
    initial_cfg_steps = CFG_STEPS_PRESETS.get(default_cfg_steps_key, [5.0, 30])
    default_cfg, default_steps = initial_cfg_steps[0], initial_cfg_steps[1]

    quality_tags_list = config.get("quality_tags_list", [])
    default_quality_tags = config.get("default_quality_tags", [])
    decade_tags_list = config.get("decade_tags_list", [])
    default_decade_tags = config.get("default_decade_tags", [])
    time_period_tags_list = config.get("time_period_tags_list", [])
    default_time_period_tags = config.get("default_time_period_tags", [])
    meta_tags_list = config.get("meta_tags_list", [])
    default_meta_tags = config.get("default_meta_tags", [])
    safety_tags_list = config.get("safety_tags_list", [])
    default_safety_tags = config.get("default_safety_tags", [])
    custom_tags_list = config.get("custom_tags_list", [])
    default_custom_tags = config.get("default_custom_tags", [])
    
    ext_link_name = config.get("external_link_name", "Link")
    ext_link_url = config.get("external_link_url", "#")
    default_neg_prompt = config.get("default_negative_prompt", "")
    comfy_url = config.get("comfy_url", "")
    workflow_file = config.get("workflow_file")
    year_choices = [str(y) for y in range(2026, 1949, -1)]

    local_ip = system_manager.get_local_ip()
    detected_url = f"http://{local_ip}:8188"

    # LoRAリストの取得
    lora_files = get_lora_list(config)
    
    # Checkpointリストの取得
    ckpt_files = get_checkpoint_list(config)
    lllite_files = get_controlnet_list(config)
    
    # ワークフローからデフォルトのチェックポイント名（重みの名前）を取得
    default_ckpt, default_loras, default_lllite = comfy_utils.extract_default_settings(workflow_file, ckpt_files, lora_files, lllite_files)
    tone_config, default_llm_model = ai_chat_manager.load_chat_config()

    # --- 2. タグデータのロード (オートコンプリート用) ---
    tags_csv_path = config.get("tags_csv_path", "danbooru_tags.csv")
    autocomplete_tags = []
    artist_autocomplete_tags = []
    
    # デフォルトのサンプルタグ (CSVがない場合用)
    sample_tags = ["1girl", "solo", "long hair", "short hair", "blue eyes", "red eyes", "smile", "looking at viewer", "standing", "sitting", "masterpiece", "best quality"]
    artist_sample_tags = ["wkamura", "greg rutkowski", "artgerm"]
    
    # 設定されたパスが存在せず、カレントディレクトリに danbooru_tags.csv がある場合はそれを優先利用する
    if not os.path.exists(tags_csv_path) and os.path.exists("danbooru_tags.csv"):
        tags_csv_path = "danbooru_tags.csv"

    if os.path.exists(tags_csv_path):
        try:
            # ヘッダーなしCSVとして読み込み、列名を指定する
            df = pd.read_csv(tags_csv_path, header=None, names=["tag", "category", "count", "aliases"], on_bad_lines='skip', engine='python')
            autocomplete_tags = df["tag"].dropna().astype(str).tolist()
            # カテゴリーIDが 1 のものだけを抽出してアーティストタグリストを作成
            artist_autocomplete_tags = df[df["category"] == 1]["tag"].dropna().astype(str).tolist()
        except Exception as e:
            print(f"⚠️ Failed to load tags.csv: {e}")
            autocomplete_tags = sample_tags
            artist_autocomplete_tags = artist_sample_tags
    else:
        autocomplete_tags = sample_tags
        artist_autocomplete_tags = artist_sample_tags

    # 上位20000件程度に絞る（ブラウザ負荷軽減のため）
    autocomplete_tags = autocomplete_tags[:20000]
    artist_autocomplete_tags = artist_autocomplete_tags[:20000]

    # --- スマホブラウザの自動翻訳による Error 400 対策 & 切断時の自動復帰 ---
    custom_head = """
    <meta name="google" content="notranslate">
    <script>
        document.documentElement.lang = 'ja';
        document.documentElement.setAttribute('translate', 'no');
        
        // スマホでバックグラウンドから復帰した際、通信エラー(切断)が起きていれば自動でリロードする
        document.addEventListener("visibilitychange", () => {
            if (document.visibilityState === 'visible') {
                // 復帰後に少し待ってからGradioのエラー通知をチェック
                setTimeout(() => {
                    const toasts = document.querySelectorAll('.toast-wrap');
                    toasts.forEach(toast => {
                        const text = toast.innerText.toLowerCase();
                        if (text.includes('connection') || text.includes('error') || text.includes('disconnected')) {
                            window.location.reload();
                        }
                    });
                }, 1500);
            }
        });
    </script>
    """
    
    # --- 追従ボタン用のカスタムCSS ---
    custom_css = """
    .sticky-container {
        position: sticky;
        top: 10px;
        z-index: 999;
        background-color: var(--background-fill-primary);
        padding: 10px;
        border-radius: 8px;
        border: 1px solid var(--border-color-primary);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    /* Gradioの不要なフッターを非表示にして画面を広く使う */
    footer { display: none !important; }
    """

    # --- 3. UI定義 ---
    with gr.Blocks(title=f"{app_name} v{version}", head=custom_head, css=custom_css, theme=gr.themes.Default(primary_hue="blue")) as demo:
        gr.Markdown(f"# 🎨 {app_name} <small>v{version}</small>")
        
        # 起動時点の履歴（プレースホルダー）
        raw_history_startup = history_utils.load_history(config)
        history_state = gr.State(raw_history_startup)
        selected_index = gr.State(-1)
        page_state = gr.State(0) # 現在のページ番号 (0始まり)
        show_favs_state = gr.State(False) # お気に入りフィルタ状態
        history_first_visit = gr.State(True) # 初回訪問フラグ
        
        # Handlers 用の State
        config_state = gr.State(config)
        workflow_file_state = gr.State(workflow_file)
        
        # ランダムアーティスト抽出用にCSVから読み込んだリストを保持
        artist_tags_state = gr.State(artist_autocomplete_tags)
        tabs = gr.Tabs()

        with tabs:
            with gr.Tab("Generate", id=0):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Accordion("Tag Presets", open=False):
                            quality_tags_input = gr.CheckboxGroup(label="Quality Tags", choices=quality_tags_list, value=default_quality_tags)
                            gr.Markdown("---")
                            with gr.Row():
                                y1_en = gr.Checkbox(label="Slot 1", value=False, min_width=60); y1_val = gr.Dropdown(choices=year_choices, value="2026", show_label=False)
                            with gr.Row():
                                y2_en = gr.Checkbox(label="Slot 2", value=False, min_width=60); y2_val = gr.Dropdown(choices=year_choices, value="2025", show_label=False)
                            with gr.Row():
                                y3_en = gr.Checkbox(label="Slot 3", value=False, min_width=60); y3_val = gr.Dropdown(choices=year_choices, value="2024", show_label=False)
                            decade_tags_input = gr.CheckboxGroup(label="Decade Tags", choices=decade_tags_list, value=default_decade_tags)
                            period_tags_input = gr.CheckboxGroup(label="Period Tags", choices=time_period_tags_list, value=default_time_period_tags)
                            meta_tags_input = gr.CheckboxGroup(label="Meta Tags", choices=meta_tags_list, value=default_meta_tags)
                            safety_tags_input = gr.CheckboxGroup(label="Safety Tags", choices=safety_tags_list, value=default_safety_tags)
                            with gr.Row():
                                artist_tags_input = gr.Textbox(label="Artist Tags", placeholder="e.g. artist name", lines=1, elem_id="artist_tags_input_area", scale=3)
                                artist_random_en = gr.Checkbox(label="Random Artist", value=False, scale=1, min_width=100, info="CSVからランダム選出")
                                artist_random_num = gr.Dropdown(choices=["1", "2", "3", "4", "5"], value="1", label="Count", scale=1, min_width=80)
                            custom_tags_input = gr.CheckboxGroup(label="Custom Tags", choices=custom_tags_list, value=default_custom_tags)
                        
                        with gr.Group():
                            gr.Markdown("**Positive Prompt**")
                            with gr.Row(variant="compact"):
                                btn_m_10 = gr.Button("-1.0", size="sm", min_width=40)
                                btn_m_01 = gr.Button("-0.1", size="sm", min_width=40)
                                btn_p_01 = gr.Button("+0.1", size="sm", min_width=40)
                                btn_p_10 = gr.Button("+1.0", size="sm", min_width=40)
                                btn_toggle = gr.Button("ON/OFF", size="sm", min_width=60, variant="secondary")
                                
                            prompt_input = gr.Textbox(label="Positive Prompt", show_label=False, lines=5, elem_id="prompt_input_area")
                            with gr.Row():
                                trigger_first = gr.Checkbox(label="Treat first tag as Trigger Word", value=False, scale=2)
                                enable_negpip = gr.Checkbox(label="Enable NegPiP", value=False, scale=1)
                        with gr.Accordion("Negative Prompt", open=False):
                            with gr.Group():
                                with gr.Row(variant="compact"):
                                    neg_btn_m_10 = gr.Button("-1.0", size="sm", min_width=40)
                                    neg_btn_m_01 = gr.Button("-0.1", size="sm", min_width=40)
                                    neg_btn_p_01 = gr.Button("+0.1", size="sm", min_width=40)
                                    neg_btn_p_10 = gr.Button("+1.0", size="sm", min_width=40)
                                    neg_btn_toggle = gr.Button("ON/OFF", size="sm", min_width=60, variant="secondary")
                                neg_input = gr.Textbox(show_label=False, lines=4, value=default_neg_prompt, elem_id="neg_prompt_input_area")
                        generate_button = gr.Button("Generate Image", variant="primary")
                        
                        # DeepL翻訳機能 (ボタン配置)
                        with gr.Accordion("🇯🇵↔🇺🇸 DeepL Prompt Bridge", open=False):
                            direction_radio, input_ja, output_en = deepl_translator.create_translation_ui()
                            with gr.Row():
                                reflect_btn = gr.Button("⬆️ Reflect")
                                append_btn = gr.Button("➕ Append")
                                translate_current_btn = gr.Button("⬇️ Translate Current Prompt")

                    with gr.Column(scale=1):
                        image_output = gr.Image(label="Result", format="png")
                        status_output = gr.Textbox(label="Status", interactive=False)
                        generate_button_side = gr.Button("Generate Image", variant="primary")
                        with gr.Row():
                            seed_input = gr.Number(label="Seed", value=0, precision=0, scale=3)
                            randomize_seed = gr.Checkbox(label="Randomize Seed", value=True, scale=1)
                        
                        # LoRA Settings (Advanced Settingsの上に配置)
                        with gr.Accordion("LoRA Settings", open=False):
                            with gr.Row():
                                with gr.Column():
                                    l1_name = gr.Dropdown(label="LoRA 1 Model (Main)", choices=lora_files, value=default_loras[0]["name"])
                                    l1_str = gr.Slider(label="Strength", minimum=0.0, maximum=2.0, step=0.01, value=default_loras[0]["str"])
                            with gr.Row():
                                turbo_lora_en = gr.Checkbox(label="Turbo LoRA [ON]", value=False, info="強度1.0で自動適用")
                                highres_lora_en = gr.Checkbox(label="Highres Boost [ON]", value=False, info="強度1.0で自動適用")
                            
                            with gr.Accordion("Extra LoRAs", open=False):
                                with gr.Row():
                                    with gr.Column():
                                        l2_name = gr.Dropdown(label="LoRA 2 Model", choices=lora_files, value=default_loras[1]["name"])
                                        l2_str = gr.Slider(label="Strength", minimum=0.0, maximum=2.0, step=0.01, value=default_loras[1]["str"])
                                with gr.Row():
                                    with gr.Column():
                                        l3_name = gr.Dropdown(label="LoRA 3 Model", choices=lora_files, value=default_loras[2]["name"])
                                        l3_str = gr.Slider(label="Strength", minimum=0.0, maximum=2.0, step=0.01, value=default_loras[2]["str"])
                                with gr.Row():
                                    with gr.Column():
                                        l4_name = gr.Dropdown(label="LoRA 4 Model", choices=lora_files, value=default_loras[3]["name"])
                                        l4_str = gr.Slider(label="Strength", minimum=0.0, maximum=2.0, step=0.01, value=default_loras[3]["str"])
                                with gr.Row():
                                    with gr.Column():
                                        l5_name = gr.Dropdown(label="LoRA 5 Model", choices=lora_files, value=default_loras[4]["name"])
                                        l5_str = gr.Slider(label="Strength", minimum=0.0, maximum=2.0, step=0.01, value=default_loras[4]["str"])

                        with gr.Accordion("Anima ControlNet-LLLite Settings", open=False):
                            with gr.Row():
                                lllite_model = gr.Dropdown(label="LLLite Model", choices=lllite_files, value="None", allow_custom_value=True, scale=3)
                                lllite_en = gr.Checkbox(label="Enable LLLite", value=False, scale=1)
                            with gr.Row():
                                lllite_img = gr.Image(type="filepath", label="Reference Image (Upload)", height=150, scale=3)
                                lllite_auto_res = gr.Checkbox(label="Auto Adjust Resolution", value=default_lllite["auto_res"], info="参照画像の縦横比に合わせて出力を自動調整します", scale=1)
                            with gr.Row():
                                lllite_str = gr.Slider(label="Strength", minimum=0.0, maximum=1.0, step=0.01, value=1.0)
                                lllite_start = gr.Slider(label="Start Percent", minimum=0.0, maximum=1.0, step=0.01, value=0.0)
                                lllite_end = gr.Slider(label="End Percent", minimum=0.0, maximum=1.0, step=0.01, value=1.0)

                        with gr.Accordion("Advanced Settings", open=False):
                            with gr.Row():
                                sampler_dropdown = gr.Dropdown(label="Sampler", choices=["er_sde", "euler_ancestral", "res_multistep"], value="euler_ancestral")
                                res_preset = gr.Dropdown(label="Resolution Preset", choices=list(RESOLUTION_PRESETS.keys()) + ["Custom"], value=default_res_key)
                            
                            with gr.Row():
                                ckpt_name = gr.Dropdown(label="Checkpoint Model", choices=ckpt_files, value=default_ckpt)
                                cfg_steps_preset = gr.Dropdown(label="CFG & Steps Preset", choices=list(CFG_STEPS_PRESETS.keys()) + ["Custom"], value=default_cfg_steps_key)
                            with gr.Row():
                                cfg_slider = gr.Slider(label="CFG", minimum=1.0, maximum=20.0, value=default_cfg, step=0.1)
                                steps_slider = gr.Slider(label="Steps", minimum=1, maximum=100, value=default_steps, step=1)
                            with gr.Row():
                                width_slider = gr.Slider(label="Width", minimum=512, maximum=2048, value=default_w, step=64); height_slider = gr.Slider(label="Height", minimum=512, maximum=2048, value=default_h, step=64)
                        with gr.Row():
                            refresh_btn_adv = gr.Button("🔄 Status"); launch_btn_adv = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        restart_btn_adv = gr.Button(f"♻️ Restart App", variant="secondary")
                        gr.Markdown(f"### [🔗 {ext_link_name}]({ext_link_url})")

            with gr.Tab("Auto Gen", id=1):
                with gr.Column(elem_classes="sticky-container"):
                    with gr.Row():
                        start_auto_btn = gr.Button("▶️ Start Auto Gen", variant="primary")
                        stop_auto_btn = gr.Button("⏹️ Stop", variant="stop")
                    auto_status = gr.Markdown("**Status:** Ready")
                
                auto_gallery = gr.Gallery(show_label=False, columns=1, height="auto", object_fit="contain")

            with gr.Tab("History", id=2) as history_tab:
                history_url_warning = gr.Markdown(visible=False)
                
                # ページネーション UI
                with gr.Row(variant="compact"):
                    refresh_history_btn = gr.Button("🔄 Refresh", scale=1)
                    prev_btn = gr.Button("◀️ Prev", scale=1)
                    page_label = gr.Textbox(value="Page 1 / 1", interactive=False, show_label=False, scale=2, text_align="center")
                    next_btn = gr.Button("Next ▶️", scale=1)
                    fav_filter_btn = gr.Button("❤ Favorites Only", scale=1)
                
                # 初期値としてサーバー起動時の最新データをセット（ページネーション適用済み）
                history_gallery = gr.Gallery(label="Past Generations", columns=4, height="auto", value=ui_handlers.get_gallery_display_data(raw_history_startup, config, 0))
                
                with gr.Accordion("Selected Tag Groups", open=False, visible=False) as tag_accordion:
                    h_q_tags = gr.Textbox(label="Quality Tags", interactive=False, lines=2) 
                    with gr.Row():
                        h_d_tags = gr.Textbox(label="Decade", interactive=False, scale=1)
                        h_p_tags = gr.Textbox(label="Period", interactive=False, scale=1)
                        h_m_tags = gr.Textbox(label="Meta", interactive=False, scale=1)
                        h_s_tags = gr.Textbox(label="Safety", interactive=False, scale=1)
                        h_a_tags = gr.Textbox(label="Artist", interactive=False, scale=1)
                    h_c_tags = gr.Textbox(label="Custom Tags", interactive=False, lines=2)
                
                with gr.Accordion("Applied Positive Prompt", open=False, visible=False) as pos_accordion:
                    selected_prompt_preview = gr.Textbox(show_label=False, interactive=False, lines=3)

                with gr.Accordion("Applied Models & LoRAs", open=False, visible=False) as models_accordion:
                    h_ckpt_name = gr.Textbox(label="Checkpoint Model", interactive=False)
                    h_lora1_name = gr.Textbox(label="LoRA 1 Model", interactive=False)
                    h_lora1_strength = gr.Number(label="LoRA 1 Strength", interactive=False)
                
                with gr.Accordion("Applied Negative Prompt", open=False, visible=False) as neg_accordion:
                    h_neg_prompt = gr.Textbox(show_label=False, interactive=False, lines=2)

                download_original_file = gr.File(label="Download Original Image", visible=False)
                
                with gr.Row():
                    fav_btn = gr.Button("🤍 Like", visible=False, scale=1)
                    restore_btn = gr.Button("♻️ Restore & Go", variant="primary", scale=2, visible=False)
                    send_to_chat_btn = gr.Button("💬 Send to AI Chat", variant="secondary", scale=2, visible=False)
                    send_to_lllite_btn = gr.Button("🖼️ Set to LLLite", variant="secondary", scale=2, visible=False)
                    delete_entry_btn = gr.Button("🗑️ Delete", variant="stop", visible=False, scale=1)
                    with gr.Row(visible=False) as confirm_delete_row:
                        gr.Markdown("⚠️ **Delete?**")
                        yes_delete_btn = gr.Button("Yes", variant="stop", size="sm", scale=1)
                        no_delete_btn = gr.Button("No", size="sm", scale=1)
                
                backup_history_btn = gr.Button("Backup History", variant="secondary", size="sm")
                
                # --- 一括削除セクション ---
                clear_history_btn = gr.Button("Clear All History", variant="stop", size="sm")
                clear_history_notice = gr.Markdown("⚠️ **本当に履歴を消しますか？消去時にバックアップが必ずできます。画像は消えません**", visible=False)
                with gr.Row(visible=False) as confirm_clear_row:
                    yes_clear_btn = gr.Button("Yes, Clear All", variant="stop", size="sm")
                    no_clear_btn = gr.Button("No, Cancel", size="sm")
                
                history_msg = gr.Markdown("")

            with gr.Tab("⚙️ System", id=3):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠 ComfyUI Server Control")
                        url_in = gr.Textbox(label="ComfyUI URL", value=comfy_url)
                        copy_ip_btn = gr.Button(f"📋 Set Detected IP: {detected_url}", size="sm")
                        ip_set_msg = gr.Markdown("", visible=False)
                        bat_in = gr.Textbox(label="Launch Batch Path", value=config.get("launch_bat"))
                        
                        gr.Markdown("#### 📂 File Path Settings")
                        real_out_in = gr.Textbox(
                            label="ComfyUI Output Path (Absolute Path)", 
                            value=config.get("comfy_output_dir", ""), 
                            placeholder="e.g. C:\\ComfyUI_windows\\ComfyUI\\output",
                            info="お使いのComfyUIのoutputフォルダのパスを指定してください"
                        )
                        backup_in = gr.Textbox(
                            label="Backup Folder Path", 
                            value=config.get("backup_output_dir", ""),
                            info="画像の移行先のパスを入力すると、引き続き履歴の追跡が行えます"
                        )
                        workflow_file_in = gr.Textbox(
                            label="Workflow Filename",
                            value=workflow_file,
                            placeholder="e.g. anima-t2i.json",
                            info="使用するワークフローのJSONファイル名を指定してください"
                        )
                        tags_path_in = gr.Textbox(label="Tags CSV Filename", value=tags_csv_path, placeholder="e.g. danbooru_tags.csv")
                        
                        gr.Markdown("### 🏷️ Tag List Editor")
                        gr.Markdown("タグの先頭に+を付けることで初期有効タグにすることができます")
                        
                        # タグ表示用ヘルパー (lambdaで十分なのでここに残すか、handlersに移動も可だが、UI構築時のみ使用なのでここで定義)
                        format_tags = lambda full, default: ", ".join([(f"+{t}" if t in default else t) for t in full])

                        q_tags_edit = gr.Textbox(label="Quality Tags", value=format_tags(quality_tags_list, default_quality_tags))
                        d_tags_edit = gr.Textbox(label="Decade Tags", value=format_tags(decade_tags_list, default_decade_tags))
                        t_tags_edit = gr.Textbox(label="Time Period Tags", value=format_tags(time_period_tags_list, default_time_period_tags))
                        m_tags_edit = gr.Textbox(label="Meta Tags", value=format_tags(meta_tags_list, default_meta_tags))
                        s_tags_edit = gr.Textbox(label="Safety Tags", value=format_tags(safety_tags_list, default_safety_tags))
                        c_tags_edit = gr.Textbox(label="Custom Tags", value=format_tags(custom_tags_list, default_custom_tags))
                        
                        neg_edit = gr.Textbox(label="Default Negative Prompt", value=config.get("default_negative_prompt", ""), lines=3)
                        
                        gr.Markdown("### 📏 Resolution Presets")
                        res_df_data = pd.DataFrame([{"Name": k, "Width": v[0], "Height": v[1]} for k, v in RESOLUTION_PRESETS.items()])
                        res_editor = gr.Dataframe(headers=["Name", "Width", "Height"], datatype=["str", "number", "number"], value=res_df_data, interactive=True)
                        
                        gr.Markdown("### 🎛️ CFG & Steps Presets")
                        cfg_steps_df_data = pd.DataFrame([{"Name": k, "CFG": v[0], "Steps": v[1]} for k, v in CFG_STEPS_PRESETS.items()])
                        cfg_steps_editor = gr.Dataframe(headers=["Name", "CFG", "Steps"], datatype=["str", "number", "number"], value=cfg_steps_df_data, interactive=True)
                        
                        deepl_translator.create_api_key_ui()
                        
                        save_btn = gr.Button("Save All Settings", variant="primary"); save_msg = gr.Markdown("")
                    with gr.Column():
                        gr.Markdown("### 🖥️ Server Management")
                        status_text = gr.Textbox(label="Connection Status", value="Checking...", interactive=False)
                        refresh_btn = gr.Button("🔄 Status"); launch_btn = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        restart_btn = gr.Button(f"♻️ Restart App", variant="secondary")

            with gr.Tab("💬 AI Chat", id=4):
                with gr.Row():
                    chat_clear_btn = gr.Button("会話履歴をクリア")
                    chat_model_input = gr.Textbox(label="LM Studio モデル名", value=default_llm_model, scale=3)

                chat_chatbot = gr.Chatbot(height=500, label="チャット履歴")
                
                gr.Markdown("### 🔊 音声再生コントロール (最新のメッセージ)")
                with gr.Row():
                    chat_play_btn = gr.Button("▶️ 再生")
                    chat_loop_btn = gr.Button("🔄 ループ再生")
                    chat_stop_btn = gr.Button("⏹️ 停止")

                with gr.Row():
                    with gr.Column(scale=2):
                        chat_img_input = gr.Image(type="filepath", label="📷 画像を添付", height=85)
                    with gr.Column(scale=8):
                        chat_msg_input = gr.Textbox(show_label=False, placeholder="メッセージを入力... (Enterで送信)", lines=2)
                
                with gr.Row():
                    tone_choices = [(v.get("label", k), k) for k, v in tone_config.items()]
                    default_tone = "default" if "default" in tone_config else list(tone_config.keys())[0]
                    chat_tone_dropdown = gr.Dropdown(
                        choices=tone_choices,
                        value=default_tone,
                        label="口調（Tone）の設定"
                    )
                    chat_send_btn = gr.Button("送信", variant="primary")

                chat_api_history = gr.State([])
                chat_latest_ai_msg = gr.Textbox(visible=False)

        # --- 4. イベント定義 ---
        
        # DeepL Reflect/Append イベント (NEW)
        reflect_btn.click(fn=lambda x: x, inputs=[output_en], outputs=[prompt_input])
        
        append_btn.click(fn=ui_handlers.append_prompt, inputs=[prompt_input, output_en], outputs=[prompt_input])

        # プロンプト欄の英語を和訳して表示するイベント
        translate_current_btn.click(
            fn=lambda text: (
                gr.update(value="EN -> EN/JA (英→日)"),
                gr.update(value=text, label="English Prompt", placeholder="Enter English text here..."),
                gr.update(value=deepl_translator.translate_prompt(text, "EN -> EN/JA (英→日)"), label="翻訳結果（日本語）")
            ),
            inputs=[prompt_input],
            outputs=[direction_radio, input_ja, output_en]
        )

        # Prompt Emphasis Events (JS only)
        btn_m_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-0.1, "prompt_input_area"))
        btn_m_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-1.0, "prompt_input_area"))
        btn_p_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(0.1, "prompt_input_area"))
        btn_p_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(1.0, "prompt_input_area"))
        btn_toggle.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_toggle_comment("prompt_input_area"))

        # Negative Prompt Emphasis Events
        neg_btn_m_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-0.1, "neg_prompt_input_area"))
        neg_btn_m_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-1.0, "neg_prompt_input_area"))
        neg_btn_p_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(0.1, "neg_prompt_input_area"))
        neg_btn_p_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(1.0, "neg_prompt_input_area"))
        neg_btn_toggle.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_toggle_comment("neg_prompt_input_area"))

        # LoRA Auto-Strength Events
        l1_name.change(fn=update_lora_strength, inputs=[l1_name, l1_str], outputs=l1_str)
        l2_name.change(fn=update_lora_strength, inputs=[l2_name, l2_str], outputs=l2_str)
        l3_name.change(fn=update_lora_strength, inputs=[l3_name, l3_str], outputs=l3_str)
        l4_name.change(fn=update_lora_strength, inputs=[l4_name, l4_str], outputs=l4_str)
        l5_name.change(fn=update_lora_strength, inputs=[l5_name, l5_str], outputs=l5_str)

        # Autocomplete Injection (Load時に一度だけ実行)
        demo.load(fn=None, inputs=[], outputs=[], js=ui_javascript.get_autocomplete_js(autocomplete_tags, ["prompt_input_area", "neg_prompt_input_area"], artist_autocomplete_tags, ["artist_tags_input_area"]))

        # アプリロード時は「内部データのみ」最新化し、ギャラリー描画(重い処理)は避ける
        demo.load(fn=ui_handlers.load_history_state_only, inputs=None, outputs=[history_state, history_gallery, page_state, page_label])
        
        # 手動リフレッシュボタン
        refresh_history_btn.click(fn=ui_handlers.load_latest_history_on_load, inputs=None, outputs=[history_state, history_gallery, page_state, page_label, show_favs_state, fav_filter_btn, history_url_warning])
        
        refresh_btn_adv.click(fn=ui_handlers.check_server_status, inputs=[url_in], outputs=[status_output])
        launch_btn_adv.click(fn=ui_handlers.launch_server, inputs=[bat_in, url_in], outputs=[status_output])
        
        copy_ip_btn.click(
            fn=lambda: (gr.update(value=detected_url), gr.update(value="✅ 反映させるには、**Save All Settings** で保存し、**Restart App** ボタンを押したあと、ブラウザをリロードしてください", visible=True)),
            outputs=[url_in, ip_set_msg]
        )
        res_preset.change(fn=lambda p: RESOLUTION_PRESETS.get(p, [gr.update(), gr.update()]), inputs=[res_preset], outputs=[width_slider, height_slider])
        cfg_steps_preset.change(fn=lambda p: CFG_STEPS_PRESETS.get(p, [gr.update(), gr.update()]), inputs=[cfg_steps_preset], outputs=[cfg_slider, steps_slider])
        
        def auto_update_cfg_steps_on_turbo(is_turbo):
            preset_name = "Fast (LCM/Turbo)" if is_turbo else "Standard"
            vals = CFG_STEPS_PRESETS.get(preset_name, [5.0, 30])
            return preset_name, vals[0], vals[1]
            
        turbo_lora_en.change(fn=auto_update_cfg_steps_on_turbo, inputs=[turbo_lora_en], outputs=[cfg_steps_preset, cfg_slider, steps_slider])

        predict_params = dict(
            fn=ui_handlers.predict, 
            inputs=[prompt_input, neg_input, trigger_first, enable_negpip, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state, ckpt_name, 
                    l1_name, l1_str, turbo_lora_en, highres_lora_en, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str, quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, artist_tags_input, artist_random_en, artist_random_num, artist_tags_state,
                    custom_tags_input, url_in, config_state, workflow_file_state,
                    lllite_en, lllite_model, lllite_img, lllite_str, lllite_start, lllite_end, lllite_auto_res], 
            outputs=[image_output, status_output, history_state, history_gallery, page_state, page_label]
        )
        generate_button.click(**predict_params); generate_button_side.click(**predict_params)
        
        # 連続生成 (Auto Gen) イベント
        auto_gen_event = start_auto_btn.click(
            fn=ui_handlers.continuous_predict,
            inputs=[prompt_input, neg_input, trigger_first, enable_negpip, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state, ckpt_name, 
                    l1_name, l1_str, turbo_lora_en, highres_lora_en, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str, quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, artist_tags_input, artist_random_en, artist_random_num, artist_tags_state,
                    custom_tags_input, url_in, config_state, workflow_file_state,
                    lllite_en, lllite_model, lllite_img, lllite_str, lllite_start, lllite_end, lllite_auto_res],
            outputs=[auto_gallery, auto_status, history_state]
        )

        stop_auto_btn.click(
            fn=lambda: gr.update(value="**Status:** ⏹️ Stopped"),
            inputs=None,
            outputs=[auto_status],
            cancels=[auto_gen_event]  # 無限ループのジェネレーターを強制停止する
        )

        history_gallery.select(
            fn=ui_handlers.on_image_select, 
            inputs=[history_state, page_state, config_state, show_favs_state], 
            outputs=[
                selected_index, 
                h_q_tags, h_d_tags, h_p_tags, h_m_tags, h_s_tags, h_a_tags, h_c_tags, 
                selected_prompt_preview, h_neg_prompt,
                h_ckpt_name,
                h_lora1_name, h_lora1_strength,
                delete_entry_btn, confirm_delete_row,
                restore_btn,
                send_to_chat_btn,
                send_to_lllite_btn,
                tag_accordion,
                neg_accordion,
                pos_accordion,
                models_accordion,
                download_original_file,
                fav_btn
            ]
        )
        
        # Restore時にLoRA情報も復元する
        restore_btn.click(fn=ui_handlers.restore_from_history_by_index, inputs=[selected_index, history_state],
            outputs=[prompt_input, neg_input, trigger_first, enable_negpip, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider,
                     sampler_dropdown, quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val,
                     decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, artist_tags_input, custom_tags_input, tabs, 
                     ckpt_name, l1_name, l1_str, l2_name, l2_str, l3_name, l3_str, turbo_lora_en, highres_lora_en, l4_name, l4_str, l5_name, l5_str,
                     lllite_en, lllite_model, lllite_img, lllite_str, lllite_start, lllite_end, lllite_auto_res])

        delete_entry_btn.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[delete_entry_btn, confirm_delete_row])
        no_delete_btn.click(fn=lambda: (gr.update(visible=True), gr.update(visible=False)), outputs=[delete_entry_btn, confirm_delete_row])

        yes_delete_btn.click(fn=ui_handlers.handle_delete_entry, 
            inputs=[selected_index, history_state, page_state, show_favs_state], 
            outputs=[
                history_state, history_gallery, selected_index, 
                h_q_tags, h_d_tags, h_p_tags, h_m_tags, h_s_tags, h_a_tags, h_c_tags, 
                selected_prompt_preview, h_neg_prompt,
                h_ckpt_name,
                h_lora1_name, h_lora1_strength,
                delete_entry_btn, confirm_delete_row, restore_btn, send_to_chat_btn, send_to_lllite_btn,
                tag_accordion, neg_accordion, pos_accordion, models_accordion, page_state, page_label,
                download_original_file,
                fav_btn
            ]
        )
        
        # AIチャットへ送るイベント
        send_to_chat_btn.click(
            fn=ui_handlers.send_to_chat_action,
            inputs=[selected_index, history_state, config_state],
            outputs=[chat_img_input, chat_msg_input, tabs]
        )

        # LLLiteに送るイベント
        send_to_lllite_btn.click(
            fn=ui_handlers.send_to_lllite_action,
            inputs=[selected_index, history_state, config_state],
            outputs=[lllite_img, tabs]
        )

        clear_history_btn.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)), 
                                outputs=[clear_history_btn, clear_history_notice, confirm_clear_row])
        no_clear_btn.click(fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)), 
                                outputs=[clear_history_btn, clear_history_notice, confirm_clear_row]) 
        yes_clear_btn.click(fn=ui_handlers.handle_clear_history, inputs=[history_state], 
                                outputs=[history_state, history_gallery, selected_prompt_preview, clear_history_notice, confirm_clear_row, clear_history_btn, page_state, page_label, download_original_file, fav_btn])
        
        backup_history_btn.click(fn=lambda: gr.update(value=ui_handlers.backup_history_action(config)), outputs=[history_msg])

        save_btn.click(fn=ui_handlers.handle_save_settings, 
            inputs=[url_in, bat_in, backup_in, real_out_in, workflow_file_in, q_tags_edit, d_tags_edit, t_tags_edit, m_tags_edit, s_tags_edit, c_tags_edit, tags_path_in, res_editor, cfg_steps_editor, neg_edit, gr.State(ext_link_name), gr.State(ext_link_url)], 
            outputs=[save_msg])
        print(h_q_tags)
        
        refresh_btn.click(fn=ui_handlers.check_server_status, inputs=[url_in], outputs=[status_text])
        launch_btn.click(fn=ui_handlers.launch_server, inputs=[bat_in, url_in], outputs=[status_text])
        
        restart_js = """
        () => {
            setTimeout(() => {
                alert("ブラウザをリロードしてください");
            }, 5000);
        }
        """
        restart_btn.click(fn=lambda: ui_handlers.restart_app(app_name), js=restart_js)
        
        # ページネーションイベント
        prev_btn.click(fn=ui_handlers.prev_page, inputs=[page_state, history_state, config_state, show_favs_state], outputs=[page_state, history_gallery, page_label])
        next_btn.click(fn=ui_handlers.next_page, inputs=[page_state, history_state, config_state, show_favs_state], outputs=[page_state, history_gallery, page_label])

        # お気に入り機能イベント
        fav_btn.click(fn=ui_handlers.toggle_favorite, 
                      inputs=[selected_index, history_state, config_state, show_favs_state, page_state], 
                      outputs=[fav_btn, history_state, history_gallery, page_label])
        
        fav_filter_btn.click(fn=ui_handlers.toggle_fav_filter,
                             inputs=[show_favs_state, history_state, config_state],
                             outputs=[show_favs_state, history_gallery, page_state, page_label, fav_filter_btn])

        # Historyタブ初回切り替え時の自動リフレッシュ
        history_tab.select(
            fn=ui_handlers.on_history_tab_select,
            inputs=[history_first_visit],
            outputs=[history_state, history_gallery, page_state, page_label, show_favs_state, fav_filter_btn, history_first_visit, history_url_warning]
        )

        # 【追加】GenerateタブのRestart Appボタンにもイベントを紐付け
        restart_btn_adv.click(fn=lambda: ui_handlers.restart_app(app_name), js=restart_js)
        
        # 【追加】AI Chat タブのイベント紐付け
        chat_inputs = [chat_msg_input, chat_img_input, chat_chatbot, chat_api_history, chat_tone_dropdown, chat_model_input]
        chat_outputs = [chat_chatbot, chat_api_history, chat_img_input, chat_msg_input, chat_latest_ai_msg]

        chat_send_btn.click(ai_chat_manager.chat_and_tts, inputs=chat_inputs, outputs=chat_outputs)
        chat_msg_input.submit(ai_chat_manager.chat_and_tts, inputs=chat_inputs, outputs=chat_outputs)
        chat_clear_btn.click(lambda: ([], [], None, "", ""), inputs=None, outputs=[chat_chatbot, chat_api_history, chat_img_input, chat_msg_input, chat_latest_ai_msg])

        chat_play_btn.click(fn=None, inputs=[chat_latest_ai_msg, chat_tone_dropdown], outputs=[chat_latest_ai_msg], js=ai_chat_manager.get_js_code('normal', tone_config))
        chat_loop_btn.click(fn=None, inputs=[chat_latest_ai_msg, chat_tone_dropdown], outputs=[chat_latest_ai_msg], js=ai_chat_manager.get_js_code('loop', tone_config))
        chat_stop_btn.click(fn=None, inputs=[chat_latest_ai_msg, chat_tone_dropdown], outputs=[chat_latest_ai_msg], js=ai_chat_manager.get_js_code('stop', tone_config))

    return demo