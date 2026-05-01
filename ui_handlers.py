import gradio as gr
import generation_manager
import system_manager
import config_utils
import history_utils
import pandas as pd
import traceback
from urllib.parse import urlparse

def clean_url(url):
    if not url: return ""
    return str(url).strip().rstrip("/")

GALLERY_PER_PAGE = 60

def get_gallery_display_data(history, config, page=0, show_favs=False):
    if show_favs:
        # お気に入りのみ抽出
        target_history = [h for h in history if h.get("is_favorite", False)]
    else:
        target_history = history
        
    start = page * GALLERY_PER_PAGE
    end = start + GALLERY_PER_PAGE
    subset = target_history[start:end]
    return [(history_utils.resolve_thumbnail_path(item, config), item.get("caption", "")) for item in subset]

def get_page_label(page, history, show_favs=False):
    if show_favs:
        target_history = [h for h in history if h.get("is_favorite", False)]
    else:
        target_history = history
        
    total = len(target_history)
    max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
    
    mode_label = " (Favorites)" if show_favs else ""
    return f"Page {page + 1} / {max_page + 1} (Total: {total}){mode_label}"

def parse_tagged_str(input_str):
    all_tags, default_tags = [], []
    for raw in input_str.split(","):
        t = raw.strip()
        if not t: continue
        if t.startswith("+"):
            clean_tag = t[1:].lstrip()
            all_tags.append(clean_tag); default_tags.append(clean_tag)
        else:
            all_tags.append(t)
    return all_tags, default_tags

def process_underscores(text):
    if not text: return ""
    tags = [t.strip() for t in text.split(",")]
    processed_tags = []
    for t in tags:
        if not t: continue
        # scoreから始まるタグは_を維持、それ以外は_をスペースに置換
        if t.lower().startswith("score"):
            processed_tags.append(t)
        else:
            processed_tags.append(t.replace("_", " "))
    return ", ".join(processed_tags)

def handle_save_settings(url, bat_path, backup_path, real_out_path, workflow_file, q_tags_str, d_tags_str, t_tags_str, m_tags_str, s_tags_str, c_tags_str, tags_path, res_df, cfg_steps_df, neg_prompt, ext_name, ext_url):
    q_list, q_def = parse_tagged_str(q_tags_str)
    d_list, d_def = parse_tagged_str(d_tags_str)
    t_list, t_def = parse_tagged_str(t_tags_str)
    m_list, m_def = parse_tagged_str(m_tags_str)
    s_list, s_def = parse_tagged_str(s_tags_str)
    c_list, c_def = parse_tagged_str(c_tags_str)
    
    success = config_utils.update_and_save_config_v2(
        url, bat_path, backup_path, real_out_path, workflow_file,
        q_list, q_def, d_list, d_def, t_list, t_def, m_list, m_def, s_list, s_def, c_list, c_def, tags_path,
        res_df, cfg_steps_df, neg_prompt, ext_name, ext_url
    )
    return "✅ 保存完了。再起動後に反映されます。" if success else "❌ 保存失敗。"

def predict(prompt, neg_prompt, trigger_first, enable_negpip, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, ckpt_name, 
            l1_name, l1_str, turbo_lora_en, highres_lora_en, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str, quality_tags, 
            y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags, period_tags, meta_tags, safety_tags, artist_tags, artist_random_en, artist_random_num, artist_tags_list, custom_tags, current_comfy_url, config, workflow_file,
            lllite_en=False, lllite_model="None", lllite_img=None, lllite_str=1.0, lllite_start=0.0, lllite_end=1.0, lllite_auto_res=True):
    
    # プロンプトのクリーニング処理 (アンダースコアをスペースに変換、scoreタグは除外)
    prompt = process_underscores(prompt)
    neg_prompt = process_underscores(neg_prompt)
    artist_tags = process_underscores(artist_tags)

    if artist_random_en and artist_tags_list:
        import random
        num = int(artist_random_num)
        sampled_artists = random.sample(artist_tags_list, min(num, len(artist_tags_list)))
        if artist_tags:
            artist_tags = artist_tags + ", " + ", ".join(sampled_artists)
        else:
            artist_tags = ", ".join(sampled_artists)

    try:
        output_image, status, saved_entry = generation_manager.generate_and_save(
            prompt, neg_prompt, trigger_first, enable_negpip, seed, randomize_seed, cfg, steps, width, height, sampler_name, 
            ckpt_name, l1_name, l1_str, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str,
            turbo_lora_en, highres_lora_en,
            quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, 
            decade_tags, period_tags, meta_tags, safety_tags, artist_tags, custom_tags, 
            current_comfy_url, workflow_file, config,
            lllite_en, lllite_model, lllite_img, lllite_str, lllite_start, lllite_end, lllite_auto_res
        )
        if saved_entry:
            history.insert(0, saved_entry)
            # 生成後は1ページ目(index 0)に戻す
            return output_image, status, history, get_gallery_display_data(history, config, 0), 0, get_page_label(0, history, False)
        return output_image, status, history, gr.update(), gr.update(), gr.update()
    except Exception as e:
        print("\n[ERROR] Unhandled Exception in predict:")
        traceback.print_exc()
        return None, f"❌ System Error: {str(e)}", history, gr.update(), gr.update(), gr.update()

