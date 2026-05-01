# generation_manager.py
import random
import comfy_utils
import history_utils
import datetime # 【追加】現在時刻を取得するために必要
import traceback
import math
from PIL import Image

def generate_and_save(
    prompt, neg_prompt, trigger_first, enable_negpip, seed, randomize_seed, cfg, steps, width, height, sampler_name, 
    ckpt_name, l1_name, l1_str, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str,
    turbo_lora_en, highres_lora_en,
    quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, 
    decade_tags, period_tags, meta_tags, safety_tags, artist_tags, custom_tags, 
    current_comfy_url, workflow_file, config,
    lllite_en=False, lllite_model="None", lllite_img=None, lllite_str=1.0, lllite_start=0.0, lllite_end=1.0, lllite_auto_res=True
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

    # --- NegPiP ノードの制御 ---
    negpip_node_id = comfy_utils.find_node_by_title(workflow, "NegPiP")
    if not negpip_node_id:
        for nid, node in workflow.items():
            class_type = node.get("class_type", "") if isinstance(node, dict) else ""
            if "NegPiP" in class_type or "negpip" in class_type.lower():
                negpip_node_id = nid
                break

    if negpip_node_id:
        if enable_negpip:
            if "text" in workflow[negpip_node_id].get("inputs", {}):
                workflow[negpip_node_id]["inputs"]["text"] = full_positive_prompt
        else:
            # NegPiPをオフにする場合。ノードにバイパス用プロパティがあれば設定する。
            # ※ComfyUI APIでノードを完全にバイパスするにはKSamplerへの繋ぎ変えが必要になる場合があります。
            pass

    # --- Anima ControlNet-LLLite ノードの制御 ---
    lllite_node_id = comfy_utils.find_node_by_title(workflow, "LLLite")
    if not lllite_node_id:
        for nid, node in workflow.items():
            class_type = node.get("class_type", "") if isinstance(node, dict) else ""
            if "LLLite" in class_type or "lllite" in class_type.lower():
                lllite_node_id = nid
                break
                
    if lllite_node_id:
        if lllite_en:
            uploaded_filename = None
            if lllite_img:
                active_url = str(current_comfy_url).strip().rstrip("/")
                uploaded_filename = comfy_utils.upload_image(lllite_img, active_url)
                
            if "model_name" in workflow[lllite_node_id].get("inputs", {}):
                workflow[lllite_node_id]["inputs"]["model_name"] = lllite_model
            if "strength" in workflow[lllite_node_id].get("inputs", {}):
                workflow[lllite_node_id]["inputs"]["strength"] = float(lllite_str)
            if "start_percent" in workflow[lllite_node_id].get("inputs", {}):
                workflow[lllite_node_id]["inputs"]["start_percent"] = float(lllite_start)
            if "end_percent" in workflow[lllite_node_id].get("inputs", {}):
                workflow[lllite_node_id]["inputs"]["end_percent"] = float(lllite_end)
                
            if uploaded_filename:
                def find_upstream_load_image(node_id):
                    node = workflow.get(str(node_id), {})
                    if node.get("class_type") == "LoadImage":
                        return str(node_id)
                    for k, v in node.get("inputs", {}).items():
                        if isinstance(v, list) and len(v) == 2:
                            found = find_upstream_load_image(v[0])
                            if found:
                                return found
                    return None
                
                load_image_id = find_upstream_load_image(lllite_node_id)
                if load_image_id:
                    workflow[load_image_id]["inputs"]["image"] = uploaded_filename
                else:
                    for nid, node in workflow.items():
                        if node.get("class_type") == "LoadImage":
                            node["inputs"]["image"] = uploaded_filename
                            break
        else:
            # 無効化時は強度を0にする
            if "strength" in workflow[lllite_node_id].get("inputs", {}):
                workflow[lllite_node_id]["inputs"]["strength"] = 0.0

    # 4. シード値の決定
    final_seed = random.randint(0, 0xffffffffffffffff) if randomize_seed else int(seed)

    # --- 【追加】参照画像の縦横比に合わせて出力解像度を自動調整 ---
    # 現在UIで設定されている Width x Height の総ピクセル数を「モデルの出力能力」として維持しつつ、
    # 参照画像のアスペクト比に合わせて新しい Width と Height を計算します。
    if lllite_node_id and lllite_en and lllite_img and lllite_auto_res:
        try:
            with Image.open(lllite_img) as ref_img:
                img_w, img_h = ref_img.size
            
            if img_w > 0 and img_h > 0:
                target_area = int(width) * int(height)
                aspect_ratio = img_w / img_h
                
                new_h = math.sqrt(target_area / aspect_ratio)
                new_w = new_h * aspect_ratio
                
                # 安定拡散モデル等で一般的な「64の倍数」に丸める
                width = max(64, int(round(new_w / 64) * 64))
                height = max(64, int(round(new_h / 64) * 64))
        except Exception as e:
            print(f"⚠️ Failed to auto-adjust resolution based on reference image: {e}")

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
    
    # リスト化して、上流のLoRA数が少ない順（Checkpointに近い順）にソート
    sorted_loras = list(lora_nodes)
    sorted_loras.sort(key=lambda nid: comfy_utils.get_upstream_lora_count(workflow, lora_nodes, nid))
        
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
        is_model_only = workflow[lora_node_id].get("class_type") == "LoraLoaderModelOnly"
        if i < len(active_loras):
            lora_name, lora_strength = active_loras[i]
            workflow[lora_node_id]["inputs"]["lora_name"] = lora_name
            workflow[lora_node_id]["inputs"]["strength_model"] = lora_strength
            if not is_model_only:
                workflow[lora_node_id]["inputs"]["strength_clip"] = lora_strength
        else:
            # 使わないノードは強度0で無効化
            workflow[lora_node_id]["inputs"]["strength_model"] = 0.0
            if not is_model_only:
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
            "prompt": prompt, "neg_prompt": neg_prompt, "trigger_first": trigger_first, "enable_negpip": enable_negpip, "seed": final_seed, "cfg": cfg, 
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
            "lora5_name": l5_name, "lora5_strength": l5_str,
            "lllite_en": lllite_en, "lllite_model": lllite_model, "lllite_img": lllite_img, 
            "lllite_str": lllite_str, "lllite_start": lllite_start, "lllite_end": lllite_end, "lllite_auto_res": lllite_auto_res
        }

        # 8. 履歴への追加実行
        # (注: 引数の数は元のコードに合わせています)
        saved_entry = history_utils.add_to_history(config, new_entry, img_info, active_url, output_image)
        
        return output_image, "✅ Success", saved_entry

    except Exception as e:
        print("\n[ERROR] Exception in generate_and_save:")
        traceback.print_exc()
        return None, f"❌ Error: {str(e)}", None