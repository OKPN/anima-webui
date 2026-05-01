import json
import requests
import time
import io
import traceback
import os
from PIL import Image

def load_workflow(workflow_path):
    """ワークフローJSONファイルを読み込む"""
    try:
        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def run_comfy_api(workflow, comfy_url):
    """
    ComfyUIにジョブを送信し、完了を待って画像を取得する。
    【v1.4.1 改良】特定のノードID(52等)への依存を完全に排除。
    """
    # 1. ジョブの送信
    try:
        payload = {"prompt": workflow}
        r = requests.post(f"{comfy_url}/prompt", json=payload, timeout=10)
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] ComfyUI Prompt API HTTP Error: {e}")
        print(f"[ERROR] Response Details: {e.response.text}")
        raise RuntimeError(f"ComfyUI API Error: {e}")
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"ComfyUIへの接続に失敗しました: {e}")

    # 2. 実行完了のポーリング
    while True:
        try:
            h_res = requests.get(f"{comfy_url}/history/{prompt_id}", timeout=5)
            h_res.raise_for_status()
            history = h_res.json()
            if prompt_id in history:
                break
            time.sleep(0.5)
        except Exception:
            time.sleep(1)

    # 3. 出力画像の情報を特定 (ID指定ではなく、中身を走査して特定)
    outputs = history[prompt_id].get("outputs", {})
    target_img_info = None

    # すべての出力ノードを確認し、最初に画像(images)を持っているものを採用する
    # これにより SaveImage ノードの番号が何番であっても動作する
    for node_id in outputs:
        if "images" in outputs[node_id] and len(outputs[node_id]["images"]) > 0:
            target_img_info = outputs[node_id]["images"][0]
            break

    if not target_img_info:
        raise RuntimeError("出力画像が見つかりませんでした。ワークフローに 'Save Image' ノードが含まれているか確認してください。")

    # 4. 画像データの取得
    view_params = {
        "filename": target_img_info["filename"],
        "subfolder": target_img_info.get("subfolder", ""),
        "type": target_img_info.get("type", "output")
    }
    
    try:
        img_res = requests.get(f"{comfy_url}/view", params=view_params, timeout=20)
        img_res.raise_for_status()
        img_obj = Image.open(io.BytesIO(img_res.content)).convert("RGB")
        return img_obj, view_params
    except requests.exceptions.HTTPError as e:
        print(f"\n[ERROR] ComfyUI View API HTTP Error: {e}")
        print(f"[ERROR] Response Details: {e.response.text}")
        raise RuntimeError(f"画像の取得に失敗しました: {e}")
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"画像の取得に失敗しました: {e}")

def find_node_by_title(workflow, title):
    """
    ノードの _meta データの title 文字列からノードIDを探す
    """
    for node_id, node in workflow.items():
        if "_meta" in node and node["_meta"].get("title") == title:
            return node_id
    return None

def get_upstream_lora_count(workflow, lora_nodes, nid, visited=None):
    if visited is None:
        visited = set()
    if nid in visited:
        return 0
    visited.add(nid)
    
    node = workflow.get(str(nid), {})
    inputs = node.get("inputs", {})
    
    max_count = 0
    for key, value in inputs.items():
        if isinstance(value, list) and len(value) >= 1:
            source_id = str(value[0])
            count = get_upstream_lora_count(workflow, lora_nodes, source_id, visited)
            if source_id in lora_nodes:
                count += 1
            if count > max_count:
                max_count = count
    return max_count

def extract_default_settings(workflow_file, ckpt_files, lora_files, lllite_files):
    default_ckpt = "None"
    default_loras = [{"name": "None", "str": 0.0} for _ in range(5)]
    default_lllite = {"en": False, "model": "None", "str": 1.0, "start": 0.0, "end": 1.0, "auto_res": True}

    if not workflow_file or not os.path.exists(workflow_file):
        return default_ckpt, default_loras, default_lllite

    workflow = load_workflow(workflow_file)
    if not workflow:
        return default_ckpt, default_loras, default_lllite

    ckpt_node_id = find_node_by_title(workflow, "拡散モデルを読み込む") or find_node_by_title(workflow, "Load Checkpoint")
    if not ckpt_node_id:
        for nid, node in workflow.items():
            class_type = node.get("class_type", "") if isinstance(node, dict) else ""
            if class_type in ["CheckpointLoaderSimple", "UNETLoader"]:
                ckpt_node_id = nid
                break
    if ckpt_node_id:
        inputs = workflow[ckpt_node_id].get("inputs", {})
        default_ckpt = inputs.get("unet_name", inputs.get("ckpt_name", "None"))
        if default_ckpt != "None" and default_ckpt not in ckpt_files:
            ckpt_files.append(default_ckpt)
            ckpt_files.sort()

    lora_nodes = set()
    for nid, node in workflow.items():
        if not isinstance(node, dict): continue
        class_type = node.get("class_type", "")
        title = node.get("_meta", {}).get("title", "")
        if "LoraLoader" in class_type or "LoRA" in title:
            lora_nodes.add(nid)
            
    sorted_loras = list(lora_nodes)
    sorted_loras.sort(key=lambda nid: get_upstream_lora_count(workflow, lora_nodes, nid))
    
    for i, nid in enumerate(sorted_loras):
        if i >= 5: break
        inputs = workflow[nid].get("inputs", {})
        l_name = inputs.get("lora_name", "None")
        l_str = float(inputs.get("strength_model", 0.0))
        default_loras[i] = {"name": l_name, "str": l_str}
        if l_name != "None" and l_name not in lora_files:
            lora_files.append(l_name)
    lora_files.sort()

    lllite_node_id = find_node_by_title(workflow, "LLLite")
    if not lllite_node_id:
        for nid, node in workflow.items():
            class_type = node.get("class_type", "") if isinstance(node, dict) else ""
            if "LLLite" in class_type or "lllite" in class_type.lower():
                lllite_node_id = nid
                break
    if lllite_node_id:
        inputs = workflow[lllite_node_id].get("inputs", {})
        l_model = inputs.get("model_name", "None")
        l_str = float(inputs.get("strength", 1.0))
        default_lllite["model"] = l_model
        default_lllite["str"] = l_str
        default_lllite["start"] = float(inputs.get("start_percent", 0.0))
        default_lllite["end"] = float(inputs.get("end_percent", 1.0))
        default_lllite["en"] = True if (l_str > 0.0 and l_model != "None") else False
        
        if l_model != "None" and l_model not in lllite_files:
            lllite_files.append(l_model)
    lllite_files.sort()

    return default_ckpt, default_loras, default_lllite

def upload_image(file_path, comfy_url):
    """Gradioで取得した画像をComfyUIにアップロードし、ファイル名を返す"""
    if not file_path or not os.path.exists(file_path):
        return None
    try:
        with open(file_path, "rb") as f:
            files = {"image": f}
            res = requests.post(f"{comfy_url}/upload/image", files=files, timeout=10)
            res.raise_for_status()
            return res.json()["name"]
    except Exception as e:
        print(f"⚠️ Failed to upload image: {e}")
        return None