def continuous_predict(prompt, neg_prompt, trigger_first, enable_negpip, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, ckpt_name, 
            l1_name, l1_str, turbo_lora_en, highres_lora_en, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str, quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags, period_tags, meta_tags, safety_tags, artist_tags, artist_random_en, artist_random_num, artist_tags_list, custom_tags, current_comfy_url, config, workflow_file,
            lllite_en=False, lllite_model="None", lllite_img=None, lllite_str=1.0, lllite_start=0.0, lllite_end=1.0, lllite_auto_res=True):
    """連続生成(Auto Gen)用のジェネレーター関数（50件で自動停止）"""
    auto_images = []
    
    for i in range(50):
        # 既存のpredict関数を呼び出して画像を1枚生成
        output_image, status, new_history, _, _, _ = predict(
            prompt, neg_prompt, trigger_first, enable_negpip, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, ckpt_name, 
            l1_name, l1_str, turbo_lora_en, highres_lora_en, l2_name, l2_str, l3_name, l3_str, l4_name, l4_str, l5_name, l5_str, quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags, period_tags, meta_tags, safety_tags, artist_tags, artist_random_en, artist_random_num, artist_tags_list, custom_tags, current_comfy_url, config, workflow_file,
            lllite_en, lllite_model, lllite_img, lllite_str, lllite_start, lllite_end, lllite_auto_res
        )
        
        history = new_history
        if output_image is not None:
            # スマホで下にスクロールしながら見れるように、リストの末尾に追加する
            auto_images.append(output_image)
            
        # UIに現在の状態をストリーミング更新する
        yield auto_images, f"⏳ **Status:** Auto Generating... ({len(auto_images)}/50)", history
        
    # 50件到達時の完了ステータス
    yield auto_images, f"✅ **Status:** Finished. (Total generated: {len(auto_images)})", history

def check_server_status(url):
    target = clean_url(url)
    try:
        parsed = urlparse(target)
        return "🟢 Running" if system_manager.check_comfy_status(parsed.hostname or "127.0.0.1", parsed.port or 8188) else "🔴 Stopped"
    except: return "❌ Error"

def launch_server(bat, url):
    if not bat: return "❌ Path is empty."
    return system_manager.launch_comfy(bat, clean_url(url)) or "🚀 Process Started"

