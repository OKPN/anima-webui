# generation_manager.py
import random
import comfy_utils
import history_utils
import datetime # 【追加】現在時刻を取得するために必要
import traceback

def generate_and_save(
    prompt, neg_prompt, trigger_first, seed, randomize_seed, cfg, steps, width, height, sampler_name, 
    ckpt_name, l1_name, l1_str, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str,
    turbo_lora_en, highres_lora_en,
    quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, 
    decade_tags, period_tags, meta_tags, safety_tags, artist_tags, custom_tags, 
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
    
    # 【追加】保存ノードを特定 ("画像を保存" というタイトルを探す)
    save_node_id = comfy_utils.find_node_by_title(workflow, "画像を保存")

    # 【変更】モデルノードを特定 ("Load Checkpoint" や "拡散モデルを読み込む" などのタイトル、またはクラス名で探す)
    ckpt_node_id = comfy_utils.find_node_by_title(workflow, "Load Checkpoint")
    if not ckpt_node_id:
        ckpt_node_id = comfy_utils.find_node_by_title(workflow, "拡散モデルを読み込む")
        
    if not ckpt_node_id:
        for nid, node in workflow.items():
            class_type = node.get("class_type", "") if isinstance(node, dict) else ""
            if class_type in ["CheckpointLoaderSimple", "UNETLoader"]:
                ckpt_node_id = nid
                break

    # 3. タグの結合ロジック
    selected_years = []
    if y1_en: selected_years.append(f"year {y1_val}")
    if y2_en: selected_years.append(f"year {y2_val}")
    if y3_en: selected_years.append(f"year {y3_val}")
    
    if artist_tags and artist_tags.strip():
        tags = [t.strip() for t in artist_tags.split(",") if t.strip() and not t.strip().startswith("#")]
        processed_tags = []
        for t in tags:
            if not t.startswith("@"):
                processed_tags.append("@" + t)
            else:
                processed_tags.append(t)
        artist_tags = ", ".join(processed_tags)
    else:
        artist_tags = ""

    combined_presets = quality_tags + selected_years + decade_tags + period_tags + meta_tags + safety_tags + custom_tags
    if artist_tags:
        combined_presets.append(artist_tags)
    prefix = ", ".join(combined_presets) + ", " if combined_presets else ""
    
    # --- #で始まるタグを除外した有効なプロンプトの作成 ---
    active_prompt_tags = [t.strip() for t in prompt.split(",") if t.strip() and not t.strip().startswith("#")]
    active_prompt = ", ".join(active_prompt_tags)
    
    if trigger_first and active_prompt_tags:
        if active_prompt_tags:
            trigger_word = active_prompt_tags[0]
            remaining_prompt = ", ".join(active_prompt_tags[1:])
            if remaining_prompt:
                full_positive_prompt = f"{trigger_word}, {prefix}{remaining_prompt}"
            else:
                full_positive_prompt = f"{trigger_word}, {prefix.rstrip(', ')}"
        else:
            full_positive_prompt = prefix.rstrip(', ')
    else:
        full_positive_prompt = prefix + active_prompt if active_prompt else prefix.rstrip(', ')
        
    active_neg_prompt = ", ".join([t.strip() for t in neg_prompt.split(",") if t.strip() and not t.strip().startswith("#")])

    # 4. シード値の決定
    final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)

    # --- 5. パラメータの動的注入 ---
    # ノードが特定できた場合のみ値を書き換える (堅牢な設計)
    if pos_node_id:
        workflow[pos_node_id]["inputs"]["text"] = full_positive_prompt
    if neg_node_id:
        workflow[neg_node_id]["inputs"]["text"] = active_neg_prompt
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
    if ckpt_node_id:
        if ckpt_name and ckpt_name != "None":
            # ノードの種類によって入力するパラメータ名を変える
            if workflow[ckpt_node_id].get("class_type") == "UNETLoader":
                workflow[ckpt_node_id]["inputs"]["unet_name"] = ckpt_name
            else:
                workflow[ckpt_node_id]["inputs"]["ckpt_name"] = ckpt_name
    
    # 【変更】LoRA設定 (接続順序に基づく自動特定ロジック)
    # ワークフロー内のLoRAノードを全て取得する
    lora_nodes = set()
    for nid, node in workflow.items():
        if not isinstance(node, dict): continue
        class_type = node.get("class_type", "")
        title = node.get("_meta", {}).get("title", "")
        
        # クラス名またはタイトルでLoRAノードを判定
        if "LoraLoader" in class_type or "LoRA" in title:
            lora_nodes.add(nid)
    
    # ノードの接続関係を遡り、上流（モデル読み込み側）にあるLoRAノードの数をカウントする
    def count_upstream_loras(nid, visited=None):
        if visited is None:
            visited = set()
        if nid in visited:
            return 0
        visited.add(nid)
        
        node = workflow.get(str(nid), {})
        inputs = node.get("inputs", {})
        
        max_count = 0
        for key, value in inputs.items():
            # ComfyUIのリンクは [node_id, port_index] のリスト形式
            if isinstance(value, list) and len(value) >= 1:
                source_id = str(value[0])
                count = count_upstream_loras(source_id, visited)
                if source_id in lora_nodes:
                    count += 1
                if count > max_count:
                    max_count = count
        return max_count

    # リスト化して、上流のLoRA数が少ない順（Checkpointに近い順）にソート
    sorted_loras = list(lora_nodes)
    sorted_loras.sort(key=lambda nid: count_upstream_loras(nid))
        
    # --- 適用するLoRAのリストを作成 ---
    active_loras = []
    
    if l1_name and l1_name != "None": active_loras.append((l1_name, float(l1_str)))
    
    if turbo_lora_en:
        active_loras.append((config.get("turbo_lora_path", "anima\\anima-turbo-lora-v0.1.safetensors"), 1.0))
    if highres_lora_en:
        active_loras.append((config.get("highres_lora_path", "anima\\anima-highres-aesthetic-boost.safetensors"), 1.0))
        
    if l2_name and l2_name != "None": active_loras.append((l2_name, float(l2_str)))
    if l3_name and l3_name != "None": active_loras.append((l3_name, float(l3_str)))
    if l4_name and l4_name != "None": active_loras.append((l4_name, float(l4_str)))
    if l5_name and l5_name != "None": active_loras.append((l5_name, float(l5_str)))

    # --- ComfyUIノードへの流し込み ---
    for i, lora_node_id in enumerate(sorted_loras):
        if i < len(active_loras):
            lora_name, lora_strength = active_loras[i]
            workflow[lora_node_id]["inputs"]["lora_name"] = lora_name
            workflow[lora_node_id]["inputs"]["strength_model"] = lora_strength
            workflow[lora_node_id]["inputs"]["strength_clip"] = lora_strength
        else:
            # 使わないノードは強度0で無効化
            workflow[lora_node_id]["inputs"]["strength_model"] = 0.0
            workflow[lora_node_id]["inputs"]["strength_clip"] = 0.0

    # 【追加】ファイル名（プレフィックス）を現在時刻で上書きする処理
    if save_node_id:
        # 現在時刻を取得し "2026-02-07_123456" の形式にする
        now_str = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
        
        # フォルダ名 "anima" と結合して上書き
        # 結果: anima/2026-02-07_123456_00001_.png のようになります
        new_prefix = f"anima/{now_str}"
        
        workflow[save_node_id]["inputs"]["filename_prefix"] = new_prefix

    try:
        # 6. ComfyUI API 実行
        active_url = str(current_comfy_url).strip().rstrip("/")
        output_image, img_info = comfy_utils.run_comfy_api(workflow, active_url)

        # 7. 保存用データの構築
        new_entry = {
            "prompt": prompt, "neg_prompt": neg_prompt, "trigger_first": trigger_first, "seed": final_seed, "cfg": cfg, 
            "steps": steps, "width": width, "height": height, "sampler_name": sampler_name, 
            "quality_tags": quality_tags, "y1_en": y1_en, "y1_val": y1_val, 
            "y2_en": y2_en, "y2_val": y2_val, "y3_en": y3_en, "y3_val": y3_val,
            "decade_tags": decade_tags, "period_tags": period_tags, "meta_tags": meta_tags, 
            "safety_tags": safety_tags, "artist_tags": artist_tags, "custom_tags": custom_tags,
            "caption": f"Seed: {final_seed} | {sampler_name}",
            "ckpt_name": ckpt_name,
            "lora1_name": l1_name, "lora1_strength": l1_str,
            "turbo_lora_en": turbo_lora_en, "highres_lora_en": highres_lora_en,
            "lora2_name": l2_name, "lora2_strength": l2_str,
            "lora3_name": l3_name, "lora3_strength": l3_str,
            "lora4_name": l4_name, "lora4_strength": l4_str,
            "lora5_name": l5_name, "lora5_strength": l5_str
        }

        # 8. 履歴への追加実行
        # (注: 引数の数は元のコードに合わせています)
        saved_entry = history_utils.add_to_history(config, new_entry, img_info, active_url, output_image)
        
        return output_image, "✅ Success", saved_entry

    except Exception as e:
        print("\n[ERROR] Exception in generate_and_save:")
        traceback.print_exc()
        return None, f"❌ Error: {str(e)}", None