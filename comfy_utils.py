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
    ComfyUIにジョブを送信し、完了を待って画像を取得する
    workflow: 編集済みのワークフロー辞書
    comfy_url: ComfyUIのURL (例: http://127.0.0.1:8188)
    """
    # 1. ジョブの送信
    try:
        # ComfyUIのAPI仕様に基づき、"prompt"キーにワークフローを渡す
        payload = {"prompt": workflow}
        r = requests.post(f"{comfy_url}/prompt", json=payload, timeout=10)
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]
    except Exception as e:
        raise RuntimeError(f"ComfyUIへの接続に失敗しました: {e}")

    # 2. 実行完了のポーリング (履歴を確認)
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

    # 3. 出力画像の情報を特定
    outputs = history[prompt_id].get("outputs", {})
    target_img_info = None

    # zi_t2i.json では ID "9" が SaveImage ノード
    if "52" in outputs and "images" in outputs["52"]:
        target_img_info = outputs["52"]["images"][0]
    else:
        # ID "52" がない場合は、最初に見つかった画像出力を採用する
        for node_id in outputs:
            if "images" in outputs[node_id]:
                target_img_info = outputs[node_id]["images"][0]
                break

    if not target_img_info:
        raise RuntimeError("出力画像が見つかりませんでした。ワークフローを確認してください。")

    # 4. 画像データの取得と情報の返却
    view_params = {
        "filename": target_img_info["filename"],
        "subfolder": target_img_info.get("subfolder", ""),
        "type": target_img_info.get("type", "output")
    }
    
    try:
        img_res = requests.get(f"{comfy_url}/view", params=view_params, timeout=20)
        img_res.raise_for_status()
        img_obj = Image.open(io.BytesIO(img_res.content)).convert("RGB")
        
        # 画像オブジェクトと、ComfyUI側でのファイル情報をセットで返す
        return img_obj, view_params
    except Exception as e:
        raise RuntimeError(f"画像の取得に失敗しました: {e}")

def find_node_by_title(workflow, title):
    """
    ノードの _meta データの title 文字列からノードIDを探すユーティリティ
    (ワークフロー内のIDが変更されてもタイトルが同じなら特定可能)
    """
    for node_id, node in workflow.items():
        if "_meta" in node and node["_meta"].get("title") == title:
            return node_id
    return None