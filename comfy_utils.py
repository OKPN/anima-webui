import json
import requests
import time
import io
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
    except Exception as e:
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
    except Exception as e:
        raise RuntimeError(f"画像の取得に失敗しました: {e}")

def find_node_by_title(workflow, title):
    """
    ノードの _meta データの title 文字列からノードIDを探す
    """
    for node_id, node in workflow.items():
        if "_meta" in node and node["_meta"].get("title") == title:
            return node_id
    return None