import gradio as gr
import random
import comfy_utils
import deepl_translator
import system_manager
import json
import os

CONFIG_FILE = "config.json"

def create_ui(config):
    # 解像度プリセットの定義
    RESOLUTION_PRESETS = {
        "1024x1024": (1024, 1024),
        "1152x896": (1152, 896),
        "896x1152": (896, 1152)
    }

    def save_current_config(url, bat_path):
        current_conf = config.copy()
        current_conf["comfy_url"] = url
        current_conf["launch_bat"] = bat_path
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(current_conf, f, indent=4, ensure_ascii=False)
        return "✅ 設定を保存しました"

    comfy_url = config.get("comfy_url")
    workflow_file = config.get("workflow_file")

    def predict(prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, history):
        workflow = comfy_utils.load_workflow(workflow_file)
        if not workflow: 
            return None, "Workflow not found.", history, gr.update()

        final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)

        # anima-t2i.json 用のノードマッピング
        if "11" in workflow: workflow["11"]["inputs"]["text"] = prompt
        if "12" in workflow: workflow["12"]["inputs"]["text"] = neg_prompt
        if "28" in workflow:
            workflow["28"]["inputs"]["width"] = int(width)
            workflow["28"]["inputs"]["height"] = int(height)
        if "19" in workflow:
            workflow["19"]["inputs"]["seed"] = final_seed
            workflow["19"]["inputs"]["cfg"] = cfg
            workflow["19"]["inputs"]["steps"] = int(steps)
            workflow["19"]["inputs"]["sampler_name"] = sampler_name

        try:
            output_image = comfy_utils.run_comfy_api(workflow, comfy_url)
            new_entry = {
                "image": output_image, "prompt": prompt, "neg_prompt": neg_prompt,
                "seed": final_seed, "cfg": cfg, "steps": steps, "width": width, "height": height,
                "sampler_name": sampler_name,
                "caption": f"Seed: {final_seed} | {sampler_name}"
            }
            history.insert(0, new_entry)
            gallery_data = [(item["image"], item["caption"]) for item in history]
            return output_image, f"Success (Seed: {final_seed})", history, gallery_data
        except Exception as e:
            return None, f"Error: {str(e)}", history, gr.update()

    def update_resolution(preset_name):
        if preset_name in RESOLUTION_PRESETS:
            w, h = RESOLUTION_PRESETS[preset_name]
            return w, h
        return gr.update(), gr.update()

    def restore_from_history(evt: gr.SelectData, history):
        if not history or evt.index >= len(history):
            return [gr.update()] * 10
        selected = history[evt.index]
        return (
            selected["prompt"], selected["neg_prompt"], selected["seed"], False, 
            selected["cfg"], selected["steps"], selected["width"], selected["height"], 
            selected.get("sampler_name", "euler_ancestral"), gr.Tabs(selected=0)
        )

    with gr.Blocks(title="Anima T2I WebUI", theme=gr.themes.Default(primary_hue="blue")) as demo:
        gr.Markdown("# 🎨 Anima T2I WebUI")
        history_state = gr.State([])
        tabs = gr.Tabs()

        with tabs:
            with gr.Tab("Generate", id=0):
                with gr.Row():
                    with gr.Column(scale=1):
                        # --- Positive Prompt 初期値設定 ---
                        prompt_input = gr.Textbox(
                            label="Positive Prompt", 
                            lines=5, 
                            value="masterpiece, best quality, "
                        )
                        # --- Negative Prompt 初期値設定 ---
                        neg_input = gr.Textbox(
                            label="Negative Prompt", 
                            lines=4, 
                            value="worst quality, low quality, score_1, score_2, score_3, blurry, jpeg artifacts, sepia, extra arms, extra legs, bad anatomy, missing limb, bad hands, extra fingers, extra digits, bad fingers, bad legs, extra legs, bad feet, "
                        )
                        generate_button = gr.Button("Generate Image", variant="primary")
                        gr.Markdown("---")
                        input_ja, output_en = deepl_translator.create_translation_ui()
                        reflect_btn = gr.Button("⬆️ Reflect to Positive Prompt")
                        deepl_translator.create_api_key_ui()
                    with gr.Column(scale=1):
                        image_output = gr.Image(label="Result", format="png")
                        status_output = gr.Textbox(label="Status", interactive=False)
                        with gr.Accordion("Advanced Settings", open=True):
                            sampler_dropdown = gr.Dropdown(
                                label="Sampler", 
                                choices=["er_sde", "euler_ancestral", "res_multistep"], 
                                value="euler_ancestral"
                            )
                            res_preset = gr.Dropdown(
                                label="Resolution Preset",
                                choices=["1024x1024", "1152x896", "896x1152", "Custom"],
                                value="1152x896"
                            )
                            seed_input = gr.Number(label="Seed", value=0, precision=0)
                            randomize_seed = gr.Checkbox(label="Randomize Seed", value=True)
                            cfg_slider = gr.Slider(label="CFG", minimum=1.0, maximum=20.0, value=5.0, step=0.1)
                            steps_slider = gr.Slider(label="Steps", minimum=1, maximum=100, value=50, step=1)
                            with gr.Row():
                                width_slider = gr.Slider(label="Width", minimum=512, maximum=2048, value=1152, step=64)
                                height_slider = gr.Slider(label="Height", minimum=512, maximum=2048, value=896, step=64)
                        
                        gr.Markdown("### [🔗 Media Converter](http://192.168.0.29:7861)")

            # (History / System タブは変更なしのため省略)
            with gr.Tab("History", id=1):
                gr.Markdown("### 🖼️ Generation History")
                history_gallery = gr.Gallery(label="Past Generations", columns=4, height="auto")
                clear_history_btn = gr.Button("Clear History", variant="stop", size="sm")

            with gr.Tab("⚙️ System", id=2):
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🛠 ComfyUI Server Control")
                        url_in = gr.Textbox(label="ComfyUI URL", value=config.get("comfy_url", "http://127.0.0.1:8188"))
                        bat_in = gr.Textbox(label="Launch Batch Path", value=config.get("launch_bat", ""))
                        save_btn = gr.Button("Save Settings")
                        save_msg = gr.Markdown("")
                    with gr.Column():
                        status_text = gr.Textbox(label="Connection Status", value="Checking...", interactive=False)
                        with gr.Row():
                            refresh_btn = gr.Button("🔄 Refresh Status")
                            launch_btn = gr.Button("🚀 Launch ComfyUI", variant="primary")

        # --- イベント定義 ---
        reflect_btn.click(fn=lambda x: x, inputs=[output_en], outputs=[prompt_input])
        res_preset.change(fn=update_resolution, inputs=[res_preset], outputs=[width_slider, height_slider])
        generate_button.click(
            fn=predict, 
            inputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, history_state], 
            outputs=[image_output, status_output, history_state, history_gallery]
        )
        history_gallery.select(
            fn=restore_from_history, 
            inputs=[history_state], 
            outputs=[prompt_input, neg_input, seed_input, randomize_seed, cfg_slider, steps_slider, width_slider, height_slider, sampler_dropdown, tabs]
        )
        clear_history_btn.click(fn=lambda: ([], []), inputs=None, outputs=[history_state, history_gallery])
        save_btn.click(fn=save_current_config, inputs=[url_in, bat_in], outputs=[save_msg])
        refresh_btn.click(fn=lambda: "🟢 Running" if system_manager.check_comfy_status() else "🔴 Stopped", outputs=[status_text])
        launch_btn.click(fn=lambda bat: system_manager.launch_comfy(bat), inputs=[bat_in], outputs=[status_text])

    return demo