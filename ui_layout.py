import gradio as gr
import ui_handlers
import deepl_translator
import system_manager
import config_utils
import history_utils 
import ui_javascript
import pandas as pd
from urllib.parse import urlparse
import os

def create_ui(config):
    # --- 1. 設定の取得 ---
    app_name = config.get("app_name", "Gradio")
    version = config_utils.VERSION
    RESOLUTION_PRESETS = config.get("resolution_presets", {})
    default_res_key = config.get("default_resolution", "1152x896")
    initial_res = RESOLUTION_PRESETS.get(default_res_key, [1152, 896])
    default_w, default_h = initial_res[0], initial_res[1]

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

    # --- 2. タグデータのロード (オートコンプリート用) ---
    tags_csv_path = config.get("tags_csv_path", "danbooru_tags.csv")
    autocomplete_tags = []
    
    # デフォルトのサンプルタグ (CSVがない場合用)
    sample_tags = ["1girl", "solo", "long hair", "short hair", "blue eyes", "red eyes", "smile", "looking at viewer", "standing", "sitting", "masterpiece", "best quality"]
    
    # 設定されたパスが存在せず、カレントディレクトリに danbooru_tags.csv がある場合はそれを優先利用する
    if not os.path.exists(tags_csv_path) and os.path.exists("danbooru_tags.csv"):
        tags_csv_path = "danbooru_tags.csv"

    if os.path.exists(tags_csv_path):
        try:
            # CSVの1列目をタグ名として読み込む (ヘッダーなし想定、あるいはヘッダー処理を入れる)
            # ここでは簡易的に pandas で読み込み、nameカラムがあればそれ、なければ1列目を使う
            df = pd.read_csv(tags_csv_path)
            if "name" in df.columns:
                autocomplete_tags = df["name"].dropna().astype(str).tolist()
            else:
                autocomplete_tags = df.iloc[:, 0].dropna().astype(str).tolist()
        except Exception as e:
            print(f"⚠️ Failed to load tags.csv: {e}")
            autocomplete_tags = sample_tags
    else:
        autocomplete_tags = sample_tags

    # 上位20000件程度に絞る（ブラウザ負荷軽減のため）
    autocomplete_tags = autocomplete_tags[:20000]

    # --- 3. UI定義 ---
    with gr.Blocks(title=f"{app_name} v{version}") as demo:
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
                            custom_tags_input = gr.CheckboxGroup(label="Custom Tags", choices=custom_tags_list, value=default_custom_tags)
                        
                        with gr.Group():
                            gr.Markdown("**Positive Prompt**")
                            with gr.Row(variant="compact"):
                                btn_m_01 = gr.Button("-0.1", size="sm"); btn_m_10 = gr.Button("-1.0", size="sm")
                            with gr.Row(variant="compact"):
                                btn_p_01 = gr.Button("+0.1", size="sm"); btn_p_10 = gr.Button("+1.0", size="sm")
                                
                            prompt_input = gr.Textbox(label="Positive Prompt", show_label=False, lines=5, elem_id="prompt_input_area")
                        with gr.Accordion("Negative Prompt", open=False):
                            with gr.Group():
                                with gr.Row(variant="compact"):
                                    neg_btn_m_01 = gr.Button("-0.1", size="sm"); neg_btn_m_10 = gr.Button("-1.0", size="sm")
                                with gr.Row(variant="compact"):
                                    neg_btn_p_01 = gr.Button("+0.1", size="sm"); neg_btn_p_10 = gr.Button("+1.0", size="sm")
                                neg_input = gr.Textbox(show_label=False, lines=4, value=default_neg_prompt, elem_id="neg_prompt_input_area")
                        generate_button = gr.Button("Generate Image", variant="primary")
                        
                        # DeepL翻訳機能 (ボタン配置)
                        with gr.Accordion("🇯🇵→🇺🇸 DeepL Prompt Bridge", open=False):
                            input_ja, output_en = deepl_translator.create_translation_ui()
                            with gr.Row():
                                reflect_btn = gr.Button("⬆️ Reflect")
                                append_btn = gr.Button("➕ Append")
                            deepl_translator.create_api_key_ui()

                    with gr.Column(scale=1):
                        image_output = gr.Image(label="Result", format="png")
                        status_output = gr.Textbox(label="Status", interactive=False)
                        generate_button_side = gr.Button("Generate Image", variant="primary")
                        with gr.Row():
                            seed_input = gr.Number(label="Seed", value=0, precision=0, scale=3)
                            randomize_seed = gr.Checkbox(label="Randomize Seed", value=True, scale=1)
                        with gr.Accordion("Advanced Settings", open=False):
                            sampler_dropdown = gr.Dropdown(label="Sampler", choices=["er_sde", "euler_ancestral", "res_multistep"], value="euler_ancestral")
                            res_preset = gr.Dropdown(label="Resolution Preset", choices=list(RESOLUTION_PRESETS.keys()) + ["Custom"], value=default_res_key)
                            cfg_slider = gr.Slider(label="CFG", minimum=1.0, maximum=20.0, value=5.0, step=0.1)
                            steps_slider = gr.Slider(label="Steps", minimum=1, maximum=100, value=50, step=1)
                            with gr.Row():
                                width_slider = gr.Slider(label="Width", minimum=512, maximum=2048, value=default_w, step=64); height_slider = gr.Slider(label="Height", minimum=512, maximum=2048, value=default_h, step=64)
                        with gr.Row():
                            refresh_btn_adv = gr.Button("🔄 Status"); launch_btn_adv = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        restart_btn_adv = gr.Button(f"♻️ Restart App", variant="secondary")
                        gr.Markdown(f"### [🔗 {ext_link_name}]({ext_link_url})")

            with gr.Tab("History", id=1) as history_tab:
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
                    h_c_tags = gr.Textbox(label="Custom Tags", interactive=False, lines=2)
                
                selected_prompt_preview = gr.Textbox(label="Selected Image Prompt", placeholder="Select image...", interactive=False, lines=2, visible=False)
                
                with gr.Accordion("Applied Negative Prompt", open=False, visible=False) as neg_accordion:
                    h_neg_prompt = gr.Textbox(show_label=False, interactive=False, lines=2)

                download_original_file = gr.File(label="Download Original Image", visible=False)
                
                with gr.Row():
                    fav_btn = gr.Button("🤍 Like", visible=False, scale=1)
                    restore_btn = gr.Button("♻️ Restore & Go", variant="primary", scale=2, visible=False)
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

            with gr.Tab("⚙️ System", id=2):
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
                        tags_path_in = gr.Textbox(label="Tags CSV Filename", value=tags_csv_path, placeholder="e.g. danbooru_tags.csv")
                        backup_in = gr.Textbox(
                            label="Backup Folder Path", 
                            value=config.get("backup_output_dir", ""),
                            info="画像の移行先のパスを入力すると、引き続き履歴の追跡が行えます"
                        )
                        
                        gr.Markdown("### 🏷️ Tag List Editor")
                        
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
                        save_btn = gr.Button("Save All Settings", variant="primary"); save_msg = gr.Markdown("")
                    with gr.Column():
                        gr.Markdown("### 🖥️ Server Management")
                        status_text = gr.Textbox(label="Connection Status", value="Checking...", interactive=False)
                        refresh_btn = gr.Button("🔄 Status"); launch_btn = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        restart_btn = gr.Button(f"♻️ Restart App", variant="secondary")

        # --- 4. イベント定義 ---
        
        # DeepL Reflect/Append イベント (NEW)
        reflect_btn.click(fn=lambda x: x, inputs=[output_en], outputs=[prompt_input])
        
        append_btn.click(fn=ui_handlers.append_prompt, inputs=[prompt_input, output_en], outputs=[prompt_input])

        # Prompt Emphasis Events (JS only)
        btn_m_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-0.1, "prompt_input_area"))
        btn_m_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-1.0, "prompt_input_area"))
        btn_p_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(0.1, "prompt_input_area"))
        btn_p_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(1.0, "prompt_input_area"))

        # Negative Prompt Emphasis Events
        neg_btn_m_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-0.1, "neg_prompt_input_area"))
        neg_btn_m_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(-1.0, "neg_prompt_input_area"))
        neg_btn_p_01.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(0.1, "neg_prompt_input_area"))
        neg_btn_p_10.click(fn=None, inputs=[], outputs=[], js=ui_javascript.get_js_emphasis(1.0, "neg_prompt_input_area"))

        # Autocomplete Injection (Load時に一度だけ実行)
        demo.load(fn=None, inputs=[], outputs=[], js=ui_javascript.get_autocomplete_js(autocomplete_tags, ["prompt_input_area", "neg_prompt_input_area"]))

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
        
        predict_params = dict(
            fn=ui_handlers.predict, 
            inputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state, 
                    quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, 
                    custom_tags_input, url_in, config_state, workflow_file_state], 
            outputs=[image_output, status_output, history_state, history_gallery, page_state, page_label]
        )
        generate_button.click(**predict_params); generate_button_side.click(**predict_params)
        
        history_gallery.select(
            fn=ui_handlers.on_image_select, 
            inputs=[history_state, page_state, config_state, show_favs_state], 
            outputs=[
                selected_index, 
                h_q_tags, h_d_tags, h_p_tags, h_m_tags, h_s_tags, h_c_tags, 
                selected_prompt_preview, h_neg_prompt,
                delete_entry_btn, confirm_delete_row,
                restore_btn,
                tag_accordion,
                selected_prompt_preview,
                neg_accordion,
                download_original_file,
                fav_btn
            ]
        )
        
        restore_btn.click(fn=ui_handlers.restore_from_history_by_index, inputs=[selected_index, history_state], 
            outputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, 
                     sampler_dropdown, quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, 
                     decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, custom_tags_input, tabs])

        delete_entry_btn.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True)), outputs=[delete_entry_btn, confirm_delete_row])
        no_delete_btn.click(fn=lambda: (gr.update(visible=True), gr.update(visible=False)), outputs=[delete_entry_btn, confirm_delete_row])
        
        yes_delete_btn.click(fn=ui_handlers.handle_delete_entry, 
            inputs=[selected_index, history_state, page_state, show_favs_state], 
            outputs=[
                history_state, history_gallery, selected_index, 
                h_q_tags, h_d_tags, h_p_tags, h_m_tags, h_s_tags, h_c_tags, 
                selected_prompt_preview, h_neg_prompt,
                delete_entry_btn, confirm_delete_row, restore_btn, 
                tag_accordion, selected_prompt_preview, neg_accordion, page_state, page_label,
                download_original_file,
                fav_btn
            ]
        )
        
        clear_history_btn.click(fn=lambda: (gr.update(visible=False), gr.update(visible=True), gr.update(visible=True)), 
                                outputs=[clear_history_btn, clear_history_notice, confirm_clear_row])
        no_clear_btn.click(fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)), 
                                outputs=[clear_history_btn, clear_history_notice, confirm_clear_row]) 
        yes_clear_btn.click(fn=ui_handlers.handle_clear_history, inputs=[history_state], 
                                outputs=[history_state, history_gallery, selected_prompt_preview, clear_history_notice, confirm_clear_row, clear_history_btn, page_state, page_label, download_original_file, fav_btn])
        
        backup_history_btn.click(fn=lambda: gr.update(value=ui_handlers.backup_history_action(config)), outputs=[history_msg])

        save_btn.click(fn=ui_handlers.handle_save_settings, 
            inputs=[url_in, bat_in, backup_in, real_out_in, q_tags_edit, d_tags_edit, t_tags_edit, m_tags_edit, s_tags_edit, c_tags_edit, tags_path_in, res_editor, neg_edit, gr.State(ext_link_name), gr.State(ext_link_url)], 
            outputs=[save_msg])
        
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
        
    return demo