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
    RESOLUTION_PRESETS = config.get("resolution_presets")
    default_res_key = config.get("default_resolution")
    
    initial_res = RESOLUTION_PRESETS.get(default_res_key, [1152, 896])
    default_w, default_h = initial_res[0], initial_res[1]

    quality_tags_list = config.get("quality_tags_list")
    default_quality_tags = config.get("default_quality_tags")
    safety_tags_list = config.get("safety_tags_list")
    default_safety_tags = config.get("default_safety_tags")
    default_neg_prompt = config.get("default_negative_prompt")
    
    comfy_url = config.get("comfy_url")
    workflow_file = config.get("workflow_file")

    # --- 2. 内部ロジック関数 ---

    def handle_save_settings(url, bat_path, q_tags_str, s_tags_str, res_df, neg_prompt):
        """システム設定の保存 (config_utils 側で処理を完結)"""
        if config_utils.update_and_save_config(url, bat_path, q_tags_str, s_tags_str, res_df, neg_prompt):
            return "✅ 設定を保存しました。反映にはアプリの再起動を推奨します。"
        return "❌ 設定の保存に失敗しました。"

    def predict(prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, quality_tags, safety_tags):
        workflow = comfy_utils.load_workflow(workflow_file)
        if not workflow: 
            return None, "Workflow not found.", history, gr.update()

        combined_presets = quality_tags + safety_tags
        prefix = ", ".join(combined_presets) + ", " if combined_presets else ""
        full_positive_prompt = prefix + prompt
        
        final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)

        # ワークフロー設定の反映
        if "11" in workflow: workflow["11"]["inputs"]["text"] = full_positive_prompt
        if "12" in workflow: workflow["12"]["inputs"]["text"] = neg_prompt
        if "28" in workflow:
            workflow["28"]["inputs"]["width"] = int(width)
            workflow["28"]["inputs"]["height"] = int(height)
        if "19" in workflow:
            workflow["19"]["inputs"].update({
                "seed": final_seed, "cfg": cfg, "steps": int(steps), "sampler_name": sampler_name
            })

        try:
            # ComfyUIから画像と画像情報(img_info)を取得するように拡張
            output_image, img_info = comfy_utils.run_comfy_api(workflow, comfy_url)
            
            # 保存用のデータ辞書を作成
            new_entry = {
                "prompt": prompt, "neg_prompt": neg_prompt,
                "seed": final_seed, "cfg": cfg, "steps": steps, "width": width, "height": height,
                "sampler_name": sampler_name, 
                "quality_tags": quality_tags, "safety_tags": safety_tags,
                "caption": f"Seed: {final_seed} | {sampler_name}"
            }
            
            # ファイルに保存し、ComfyUIの画像を直接参照するデータを受け取る
            saved_entry = history_utils.add_to_history(config, new_entry, img_info)
            
            # 画面表示用ステートの更新
            history.insert(0, saved_entry)
            gallery_data = [(item["image"], item["caption"]) for item in history]
            
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
            return [gr.update()] * 12
        selected = history[evt.index]
        return (
            selected["prompt"], selected["neg_prompt"], selected["seed"], False, 
            selected["cfg"], selected["steps"], selected["width"], selected["height"], 
            selected.get("sampler_name", "euler_ancestral"), 
            selected.get("quality_tags", default_quality_tags),
            selected.get("safety_tags", default_safety_tags),
            gr.Tabs(selected=0)
        )

    # --- 3. UI定義 ---
    with gr.Blocks(title=f"Anima T2I WebUI v{config_utils.VERSION}") as demo:
        gr.Markdown(f"# 🎨 Anima T2I WebUI <small>v{config_utils.VERSION}</small>")
        
        # --- ここが最重要: 起動時に履歴ファイルを読み込んで画面にセットする ---
        saved_history = history_utils.load_history(config)
        history_state = gr.State(saved_history)
        
        tabs = gr.Tabs()

        with tabs:
            with gr.Tab("Generate", id=0):
                with gr.Row():
                    with gr.Column(scale=1):
                        with gr.Accordion("Tag Presets (Quality & Safety)", open=False):
                            quality_tags_input = gr.CheckboxGroup(label="Quality Tags", choices=quality_tags_list, value=default_quality_tags)
                            safety_tags_input = gr.CheckboxGroup(label="Safety Tags", choices=safety_tags_list, value=default_safety_tags)
                        
                        prompt_input = gr.Textbox(label="Positive Prompt", lines=5, placeholder="Describe what you want to generate...")
                        
                        with gr.Accordion("Negative Prompt", open=False):
                            neg_input = gr.Textbox(show_label=False, lines=4, value=default_neg_prompt)
                        
                        generate_button = gr.Button("Generate Image", variant="primary")
                        gr.Markdown("---")
                        input_ja, output_en = deepl_translator.create_translation_ui()
                        reflect_btn = gr.Button("⬆️ Reflect to Positive Prompt")
                        deepl_translator.create_api_key_ui()
                    
                    with gr.Column(scale=1):
                        image_output = gr.Image(label="Result", format="png")
                        status_output = gr.Textbox(label="Status", interactive=False)
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
                gr.Markdown("### 🖼️ Generation History")
                # --- ロードした履歴データでギャラリーを初期化 ---
                history_gallery = gr.Gallery(
                    label="Past Generations", 
                    columns=4, 
                    height="auto",
                    value=[(item["image"], item["caption"]) for item in saved_history]
                )
                clear_history_btn = gr.Button("Clear History", variant="stop", size="sm")

            with gr.Tab("⚙️ System", id=2):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠 ComfyUI Server Control")
                        url_in = gr.Textbox(label="ComfyUI URL", value=config.get("comfy_url"))
                        bat_in = gr.Textbox(label="Launch Batch Path", value=config.get("launch_bat"))
                        
                        gr.Markdown("### 🏷️ Tag List Editor")
                        q_tags_edit = gr.Textbox(label="Quality Tags (Comma separated)", value=", ".join(quality_tags_list))
                        s_tags_edit = gr.Textbox(label="Safety Tags (Comma separated)", value=", ".join(safety_tags_list))
                        
                        neg_edit = gr.Textbox(label="Default Negative Prompt", value=default_neg_prompt, lines=3)
                        
                        save_btn = gr.Button("Save All Settings", variant="primary")
                        save_msg = gr.Markdown("")
                    with gr.Column():
                        gr.Markdown("### 📏 Resolution Presets")
                        res_df_data = pd.DataFrame([{"Name": k, "Width": v[0], "Height": v[1]} for k, v in RESOLUTION_PRESETS.items()])
                        res_editor = gr.Dataframe(
                            headers=["Name", "Width", "Height"],
                            datatype=["str", "number", "number"],
                            value=res_df_data,
                            column_count=(3, "fixed"), # 警告回避済
                            interactive=True,
                            label="Resolution List (Edit and Save)"
                        )
                        gr.Markdown("---")
                        status_text = gr.Textbox(label="Connection Status", value="Checking...", interactive=False)
                        with gr.Row():
                            refresh_btn = gr.Button("🔄 Refresh Status")
                            launch_btn = gr.Button("🚀 Launch ComfyUI", variant="primary")
                        
                        gr.Markdown("---")
                        gr.Markdown("### ♻️ App Management")
                        restart_btn = gr.Button("♻️ Restart WebUI", variant="secondary")
                        gr.Markdown("※ 再起動後、ブラウザをリロードしてください。")

        # --- イベント定義 ---
        reflect_btn.click(fn=lambda x: x, inputs=[output_en], outputs=[prompt_input])
        res_preset.change(fn=update_resolution, inputs=[res_preset], outputs=[width_slider, height_slider])
        generate_button.click(fn=predict, inputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state, quality_tags_input, safety_tags_input], outputs=[image_output, status_output, history_state, history_gallery])
        history_gallery.select(fn=restore_from_history, inputs=[history_state], outputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, quality_tags_input, safety_tags_input, tabs])
        
        def handle_clear():
            history_utils.clear_history(config)
            return [], []
        
        clear_history_btn.click(fn=handle_clear, inputs=None, outputs=[history_state, history_gallery])
        save_btn.click(fn=handle_save_settings, inputs=[url_in, bat_in, q_tags_edit, s_tags_edit, res_editor, neg_edit], outputs=[save_msg])
        refresh_btn.click(fn=lambda: "🟢 Running" if system_manager.check_comfy_status() else "🔴 Stopped", outputs=[status_text])
        launch_btn.click(fn=lambda bat: system_manager.launch_comfy(bat), inputs=[bat_in], outputs=[status_text])
        restart_btn.click(fn=system_manager.restart_webui)
        
    return demo