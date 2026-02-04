import socket
import subprocess
import os
import sys

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

def restart_gradio(app_name="Gradio"):
    """
    アプリケーションプロセス自体を再起動する
    app_name: コンソールに表示するアプリ名
    """
    print(f"\n--- 🔄 Restarting {app_name} ---")
    # 現在の実行環境（pythonパス）と実行引数を使用して自分自身を再実行
    executable = sys.executable
    os.execv(executable, [executable] + sys.argv)

def get_local_ip():
    """
    PCのローカルIPアドレス（LAN IP）を取得する (ipconfig関数の実実装)
    """
    # UDPソケットを作成 (パケットは実際には送信されません)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        # 適当な外部アドレス(Google DNS等)に接続を試みることで、
        # OSがその接続に使用するローカルインターフェースのIPを特定します。
        s.connect(('10.254.254.254', 1))
        ip = s.getsockname()[0]
    except Exception:
        # ネットワーク未接続などの場合は localhost を返す
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip