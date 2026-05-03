from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware  # ← ★この1行を追加！
from pydantic import BaseModel
import subprocess
import time
import os
from huggingface_hub import hf_hub_download
from irodori_tts.inference_runtime import (
    InferenceRuntime,
    RuntimeKey,
    SamplingRequest,
    default_runtime_device,
    resolve_cfg_scales,
    save_wav,
)

app = FastAPI(title="デスゲームコンシェルジュ TTS API")

# モデルのロード（起動時に1度だけ実行されます）
repo_id = "Aratako/Irodori-TTS-500M-v2-VoiceDesign"
print(f"モデルをダウンロード（またはキャッシュから読み込み）しています: {repo_id}")
checkpoint_path = hf_hub_download(repo_id=repo_id, filename="model.safetensors")

print("モデルをメモリ（VRAM）にロードしています...（数十秒かかる場合があります）")
runtime = InferenceRuntime.from_key(
    RuntimeKey(
        checkpoint=checkpoint_path,
        model_device=default_runtime_device(),
        codec_repo="Aratako/Semantic-DACVAE-Japanese-32dim",
        model_precision="fp32",
        codec_device=default_runtime_device(),
        codec_precision="fp32",
        codec_deterministic_encode=True,
        codec_deterministic_decode=True,
        enable_watermark=False,
        compile_model=False,
        compile_dynamic=False,
    )
)
print("ロード完了！APIの待機を開始します。")

# ↓ ② ここから下を追加（CORSエラーを回避する設定）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # どのURL（ポート）からのアクセスも許可する
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ↑ ここまで追加

# リクエストで受け取るデータの形（JSON）を定義
class TTSRequest(BaseModel):
    text: str
    caption: str = ""
    ref_wav: str = ""

@app.post("/generate-voice")
async def generate_voice(request: TTSRequest):
    try:
        print(f"音声生成を開始します: {request.text}")
        start_time = time.time()

        # 同時にリクエストが来ても上書きされないよう、ファイル名に現在時刻を入れる
        output_filename = f"outputs/output_{int(start_time * 1000)}.wav"
        os.makedirs("outputs", exist_ok=True)
        
        # CFGスケールの解決
        cfg_scale_text, cfg_scale_caption, cfg_scale_speaker, _ = resolve_cfg_scales(
            cfg_guidance_mode="independent",
            cfg_scale_text=3.0,
            cfg_scale_caption=3.0,
            cfg_scale_speaker=5.0,
            cfg_scale=None,
            use_caption_condition=bool(
                runtime.model_cfg.use_caption_condition
                and request.caption
            ),
            use_speaker_condition=bool(runtime.model_cfg.use_speaker_condition),
        )

        # 常駐モデルを使って推論を実行
        result = runtime.synthesize(
            SamplingRequest(
                text=request.text,
                caption=request.caption if request.caption else None,
                ref_wav=request.ref_wav if request.ref_wav else None,
                no_ref=not bool(request.ref_wav),
                num_candidates=1,
                decode_mode="sequential",
                seconds=40.0,            # 1. 生成可能な最大秒数を30秒から60秒に延長
                num_steps=40,
                cfg_scale_text=cfg_scale_text,
                cfg_scale_caption=cfg_scale_caption,
                cfg_scale_speaker=cfg_scale_speaker,
                cfg_guidance_mode="independent",
                cfg_min_t=0.5,
                cfg_max_t=1.0,
                context_kv_cache=True,
                trim_tail=True,         # 2. 語尾の余韻が不自然に切れるのを防ぐため無音カットをオフに
                tail_window_size=20,
                tail_std_threshold=0.05,
                tail_mean_threshold=0.1,
                max_text_len=512,        # 3. テキストのトークン上限を倍増し、長文の尻切れを防ぐ
            ),
            log_fn=None,
        )

        # WAVファイルとして保存
        save_wav(output_filename, result.audio, result.sample_rate)
        
        print(f"音声生成が完了しました！ 処理時間: {time.time() - start_time:.2f}秒")
        
        # 出来上がったWAVファイルをAPIのレスポンスとして返す
        if os.path.exists(output_filename):
            return FileResponse(output_filename, media_type="audio/wav")
        else:
            raise HTTPException(status_code=500, detail="ファイルの生成に失敗しました")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"音声生成中にエラーが発生しました: {str(e)}")