def send_to_chat_action(idx, history, config):
    if idx < 0 or not history or idx >= len(history):
        return gr.update(), gr.update(), gr.update()
        
    item = history[idx]
    img_path = history_utils.resolve_image_path(item, config)
    
    parts = []
    
    q = ", ".join(item.get("quality_tags", []))
    if q: parts.append(q)
    d = ", ".join(item.get("decade_tags", []))
    if d: parts.append(d)
    p = ", ".join(item.get("period_tags", []))
    if p: parts.append(p)
    m = ", ".join(item.get("meta_tags", []))
    if m: parts.append(m)
    s = ", ".join(item.get("safety_tags", []))
    if s: parts.append(s)
    a = item.get("artist_tags", "")
    if a: parts.append(a)
    c = ", ".join(item.get("custom_tags", []))
    if c: parts.append(c)
    
    prompt = item.get("prompt", "")
    trigger_first = item.get("trigger_first", False)
    
    trigger_word = ""
    remaining_prompt = prompt
    
    if trigger_first and prompt:
        prompt_tags = [t.strip() for t in prompt.split(",") if t.strip() and not t.strip().startswith("#")]
        if prompt_tags:
            trigger_word = prompt_tags[0]
            remaining_prompt = ", ".join(prompt_tags[1:])
            
    if remaining_prompt: 
        parts.append(remaining_prompt)
    
    full_prompt = ", ".join(filter(None, parts))
    
    if trigger_word:
        full_prompt = f"{trigger_word}, {full_prompt}" if full_prompt else trigger_word

    msg_text = full_prompt
    return img_path, msg_text, gr.update(selected=4)

def send_to_lllite_action(idx, history, config):
    if idx < 0 or not history or idx >= len(history):
        return gr.update(), gr.update()
        
    item = history[idx]
    img_path = history_utils.resolve_image_path(item, config)
    
    return img_path, gr.update(selected=0)

def on_image_select(evt: gr.SelectData, history, page, config, show_favs):
    # ページネーションを考慮したインデックス計算
    view_index = (page * GALLERY_PER_PAGE) + evt.index
    
    target_list = history
    if show_favs:
        target_list = [h for h in history if h.get("is_favorite", False)]

    if not target_list or view_index >= len(target_list): 
        return [
            -1, "", "", "", "", "", "", "", "", 
            "", # ckpt_name
            "", # lora1_name
            0.0, # lora1_strength
            gr.update(visible=False),  # Delete
            gr.update(visible=False), # Confirm
            gr.update(visible=False), # Restore
            gr.update(visible=False), # Send to Chat
            gr.update(visible=False), # Send to LLLite
            gr.update(visible=False), # Tag
            gr.update(visible=False), # Neg
            gr.update(visible=False), # Pos
            gr.update(visible=False), # Models
            gr.update(visible=False, value=None),
            gr.update(visible=False) # fav_btn
        ]
    
    item = target_list[view_index]
    
    # フィルタリングされている場合、元のhistoryリスト内でのインデックスを探す必要がある
    # ここではオブジェクトの同一性(id)ではなく、内容の一致で探す（簡易的に）
    # ただし、historyリスト内のオブジェクトそのものを参照しているはずなので、index()で検索可能
    try:
        real_index = history.index(item)
    except ValueError:
        real_index = -1 # Error case

    q = ", ".join(item.get("quality_tags", []))
    d = ", ".join(item.get("decade_tags", []))
    p = ", ".join(item.get("period_tags", []))
    m = ", ".join(item.get("meta_tags", []))
    s = ", ".join(item.get("safety_tags", []))
    a = item.get("artist_tags", "")
    c = ", ".join(item.get("custom_tags", []))
    
    ckpt_name = item.get("ckpt_name", "None")
    lora1_name = item.get("lora1_name", "None")
    lora1_strength = item.get("lora1_strength", 0.0)
    original_image_path = history_utils.resolve_image_path(item, config)
    
    is_fav = item.get("is_favorite", False)
    fav_label = "❤ Liked" if is_fav else "🤍 Like"
    fav_variant = "primary" if is_fav else "secondary"
    
    
    return [
        real_index,
        q, d, p, m, s, a, c, 
        item.get("prompt", ""),
        item.get("neg_prompt", ""),
        ckpt_name,
        lora1_name,
        lora1_strength,
        gr.update(visible=True),  # Delete
        gr.update(visible=False), # Confirm
        gr.update(visible=True),  # Restore
        gr.update(visible=True),  # Send to Chat
        gr.update(visible=True),  # Send to LLLite
        gr.update(visible=True),  # TagAccordion
        gr.update(visible=True),  # NegPromptAccordion
        gr.update(visible=True),  # PosAccordion
        gr.update(visible=True),  # ModelsAccordion
        gr.update(visible=True, value=original_image_path),
        gr.update(visible=True, value=fav_label, variant=fav_variant) # fav_btn
    ]

