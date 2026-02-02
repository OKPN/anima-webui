🎨 Anima WebUI

ComfyUI をバックエンドとして利用し、直感的な操作で画像生成を行うための Gradio ベースの Web UI です。 DeepL API を利用した日本語プロンプトの自動翻訳機能や、ComfyUI サーバの起動管理機能を備えています。
🛠 事前準備

このアプリを動かすには、以下の環境が必要です。

    Python 3.12.x

        公式サイトからダウンロードしてください。

        重要: インストール時、必ず [Add Python to PATH] にチェックを入れてください。

    ComfyUI

        画像生成のバックエンドとして動作している必要があります。

    DeepL API Key (任意)

        プロンプトの日本語翻訳機能を使用する場合に必要です。

🚀 セットアップと起動手順

    リポジトリのクローン
    PowerShell

    git clone https://github.com/okpn/anima-webui.git
    cd anima-webui

    設定ファイルの準備

        config.json.sample をコピーして、同じフォルダに config.json を作成してください。

        config.json をテキストエディタで開き、必要に応じて以下の項目を編集します。

            DEEPL_API_KEY: 自分の API キーを入力。

            comfy_url: ComfyUI のアドレス（デフォルトは http://127.0.0.1:8188）。

    起動

        start_anima_webui.bat をダブルクリックしてください。

        初回起動時は、自動的に仮想環境（venv）が作成され、必要なライブラリがインストールされます。

        準備が整うと、ブラウザで Web UI が立ち上がります。

💡 主な機能

    Generate タブ: プロンプト入力と画像生成。DeepL による日本語入力サポート。

    History タブ: 過去に生成した画像の履歴確認と設定の復元。

    System タブ: ComfyUI サーバーの接続状態確認および、バッチファイルを指定しての起動。

⚠️ 注意事項

    config.json には個人情報（APIキーなど）が含まれるため、GitHub 等に公開しないよう注意してください（デフォルトで .gitignore に指定されています）。

    ComfyUI 側で使用するワークフロー（anima-t2i.json）に必要なカスタムノードがインストールされていることを確認してください。
