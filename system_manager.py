import socket
import subprocess
import os
import sys
import requests

def check_comfy_status(host="127.0.0.1", port=8188):
    """ComfyUIのポートが開放されているか確認"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        return s.connect_ex((host, port)) == 0

def launch_comfy(bat_path):
    """バッチファイルを新しいウィンドウで実行"""
    if os.path.exists(bat_path):
        # 新しいコンソールを開いて実行
        subprocess.Popen(["cmd", "/c", bat_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return "🚀 起動コマンドを送信しました。立ち上がるまで数十秒お待ちください。"
    return f"❌ エラー: バッチファイルが見つかりません\nパス: {bat_path}"

def restart_webui():
    """WebUI プロセス自体を再起動する"""
    print("--- Restarting Anima WebUI ---")
    # 現在の実行環境（pythonパス）と実行引数を使用して自分自身を再実行
    os.execv(sys.executable, [sys.executable] + sys.argv)