def restore_from_history_by_index(idx, history):
    if idx < 0 or not history or idx >= len(history): return [gr.update()] * 45
    s = history[idx]
    return (
        s["prompt"], s["neg_prompt"], s.get("trigger_first", False), s.get("enable_negpip", False), s["seed"], True, s["cfg"], s["steps"], s["width"], s["height"],

        s.get("sampler_name", "euler_ancestral"), s.get("quality_tags", []),
        s.get("y1_en", False), s.get("y1_val", "2026"), s.get("y2_en", False), s.get("y2_val", "2025"),
        s.get("y3_en", False), s.get("y3_val", "2024"),
        s.get("decade_tags", []), s.get("period_tags", []), s.get("meta_tags", []), s.get("safety_tags", []), s.get("artist_tags", ""),
        s.get("custom_tags", []), gr.update(selected=0),
        s.get("ckpt_name", "None"),
        s.get("lora1_name", "None"),
        float(s.get("lora1_strength", 0.0)),
        s.get("lora2_name", "None"),
        float(s.get("lora2_strength", 0.0)),
        s.get("lora3_name", "None"),
        float(s.get("lora3_strength", 0.0)),
        s.get("turbo_lora_en", False),
        s.get("highres_lora_en", False),
        s.get("lora4_name", "None"),
        float(s.get("lora4_strength", 0.0)),
        s.get("lora5_name", "None"),
        float(s.get("lora5_strength", 0.0)),
        s.get("lllite_en", False),
        s.get("lllite_model", "None"),
        s.get("lllite_img", None),
        float(s.get("lllite_str", 1.0)),
        float(s.get("lllite_start", 0.0)),
        float(s.get("lllite_end", 1.0)),
        s.get("lllite_auto_res", True)
    )
def check_url_warning(config):
    current_url = config.get("comfy_url", "")
    local_ip = system_manager.get_local_ip()
    
    if not current_url or not local_ip:
        return gr.update(visible=False)
        
    # URL内に localhost や 127.0.0.1 が含まれているか
    is_loopback = "localhost" in current_url or "127.0.0.1" in current_url
    
    # ローカルIP自体がループバックでないことを確認
    ip_is_not_loopback = local_ip != "127.0.0.1" and local_ip != "localhost"
    
    if is_loopback and ip_is_not_loopback:
        msg = f"⚠️ **ネットワーク警告:** 現在の ComfyUI URL は `{current_url}` です。他のデバイスで履歴画像が表示されない場合は、Systemタブで ComfyUI URL を `http://{local_ip}:8188` に設定してみてください。"
        return gr.update(visible=True, value=msg)
        
    return gr.update(visible=False)

def load_latest_history_on_load():
    current_cfg = config_utils.load_config() 
    hist = history_utils.load_history(current_cfg)
    warn = check_url_warning(current_cfg)
    # 初期ロード時はページ0
    return hist, get_gallery_display_data(hist, current_cfg, 0, False), 0, get_page_label(0, hist, False), False, "❤ Favorites Only", warn

def on_history_tab_select(first_visit):
    if not first_visit:
        # 2回目以降は何もしない（フラグはFalseのまま維持）
        return gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), False, gr.update()
    
    # 初回のみリフレッシュを実行
    hist, gallery, page, label, fav_state, fav_label, warn = load_latest_history_on_load()
    return hist, gallery, page, label, fav_state, fav_label, False, warn

def load_history_state_only():
    """起動時用: 内部データだけ更新し、重いギャラリー描画はスキップする"""
    current_cfg = config_utils.load_config() 
    hist = history_utils.load_history(current_cfg)
    # Galleryは gr.update() で「変更なし」を返す
    return hist, gr.update(), 0, get_page_label(0, hist, False)

