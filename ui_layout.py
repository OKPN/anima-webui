import gradio as gr
import random
import comfy_utils
import deepl_translator
import system_manager
import config_utils
import history_utils 
import pandas as pd
from urllib.parse import urlparse # 【追加】URL解析用

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
    time_period_tags_list = config.get("time_period_tags_list", [])
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

    def clean_url(url):
        if not url: return ""
        return str(url).strip().rstrip("/")

    local_ip = system_manager.get_local_ip()
    detected_url = f"http://{local_ip}:8188"
    is_matched = (clean_url(comfy_url) == clean_url(detected_url))

    def get_gallery_display_data(history):
        return [(history_utils.resolve_image_path(item, config), item.get("caption", "")) for item in history]

    # --- 2. 内部ロジック関数 ---

    def check_server_status(url):
        """
        【v1.3.6 修正】URLを正しくパースしてホスト名とポートを抽出する
        """
        target = clean_url(url)
        if not target or target.lower() in ["http:/", "http://", "https:/", "https://"]:
            return "⚠️ URL Not Configured"
        try:
            # URLからホスト(IP)とポートを分離して解析
            parsed = urlparse(target)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 8188
            
            # 正しい引数で呼び出し
            is_running = system_manager.check_comfy_status(host, port)
            return "🟢 Running" if is_running else "🔴 Stopped"
        except Exception as e:
            return f"❌ Connection Error: {str(e)}"

    def launch_server(bat, url):
        target = clean_url(url)
        if not bat: return "❌ Launch Batch Path is empty."
        try:
            res = system_manager.launch_comfy(bat, target)
            return res if res else "🚀 Process Started"
        except Exception as e:
            return f"❌ Launch Error: {str(e)}"

    def handle_save_settings(url, bat_path, backup_path, q_tags_str, d_tags_str, t_tags_str, m_tags_str, s_tags_str, c_tags_str, res_df, neg_prompt, ext_name, ext_url):
        if config_utils.update_and_save_config(url, bat_path, backup_path, q_tags_str, d_tags_str, t_tags_str, m_tags_str, s_tags_str, c_tags_str, res_df, neg_prompt, ext_name, ext_url):
            return "✅ 設定を保存しました。反映にはアプリの再起動を推奨します。"
        return "❌ 設定の保存に失敗しました。"

    def predict(prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, quality_tags, 
                y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags, period_tags, meta_tags, safety_tags, custom_tags, current_comfy_url):
        workflow = comfy_utils.load_workflow(workflow_file)
        if not workflow: return None, "Workflow not found.", history, gr.update()
        selected_years = []
        if y1_en: selected_years.append(f"year {y1_val}")
        if y2_en: selected_years.append(f"year {y2_val}")
        if y3_en: selected_years.append(f"year {y3_val}")
        combined_presets = quality_tags + selected_years + decade_tags + period_tags + meta_tags + safety_tags + custom_tags
        prefix = ", ".join(combined_presets) + ", " if combined_presets else ""
        full_positive_prompt = prefix + prompt
        final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)
        if "11" in workflow: workflow["11"]["inputs"]["text"] = full_positive_prompt
        if "12" in workflow: workflow["12"]["inputs"]["text"] = neg_prompt
        if "28" in workflow: workflow["28"]["inputs"]["width"], workflow["28"]["inputs"]["height"] = int(width), int(height)
        if "19" in workflow: workflow["19"]["inputs"].update({"seed": final_seed, "cfg": cfg, "steps": int(steps), "sampler_name": sampler_name})
        try:
            active_url = clean_url(current_comfy_url)
            output_image, img_info = comfy_utils.run_comfy_api(workflow, active_url)
            new_entry = {
                "prompt": prompt, "neg_prompt": neg_prompt, "seed": final_seed, "cfg": cfg, "steps": steps, "width": width, "height": height,
                "sampler_name": sampler_name, "quality_tags": quality_tags, 
                "y1_en": y1_en, "y1_val": y1_val, "y2_en": y2_en, "y2_val": y2_val, "y3_en": y3_en, "y3_val": y3_val,
                "decade_tags": decade_tags, "period_tags": period_tags, "meta_tags": meta_tags, "safety_tags": safety_tags,
                "custom_tags": custom_tags, "caption": f"Seed: {final_seed} | {sampler_name}"
            }
            saved_entry = history_utils.add_to_history(config, new_entry, img_info, active_url)
            history.insert(0, saved_entry)
            return output_image, f"Success", history, get_gallery_display_data(history)
        except Exception as e:
            return None, f"Error: {str(e)}", history, gr.update()

    # --- History 強化ロジック ---

    def on_image_select(evt: gr.SelectData, history):
        if not history or evt.index >= len(history): 
            return -1, "", gr.update(visible=False), gr.update(visible=False)
        return evt.index, history[evt.index].get("prompt", ""), gr.update(visible=True), gr.update(visible=False)

    def restore_from_history_by_index(idx, history):
        if idx < 0 or not history or idx >= len(history): return [gr.update()] * 22
        s = history[idx]
        return (
            s["prompt"], s["neg_prompt"], s["seed"], False, s["cfg"], s["steps"], s["width"], s["height"], 
            s.get("sampler_name", "euler_ancestral"), s.get("quality_tags", []),
            s.get("y1_en", False), s.get("y1_val", "2026"),
            s.get("y2_en", False), s.get("y2_val", "2025"),
            s.get("y3_en", False), s.get("y3_val", "2024"),
            s.get("decade_tags", []), s.get("period_tags", []), s.get("meta_tags", []), s.get("safety_tags", []),
            s.get("custom_tags", []), gr.Tabs(selected=0)
        )

    def handle_backup_history():
        path = history_utils.backup_history(config)
        return f"✅ Backup created: {path}" if path else "❌ Backup failed."

    def show_clear_confirm():
        return gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)

    def hide_clear_confirm():
        return gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)

    def handle_clear_history(history):
        if history_utils.clear_history(config):
            return [], [], gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)
        return history, get_gallery_display_data(history), gr.update(visible=True), gr.update(visible=True), gr.update(visible=True), gr.update(visible=False)

    def show_delete_confirm():
        return gr.update(visible=False), gr.update(visible=True)

    def hide_delete_confirm():
        return gr.update(visible=True), gr.update(visible=False)

    def handle_delete_entry(idx, history):
        """
        【v1.3.6 改善】削除後、その位置に繰り上がった次の画像を自動選択して連続削除を可能にする
        """
        new_history = history_utils.delete_history_entry(config, idx)
        
        if new_history is not None:
            # 1. 削除した位置に次の画像があるかチェック
            if 0 <= idx < len(new_history):
                next_prompt = new_history[idx].get("prompt", "")
                return (
                    new_history, 
                    get_gallery_display_data(new_history), 
                    idx,           # 同じインデックスを維持
                    next_prompt,   # 繰り上がった画像の情報を表示
                    gr.update(visible=True),  # 削除ボタンを表示し続ける
                    gr.update(visible=False) # 確認Rowは一旦閉じる
                )
            else:
                # リストが空になった、または末尾を消した場合はリセット
                return new_history, get_gallery_display_data(new_history), -1, "", gr.update(visible=False), gr.update(visible=False)
        
        return history, gr.update(), idx, gr.update(), gr.update(), gr.update()

    # --- 3. UI定義 ---
    with gr.Blocks(title=f"{app_name} v{version}") as demo:
        gr.Markdown(f"# 🎨 {app_name} <small>v{version}</small>")
        raw_history = history_utils.load_history(config)
        history_state = gr.State(raw_history)
        selected_index = gr.State(-1)
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
                            decade_tags_input = gr.CheckboxGroup(label="Decade Tags", choices=decade_tags_list, value=[])
                            period_tags_input = gr.CheckboxGroup(label="Period Tags", choices=time_period_tags_list, value=[])
                            meta_tags_input = gr.CheckboxGroup(label="Meta Tags", choices=meta_tags_list, value=default_meta_tags)
                            safety_tags_input = gr.CheckboxGroup(label="Safety Tags", choices=safety_tags_list, value=default_safety_tags)
                            custom_tags_input = gr.CheckboxGroup(label="Custom Tags", choices=custom_tags_list, value=default_custom_tags)
                        prompt_input = gr.Textbox(label="Positive Prompt", lines=5)
                        with gr.Accordion("Negative Prompt", open=False):
                            neg_input = gr.Textbox(show_label=False, lines=4, value=default_neg_prompt)
                        generate_button = gr.Button("Generate Image", variant="primary")
                        with gr.Accordion("🇯🇵→🇺🇸 DeepL Prompt Bridge", open=False):
                            input_ja, output_en = deepl_translator.create_translation_ui()
                            reflect_btn = gr.Button("⬆️ Reflect"); append_btn = gr.Button("➕ Append")
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

            with gr.Tab("History", id=1):
                history_hint = gr.Markdown(f"💡 ヒント...", visible=not is_matched)
                history_gallery = gr.Gallery(label="Past Generations", columns=4, height="auto", value=get_gallery_display_data(raw_history))
                with gr.Row():
                    selected_prompt_preview = gr.Textbox(label="Selected Image Prompt", placeholder="Select image...", interactive=False, lines=2, scale=4)
                    restore_btn = gr.Button("♻️ Restore & Go", variant="primary", scale=1)
                    delete_entry_btn = gr.Button("🗑️ Delete", variant="stop", visible=False, scale=1)
                    with gr.Row(visible=False) as confirm_delete_row:
                        gr.Markdown("⚠️ **Delete?**") 
                        yes_delete_btn = gr.Button("Yes", variant="stop", size="sm", scale=1)
                        no_delete_btn = gr.Button("No", size="sm", scale=1)
                
                backup_history_btn = gr.Button("Backup History", variant="secondary", size="sm")
                backup_status = gr.Markdown("")
                clear_history_btn = gr.Button("Clear All History", variant="stop", size="sm")
                clear_history_notice = gr.Markdown("(タイムスタンプ付き .bak 作成後に削除)", visible=True)
                with gr.Row(visible=False) as confirm_clear_row:
                    gr.Markdown("⚠️ **本当に全て削除しますか？**")
                    yes_clear_btn = gr.Button("YES, Clear All", variant="stop", size="sm")
                    no_clear_btn = gr.Button("Cancel", size="sm")

            with gr.Tab("⚙️ System", id=2):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠 ComfyUI Server Control")
                        url_in = gr.Textbox(label="ComfyUI URL", value=comfy_url)
                        copy_ip_btn = gr.Button(f"📋 Set Detected IP: {detected_url}", size="sm")
                        bat_in = gr.Textbox(label="Launch Batch Path", value=config.get("launch_bat"))
                        backup_in = gr.Textbox(label="Backup Folder Path", value=config.get("backup_output_dir", ""))
                        gr.Markdown("### 🏷️ Tag List Editor")
                        q_tags_edit = gr.Textbox(label="Quality Tags", value=", ".join(quality_tags_list))
                        d_tags_edit = gr.Textbox(label="Decade Tags", value=", ".join(decade_tags_list))
                        t_tags_edit = gr.Textbox(label="Time Period Tags", value=", ".join(time_period_tags_list))
                        m_tags_edit = gr.Textbox(label="Meta Tags", value=", ".join(meta_tags_list))
                        s_tags_edit = gr.Textbox(label="Safety Tags", value=", ".join(safety_tags_list))
                        c_tags_edit = gr.Textbox(label="Custom Tags", value=", ".join(custom_tags_list))
                        neg_edit = gr.Textbox(label="Default Negative Prompt", value=config.get("default_negative_prompt", ""), lines=3)
                        gr.Markdown("### 📏 Resolution Presets")
                        res_df_data = pd.DataFrame([{"Name": k, "Width": v[0], "Height": v[1]} for k, v in RESOLUTION_PRESETS.items()])
                        res_editor = gr.Dataframe(headers=["Name", "Width", "Height"], datatype=["str", "number", "number"], value=res_df_data, interactive=True, label="Resolution List")
                        save_btn = gr.Button("Save All Settings", variant="primary"); save_msg = gr.Markdown("")
                    with gr.Column():
                        gr.Markdown("### 🔗 External Link Settings")
                        ext_name_in = gr.Textbox(label="Link Name", value=ext_link_name); ext_url_in = gr.Textbox(label="Link URL", value=ext_link_url)
                        gr.Markdown("### 🖥️ Server Management")
                        status_text = gr.Textbox(label="Connection Status", value="Checking...", interactive=False)
                        with gr.Row():
                            refresh_btn = gr.Button("🔄 Status"); launch_btn = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        restart_btn = gr.Button(f"♻️ Restart App", variant="secondary")

        # --- イベント定義 ---
        copy_ip_btn.click(fn=lambda: (gr.update(value=detected_url, info="✅ 成功"), gr.update(visible=False)), outputs=[url_in, history_hint])
        reflect_btn.click(fn=lambda x: x, inputs=[output_en], outputs=[prompt_input])
        res_preset.change(fn=lambda p: RESOLUTION_PRESETS.get(p, [gr.update(), gr.update()]), inputs=[res_preset], outputs=[width_slider, height_slider])
        
        predict_params = dict(
            fn=predict, 
            inputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state, 
                    quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, period_tags_input, meta_tags_input, safety_tags_input, 
                    custom_tags_input, url_in], 
            outputs=[image_output, status_output, history_state, history_gallery]
        )
        generate_button.click(**predict_params); generate_button_side.click(**predict_params)
        
        # サーバー管理イベント
        refresh_btn_adv.click(fn=check_server_status, inputs=[url_in], outputs=[status_output])
        launch_btn_adv.click(fn=launch_server, inputs=[bat_in, url_in], outputs=[status_output])
        
        # History イベント
        history_gallery.select(fn=on_image_select, inputs=[history_state], outputs=[selected_index, selected_prompt_preview, delete_entry_btn, confirm_delete_row])
        restore_btn.click(fn=restore_from_history_by_index, inputs=[selected_index, history_state], 
            outputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, 
                     sampler_dropdown, quality_tags_input, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags_input, 
                     period_tags_input, meta_tags_input, safety_tags_input, custom_tags_input, tabs])
        
        delete_entry_btn.click(fn=show_delete_confirm, outputs=[delete_entry_btn, confirm_delete_row])
        no_delete_btn.click(fn=hide_delete_confirm, outputs=[delete_entry_btn, confirm_delete_row])
        yes_delete_btn.click(fn=handle_delete_entry, inputs=[selected_index, history_state], 
            outputs=[history_state, history_gallery, selected_index, selected_prompt_preview, delete_entry_btn, confirm_delete_row])
        
        backup_history_btn.click(fn=handle_backup_history, outputs=[backup_status])
        clear_history_btn.click(fn=show_clear_confirm, outputs=[clear_history_btn, clear_history_notice, backup_history_btn, confirm_clear_row])
        no_clear_btn.click(fn=hide_clear_confirm, outputs=[clear_history_btn, clear_history_notice, backup_history_btn, confirm_clear_row])
        yes_clear_btn.click(fn=handle_clear_history, inputs=[history_state], outputs=[history_state, history_gallery, clear_history_btn, clear_history_notice, backup_history_btn, confirm_clear_row])
        
        save_btn.click(fn=handle_save_settings, inputs=[url_in, bat_in, backup_in, q_tags_edit, d_tags_edit, t_tags_edit, m_tags_edit, s_tags_edit, c_tags_edit, res_editor, neg_edit, ext_name_in, ext_url_in], outputs=[save_msg])
        refresh_btn.click(fn=check_server_status, inputs=[url_in], outputs=[status_text])
        launch_btn.click(fn=launch_server, inputs=[bat_in, url_in], outputs=[status_text])
        restart_btn.click(fn=lambda: system_manager.restart_gradio(app_name))
        
    return demo