# generation_manager.py
import random
import comfy_utils
import history_utils

def generate_and_save(
    prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, 
    quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, 
    decade_tags, period_tags, meta_tags, safety_tags, custom_tags, 
    current_comfy_url, workflow_file, config
):
    """
    ワークフローの初期タイトル値を使用して、IDを動的に特定する生成マネージャー。
    """
    # 1. ワークフローのロード
    workflow = comfy_utils.load_workflow(workflow_file)
    if not workflow:
        return None, "❌ Workflow file not found.", None

    # --- 2. ワークフロー初期値（タイトル）によるノード特定 ---
    # 提供された anima-t2i.json のタイトル名に基づいて検索します
    pos_node_id = comfy_utils.find_node_by_title(workflow, "CLIP Text Encode (Positive Prompt)")
    neg_node_id = comfy_utils.find_node_by_title(workflow, "CLIP Text Encode (Negative Prompt)")
    latent_node_id = comfy_utils.find_node_by_title(workflow, "空の潜在画像")
    sampler_node_id = comfy_utils.find_node_by_title(workflow, "Kサンプラー")

    # 3. タグの結合ロジック
    selected_years = []
    if y1_en: selected_years.append(f"year {y1_val}")
    if y2_en: selected_years.append(f"year {y2_val}")
    if y3_en: selected_years.append(f"year {y3_val}")
    
    combined_presets = quality_tags + selected_years + decade_tags + period_tags + meta_tags + safety_tags + custom_tags
    prefix = ", ".join(combined_presets) + ", " if combined_presets else ""
    full_positive_prompt = prefix + prompt

    # 4. シード値の決定
    final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)

    # --- 5. パラメータの動的注入 ---
    # ノードが特定できた場合のみ値を書き換える (堅牢な設計)
    if pos_node_id:
        workflow[pos_node_id]["inputs"]["text"] = full_positive_prompt
    if neg_node_id:
        workflow[neg_node_id]["inputs"]["text"] = neg_prompt
    if latent_node_id:
        workflow[latent_node_id]["inputs"]["width"] = int(width)
        workflow[latent_node_id]["inputs"]["height"] = int(height)
    if sampler_node_id:
        workflow[sampler_node_id]["inputs"].update({
            "seed": final_seed, 
            "cfg": cfg, 
            "steps": int(steps), 
            "sampler_name": sampler_name
        })

    try:
        # 6. ComfyUI API 実行
        active_url = str(current_comfy_url).strip().rstrip("/")
        output_image, img_info = comfy_utils.run_comfy_api(workflow, active_url)

        # 7. 保存用データの構築
        new_entry = {
            "prompt": prompt, "neg_prompt": neg_prompt, "seed": final_seed, "cfg": cfg, 
            "steps": steps, "width": width, "height": height, "sampler_name": sampler_name, 
            "quality_tags": quality_tags, "y1_en": y1_en, "y1_val": y1_val, 
            "y2_en": y2_en, "y2_val": y2_val, "y3_en": y3_en, "y3_val": y3_val,
            "decade_tags": decade_tags, "period_tags": period_tags, "meta_tags": meta_tags, 
            "safety_tags": safety_tags, "custom_tags": custom_tags,
            "caption": f"Seed: {final_seed} | {sampler_name}"
        }

        # 8. 履歴への追加実行
        saved_entry = history_utils.add_to_history(config, new_entry, img_info, active_url, output_image)
        
        return output_image, "✅ Success", saved_entry

    except Exception as e:
        return None, f"❌ Error: {str(e)}", None