def handle_delete_entry(idx, history, page, show_favs):
    if idx < 0: 
        return (history, gr.update(), -1, 
                "", "", "", "", "", "", "", "", "",
                "", "", 0.0,
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), # send_to_chat
                gr.update(visible=False), # send_to_lllite
                gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), page, gr.update(),
                gr.update(visible=False, value=None),
                gr.update(visible=False))
    
    current_config = config_utils.load_config()
    new_h = history_utils.delete_history_entry(current_config, history, idx)
    
    if not new_h:
        return (new_h, [], -1, 
                "", "", "", "", "", "", "", "", "",
                "", "", 0.0,
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), # send_to_chat
                gr.update(visible=False), # send_to_lllite
                gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), 0, get_page_label(0, [], show_favs),
                gr.update(visible=False, value=None),
                gr.update(visible=False))
    
    # 削除後にページ範囲外にならないよう調整
    if show_favs:
        target_list = [h for h in new_h if h.get("is_favorite", False)]
    else:
        target_list = new_h
        
    total = len(target_list)
    max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
    if page > max_page: page = max_page
    
    new_gallery = get_gallery_display_data(new_h, current_config, page, show_favs)
    new_label = get_page_label(page, new_h, show_favs)

    # 削除後は選択状態を解除する（複雑さを避けるため）
    new_idx = idx
    # if new_idx >= len(new_h):
    #     new_idx = len(new_h) - 1
    
    return (
        new_h, new_gallery, -1, 
        "", "", "", "", "", "", "", "", "",
        "", "", 0.0,
        gr.update(visible=False),  # Delete
        gr.update(visible=False), # Confirm
        gr.update(visible=False),  # Restore
        gr.update(visible=False),  # Send to Chat
        gr.update(visible=False),  # Send to LLLite
        gr.update(visible=False),  # TagAccordion
        gr.update(visible=False),  # NegPromptAccordion
        gr.update(visible=False),  # PosAccordion
        gr.update(visible=False),  # ModelsAccordion
        page, new_label,          # Page State & Label
        gr.update(visible=False, value=None),
        gr.update(visible=False)
    )

def handle_clear_history(history):
    current_config = config_utils.load_config()
    history_utils.clear_history(current_config)
    return [], [], "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), 0, get_page_label(0, [], False), gr.update(visible=False, value=None), gr.update(visible=False)

def append_prompt(current, added):
    if not added: return current
    if not current: return added
    text = current.strip()
    if text.endswith(","):
        return text + " " + added
    return text + ", " + added

def restart_app(app_name):
    system_manager.restart_gradio(app_name)

def backup_history_action(config):
    return f"✅ {history_utils.backup_history(config)[1]}"

def next_page(page, history, config, show_favs):
    if show_favs:
        target_list = [h for h in history if h.get("is_favorite", False)]
    else:
        target_list = history
        
    total = len(target_list)
    max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
    new_page = min(page + 1, max_page)
    return new_page, get_gallery_display_data(history, config, new_page, show_favs), get_page_label(new_page, history, show_favs)

def prev_page(page, history, config, show_favs):
    new_page = max(0, page - 1)
    return new_page, get_gallery_display_data(history, config, new_page, show_favs), get_page_label(new_page, history, show_favs)

def toggle_favorite(idx, history, config, show_favs, page):
    if idx < 0 or idx >= len(history):
        return gr.update(), history, gr.update(), gr.update()
    
    item = history[idx]
    new_state = not item.get("is_favorite", False)
    item["is_favorite"] = new_state
    
    # 保存
    history_utils.save_history_json(config, history)
    
    # UI更新用
    fav_label = "❤ Liked" if new_state else "🤍 Like"
    fav_variant = "primary" if new_state else "secondary"
    
    # フィルタリング中にお気に入りを解除した場合、リストから消えるためギャラリー更新が必要
    # ただし、即座に消えると操作しづらい場合もあるが、整合性のため更新する
    if show_favs and not new_state:
        # ページ範囲チェック
        target_list = [h for h in history if h.get("is_favorite", False)]
        total = len(target_list)
        max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
        if page > max_page: page = max_page
        
        return gr.update(value=fav_label, variant=fav_variant), history, get_gallery_display_data(history, config, page, show_favs), get_page_label(page, history, show_favs)
    
    return gr.update(value=fav_label, variant=fav_variant), history, gr.update(), gr.update()

def toggle_fav_filter(current_state, history, config):
    new_state = not current_state
    btn_label = "❤ Favorites Only" if not new_state else "Show All"
    # フィルタ切り替え時はページ0に戻す
    return new_state, get_gallery_display_data(history, config, 0, new_state), 0, get_page_label(0, history, new_state), btn_label
