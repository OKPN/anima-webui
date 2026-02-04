import gradio as gr
import random
import comfy_utils
import deepl_translator
import system_manager
import config_utils
import history_utils  # 永続化履歴を管理するモジュール
import pandas as pd

def create_ui(config):
    # --- 1. 設定の取得 (config_utils 経由) ---
    app_name = config.get("app_name", "Gradio")
    version = config_utils.VERSION
    
    RESOLUTION_PRESETS = config.get("resolution_presets")
    default_res_key = config.get("default_resolution")
    
    initial_res = RESOLUTION_PRESETS.get(default_res_key, [1152, 896])
    default_w, default_h = initial_res[0], initial_res[1]

    # 全カテゴリのタグリストを読み込み
    quality_tags_list = config.get("quality_tags_list", [])
    default_quality_tags = config.get("default_quality_tags", [])
    
    decade_tags_list = config.get("decade_tags_list", [])
    
    time_period_tags_list = config.get("time_period_tags_list", [])
    default_time_period_tags = config.get("default_time_period_tags", [])
    
    meta_tags_list = config.get("meta_tags_list", [])
    default_meta_tags = config.get("default_meta_tags", [])
    
    safety_tags_list = config.get("safety_tags_list", [])
    default_safety_tags = config.get("default_safety_tags", [])
    
    default_neg_prompt = config.get("default_negative_prompt")
    comfy_url = config.get("comfy_url", "")
    workflow_file = config.get("workflow_file")

    # 年代リールの選択肢 (1950年まで)
    year_choices = [str(y) for y in range(2026, 1949, -1)]

    def clean_url(url):
        if not url: return ""
        return str(url).strip().rstrip("/")

    # --- 🛠️ 自動IP検出と一致判定 ---
    local_ip = system_manager.get_local_ip()
    detected_url = f"http://{local_ip}:8188"
    
    comfy_url_clean = clean_url(comfy_url)
    detected_url_clean = clean_url(detected_url)
    is_matched = (comfy_url_clean == detected_url_clean)

    # --- 2. 内部ロジック関数 ---

    def apply_detected_ip():
        return (
            gr.update(value=detected_url, info="✅ 検出されたローカルIPと一致しました。保存して再起動してください。"),
            gr.update(visible=False) 
        )

    def handle_save_settings(url, bat_path, q_tags_str, d_tags_str, t_tags_str, m_tags_str, s_tags_str, res_df, neg_prompt):
        """すべてのカテゴリを config_utils へ渡す"""
        if config_utils.update_and_save_config(url, bat_path, q_tags_str, d_tags_str, t_tags_str, m_tags_str, s_tags_str, res_df, neg_prompt):
            return "✅ 設定を保存しました。反映にはアプリの再起動を推奨します。"
        return "❌ 設定の保存に失敗しました。"

    def predict(prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, quality_tags, 
                y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags, period_tags, meta_tags, safety_tags, current_comfy_url):
        workflow = comfy_utils.load_workflow(workflow_file)
        if not workflow: 
            return None, "Workflow not found.", history, gr.update()

        # スロットから有効な年を取得
        selected_years = []
        if y1_en: selected_years.append(f"year {y1_val}")
        if y2_en: selected_years.append(f"year {y2_val}")
        if y3_en: selected_years.append(f"year {y3_val}")

        # 全てのタグを結合
        combined_presets = quality_tags + selected_years + decade_tags + period_tags + meta_tags + safety_tags
        prefix = ", ".join(combined_presets) + ", " if combined_presets else ""
        full_positive_prompt = prefix + prompt
        
        final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)

        if "11" in workflow: workflow["11"]["inputs"]["text"] = full_positive_prompt
        if "12" in workflow: workflow["12"]["inputs"]["text"] = neg_prompt
        if "28" in workflow:
            workflow["28"]["inputs"]["width"] = int(width)
            workflow["28"]["inputs"]["height"] = int(height)
        if "19" in workflow:
            workflow["19"]["inputs"].update({"seed": final_seed, "cfg": cfg, "steps": int(steps), "sampler_name": sampler_name})

        try:
            active_url = clean_url(current_comfy_url)
            output_image, img_info = comfy_utils.run_comfy_api(workflow, active_url)
            
            new_entry = {
                "prompt": prompt, "neg_prompt": neg_prompt, "seed": final_seed, "cfg": cfg, "steps": steps, "width": width, "height": height,
                "sampler_name": sampler_name, "quality_tags": quality_tags, 
                "y1_en": y1_en, "y1_val": y1_val, "y2_en": y2_en, "y2_val": y2_val, "y3_en": y3_en, "y3_val": y3_val,
                "decade_tags": decade_tags, "period_tags": period_tags, "meta_tags": meta_tags, "safety_tags": safety_tags,
                "caption": f"Seed: {final_seed} | {sampler_name}"
            }
            
            saved_entry = history_utils.add_to_history(config, new_entry, img_info, active_url)
            saved_entry["image"] = clean_url(saved_entry.get("image", ""))
            history.insert(0, saved_entry)
            gallery_data = [(clean_url(item["image"]), item["caption"]) for item in history]
            
            return output_image, f"Success (Seed: {final_seed})", history, gallery_data
        except Exception as e:
            return None, f"Error: {str(e)}", history, gr.update()

    def update_resolution(preset_name):
        if preset_name in RESOLUTION_PRESETS:
            res = RESOLUTION_PRESETS[preset_name]
            return res[0], res[1]
        return gr.update(), gr.update()

    def restore_from_history(evt: gr.SelectData, history):
        if not history or evt.index >= len(history):
            return [gr.update()] * 21
        s = history[evt.index]
        return (
            s["prompt"], s["neg_prompt"], s["seed"], False, s["cfg"], s["steps"], s["width"], s["height"], 
            s.get("sampler_name", "euler_ancestral"), s.get("quality_tags", []),
            s.get("y1_en", False), s.get("y1_val", "2026"),
            s.get("y2_en", False), s.get("y2_val", "2025"),
            s.get("y3_en", False), s.get("y3_val", "2024"),
            s.get("decade_tags", []), s.get("period_tags", []), s.get("meta_tags", []), s.get("safety_tags", []),
            gr.Tabs(selected=0)
        )

    # --- 3. UI定義 ---
    with gr.Blocks(title=f"{app_name} v{version}") as demo:
        gr.Markdown(f"# 🎨 {app_name} <small>v{version}</small>")
        
        raw_history = history_utils.load_history(config)
        cleaned_history = [{"image": clean_url(item.get("image", "")), "caption": item.get("caption", "")} for item in raw_history]
        history_state = gr.State(raw_history)
        
        tabs = gr.Tabs()

        with tabs:
            with gr.Tab("Generate", id=0):
                with gr.Row():
                    with gr.Column(scale=1): # 左カラム
                        with gr.Accordion("Tag Presets (Quality, Period, Meta & Safety)", open=False):
                            quality_tags_input = gr.CheckboxGroup(label="Quality Tags", choices=quality_tags_list, value=default_quality_tags)
                            
                            gr.Markdown("---")
                            gr.Markdown("**Specific Year Slots (Blended Year Tags)**")
                            with gr.Row():
                                y1_en = gr.Checkbox(label="Slot 1", value=False, min_width=60)
                                y1_val = gr.Dropdown(choices=year_choices, value="2026", show_label=False)
                            with gr.Row():
                                y2_en = gr.Checkbox(label="Slot 2", value=False, min_width=60)
                                y2_val = gr.Dropdown(choices=year_choices, value="2025", show_label=False)
                            with gr.Row():
                                y3_en = gr.Checkbox(label="Slot 3", value=False, min_width=60)
                                y3_val = gr.Dropdown(choices=year_choices, value="2024", show_label=False)
                            
                            decade_tags_input = gr.CheckboxGroup(label="Decade Tags", choices=decade_tags_list, value=[])
                            period_tags_input = gr.CheckboxGroup(label="Period Tags", choices=time_period_tags_list, value=[])
                            meta_tags_input = gr.CheckboxGroup(label="Meta Tags", choices=meta_tags_list, value=default_meta_tags)
                            safety_tags_input = gr.CheckboxGroup(label="Safety Tags", choices=safety_tags_list, value=default_safety_tags)
                        
                        prompt_input = gr.Textbox(label="Positive Prompt", lines=5)
                        with gr.Accordion("Negative Prompt", open=False):
                            neg_input = gr.Textbox(show_label=False, lines=4, value=default_neg_prompt)
                        generate_button = gr.Button("Generate Image", variant="primary")
                        gr.Markdown("---")
                        input_ja, output_en = deepl_translator.create_translation_ui()
                        reflect_btn = gr.Button("⬆️ Reflect to Positive Prompt")
                        deepl_translator.create_api_key_ui()
                    
                    with gr.Column(scale=1): # 右カラム
                        image_output = gr.Image(label="Result", format="png")
                        status_output = gr.Textbox(label="Status", interactive=False)
                        generate_button_side = gr.Button("Generate Image", variant="primary")
                        with gr.Accordion("Advanced Settings", open=False):
                            sampler_dropdown = gr.Dropdown(label="Sampler", choices=["er_sde", "euler_ancestral", "res_multistep"], value="euler_ancestral")
                            res_preset = gr.Dropdown(label="Resolution Preset", choices=list(RESOLUTION_PRESETS.keys()) + ["Custom"], value=default_res_key)
                            seed_input = gr.Number(label="Seed", value=0, precision=0)
                            randomize_seed = gr.Checkbox(label="Randomize Seed", value=True)
                            cfg_slider = gr.Slider(label="CFG", minimum=1.0, maximum=20.0, value=5.0, step=0.1)
                            steps_slider = gr.Slider(label="Steps", minimum=1, maximum=100, value=50, step=1)
                            with gr.Row():
                                width_slider = gr.Slider(label="Width", minimum=512, maximum=2048, value=default_w, step=64)
                                height_slider = gr.Slider(label="Height", minimum=512, maximum=2048, value=default_h, step=64)
                        gr.Markdown("### [🔗 MediaMatrix Station](http://192.168.0.29:7861)")

            with gr.Tab("History", id=1):
                history_hint = gr.Markdown(f"💡 ヒント...", visible=not is_matched)
                history_gallery = gr.Gallery(label="Past Generations", columns=4, height="auto", value=[(item["image"], item["caption"]) for item in cleaned_history])
                clear_history_btn = gr.Button("Clear History", variant="stop", size="sm")

            with gr.Tab("⚙️ System", id=2):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠 ComfyUI Server Control")
                        url_in = gr.Textbox(label="ComfyUI URL", value=comfy_url, info="💡 IP一致チェック...")
                        copy_ip_btn = gr.Button(f"📋 Set Detected IP: {detected_url}", size="sm")
                        bat_in = gr.Textbox(label="Launch Batch Path", value=config.get("launch_bat"))
                        
                        gr.Markdown("### 🏷️ Tag List Editor")
                        q_tags_edit = gr.Textbox(label="Quality Tags (Comma separated)", value=", ".join(quality_tags_list))
                        d_tags_edit = gr.Textbox(label="Decade Tags (Comma separated)", value=", ".join(decade_tags_list))
                        t_tags_edit = gr.Textbox(label="Time Period Tags (Comma separated)", value=", ".join(time_period_tags_list))
                        m_tags_edit = gr.Textbox(label="Meta Tags (Comma separated)", value=", ".join(meta_tags_list))
                        s_tags_edit = gr.Textbox(label="Safety Tags (Comma separated)", value=", ".join(safety_tags_list))
                        
                        neg_edit = gr.Textbox(label="Default Negative Prompt", value=default_neg_prompt, lines=3)
                        save_btn = gr.Button("Save All Settings", variant="primary")
                        save_msg = gr.Markdown("")
                    # ... (残りのカラムは維持)
                    with gr.Column():
                        gr.Markdown("### 📏 Resolution Presets")
                        res_df_data = pd.DataFrame([{"Name": k, "Width": v[0], "Height": v[1]} for k, v in RESOLUTION_PRESETS.items()])
                        res_editor = gr.Dataframe(headers=["Name", "Width", "Height"], datatype=["str", "number", "number"], value=res_df_data, column_count=(3, "fixed"), interactive=True, label="Resolution List")
                        status_text = gr.Textbox(label="Connection Status", value="Checking...", interactive=False)
                        with gr.Row():
                            refresh_btn = gr.Button("🔄 Refresh Status")
                            launch_btn = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        restart_btn = gr.Button(f"♻️ Restart {app_name}", variant="secondary")

        # --- イベント定義 ---
        copy_ip_btn.click(fn=apply_detected_ip, outputs=[url_in, history_hint])
        predict_params = dict(
            fn=predict, 
            inputs=[
                prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state, 
                quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, url_in
            ], 
            outputs=[image_output, status_output, history_state, history_gallery]
        )
        generate_button.click(**predict_params)
        generate_button_side.click(**predict_params)
        history_gallery.select(fn=restore_from_history, inputs=[history_state], outputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, tabs])
        save_btn.click(fn=handle_save_settings, inputs=[url_in, bat_in, q_tags_edit, d_tags_edit, t_tags_edit, m_tags_edit, s_tags_edit, res_editor, neg_edit], outputs=[save_msg])
        refresh_btn.click(fn=lambda: "🟢 Running" if system_manager.check_comfy_status() else "🔴 Stopped", outputs=[status_text])
        launch_btn.click(fn=lambda bat: system_manager.launch_comfy(bat), inputs=[bat_in], outputs=[status_text])
        restart_btn.click(fn=lambda: system_manager.restart_gradio(app_name))
        
    return demo