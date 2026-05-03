import os
import json
import base64
import mimetypes
import requests
import gradio as gr

LM_STUDIO_URL = "http://127.0.0.1:1234/v1/chat/completions"

def load_chat_config():
    default_model = "gemma-4-26b-a4b-it-heretic-ara-v2-i1"
    default_tones = {
        "default": {
            "label": "標準",
            "prompt": "あなたは優秀な「画像生成のプロンプト」アシスタントです。画像とその生成プロンプトが貼られたら、ユーザの「プロンプトのどこを変えると望む絵を生成できるか？」という問いに答え、差し替え後の画像生成プロンプトを掲示してください。",
            "caption": "落ち着いた女性の声で自然に読み上げてください。",
            "ref_wav": None
        }
    }
    tone_file = "ai_chat_tones.json"
    if os.path.exists(tone_file):
        try:
            with open(tone_file, "r", encoding="utf-8") as f:
                config_data = json.load(f)
                model = config_data.pop("default_llm_model", default_model)
                # "default_llm_model" キーを削除した残りがトーン設定
                return config_data, model
        except Exception as e:
            print(f"⚠️ Failed to load {tone_file}: {e}")
    return default_tones, default_model

def encode_image_to_base64(filepath):
    with open(filepath, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def chat_and_tts(text, img_path, chatbot_history, api_history, tone, model_name):
    # トーン設定は実行時に都度ロードするか、呼び出し元から受け取るのがクリーンですが
    # ここではローカルのjsonを再度読み込むかキャッシュを使います
    tone_config, _ = load_chat_config()
    
    if not text and not img_path:
        yield chatbot_history, api_history, gr.update(), gr.update(), ""
        return

    if img_path:
        chatbot_history.append({"role": "user", "content": (img_path,)})
    if text:
        chatbot_history.append({"role": "user", "content": text})

    api_msg_content = []
    if text:
        api_msg_content.append({"type": "text", "text": text})
    if img_path:
        b64_img = encode_image_to_base64(img_path)
        mime_type, _ = mimetypes.guess_type(img_path)
        if not mime_type:
            mime_type = "image/jpeg"
        api_msg_content.append({"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}})
    
    api_history.append({"role": "user", "content": api_msg_content})

    yield chatbot_history, api_history, None, "", ""

    messages = [{"role": "system", "content": tone_config[tone]["prompt"]}] + api_history
    try:
        res = requests.post(LM_STUDIO_URL, json={
            "model": model_name,
            "messages": messages,
            "temperature": 0.8,
            "top_p": 0.95
        }, timeout=120)
        res.raise_for_status()
        reply = res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        reply = f"【LLM通信エラー】: {e}"

    chatbot_history.append({"role": "assistant", "content": reply})
    api_history.append({"role": "assistant", "content": reply})

    yield chatbot_history, api_history, gr.update(), gr.update(), reply

def get_js_code(mode, tone_config_dict):
    js_tone_config = {k: {"caption": v.get("caption", ""), "ref_wav": v.get("ref_wav")} for k, v in tone_config_dict.items()}
    js_tone_config_str = json.dumps(js_tone_config, ensure_ascii=False)
    
    code = """
    function(text, tone) {
        if (!text) return text;
        const mode = 'MODE_PLACEHOLDER';
        
        if (window.audioState && window.audioState.currentAudio) {
            window.audioState.isStopped = true;
            window.audioState.currentAudio.pause();
        }
        if (mode === 'stop') return text;

        window.audioState = { isStopped: false, currentAudio: null };
        let isLoopMode = (mode === 'loop');
        
        const sentences = text.match(/[^。！？\\n]+[。！？\\n]*/g) || [text];
        const chunks = [];
        let currentChunk = '';
        for (const sentence of sentences) {
            if (currentChunk.length + sentence.length >= 100 && currentChunk.length > 0) {
                chunks.push(currentChunk.trim());
                currentChunk = '';
            }
            currentChunk += sentence;
        }
        if (currentChunk.trim()) chunks.push(currentChunk.trim());
        if (chunks.length === 0) return text;

        let toneConfig = TONE_CONFIG_PLACEHOLDER;
        
        let fetchAudio = async (chunkText) => {
            let payload = { text: chunkText, caption: toneConfig[tone].caption };
            if (toneConfig[tone].ref_wav) payload.ref_wav = toneConfig[tone].ref_wav;
            try {
                let res = await fetch('/api/tts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
                if (!res.ok) return null;
                let blob = await res.blob();
                return URL.createObjectURL(blob);
            } catch (e) { console.error(e); return null; }
        };
        
        if (!window.cachedAudioUrls) window.cachedAudioUrls = {};
        const cacheKey = text + tone;
        if (!window.cachedAudioUrls[cacheKey]) window.cachedAudioUrls[cacheKey] = [];
        let cachedUrls = window.cachedAudioUrls[cacheKey];
        
        let playLoop = async () => {
            while (!window.audioState.isStopped) {
                let nextAudioPromise = null;
                if (!cachedUrls[0]) nextAudioPromise = fetchAudio(chunks[0]);
                
                for (let i = 0; i < chunks.length; i++) {
                    if (window.audioState.isStopped) break;
                    let url = cachedUrls[i];
                    if (!url) { url = await (nextAudioPromise || fetchAudio(chunks[i])); if (url) cachedUrls[i] = url; }
                    if (i + 1 < chunks.length && !cachedUrls[i + 1]) { nextAudioPromise = fetchAudio(chunks[i + 1]); } else { nextAudioPromise = null; }
                    
                    if (url && !window.audioState.isStopped) {
                        let audio = new Audio(url);
                        window.audioState.currentAudio = audio;
                        await new Promise(r => { audio.onended = r; audio.onerror = r; audio.play().catch(r); });
                        window.audioState.currentAudio = null;
                    }
                }
                if (!isLoopMode) break;
                if (!window.audioState.isStopped) await new Promise(res => setTimeout(res, 800));
            }
        };
        playLoop();
        return text;
    }
    """
    return code.replace("MODE_PLACEHOLDER", mode).replace("TONE_CONFIG_PLACEHOLDER", js_tone_config_str)