🎨 Anima WebUI <small>v1.1.1</small>

ComfyUI をバックエンドとして利用し、直感的な操作で高品質な画像生成を行うための Gradio ベースの Web UI です。 DeepL API を利用した日本語プロンプトの自動翻訳機能や、生成設定の完全な永続化履歴機能を備えています。

🛠 事前準備

このアプリを動かすには、以下の環境とモデルデータが必要です。
1. ソフトウェア環境

    Python 3.12.x: 公式サイトからダウンロードしてください。インストール時、必ず [Add Python to PATH] にチェックを入れてください。

    ComfyUI: 画像生成のバックエンドとして動作している必要があります。

2. モデル & ワークフローの導入

Hugging Face (circlestone-labs/Anima) から以下のファイルをダウンロードし、配置してください。

    モデルファイル: Anima-v1-0.safetensors 等を ComfyUI 本体の models/checkpoints/ フォルダへ配置します。

    ワークフローファイル: anima-t2i.json を本アプリ（anima-webui）のルートフォルダに配置してください。

3. DeepL API Key (任意)

    プロンプトの日本語翻訳機能を使用する場合に必要です。

🚀 セットアップと起動手順
1. リポジトリのクローン
PowerShell

git clone https://github.com/okpn/anima-webui.git
cd anima-webui

2. 設定ファイルの準備

アプリを正常に動作させるため、以下の 2 つのファイルを準備してください。

    config.json:

        config.json.sample をコピーして、名前を config.json に変更します。

        テキストエディタで開き、DEEPL_API_KEY、comfy_url、launch_bat（ComfyUI 起動用バッチのパス）を編集します。

    
3. 起動

    start_anima_webui.bat をダブルクリックしてください。

    初回起動時に必要なライブラリ（gradio, requests, Pillow, deepl, pandas）が自動インストールされます。

    準備が整うと、ブラウザで http://localhost:7867 が立ち上がります。

💡 主な機能
タブ名	機能概要
Generate	プロンプト入力と画像生成。DeepL による日本語入力サポート。タグプリセット（Quality/Safety）の選択。
History	永続化された生成履歴の確認。画像を消しても設定（プロンプト、シード、解像度等）を完全に復元可能。
System	ComfyUI の起動管理。タグリスト、プリセット解像度、デフォルトネガティブプロンプトの編集。WebUI の再起動。
⚠️ 注意事項

    設定の保護: config.json には API キーが含まれるため、GitHub 等に公開しないでください。

    二重保存の回避: 本アプリの履歴機能は ComfyUI 側の出力画像を参照するため、ストレージを無駄に消費しません。

    再起動: System タブから WebUI を再起動した後は、ブラウザのページを更新（F5）してください。

    二重保存の回避: 本アプリの履歴機能は ComfyUI 側の出力画像を参照するため、ストレージを無駄に消費しません。

    再起動: System タブから WebUI を再起動した後は、ブラウザのページを更新（F5）してください。
