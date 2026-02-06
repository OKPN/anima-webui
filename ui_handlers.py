import gradio as gr
import generation_manager
import system_manager
import config_utils
import history_utils
import pandas as pd
from urllib.parse import urlparse

def clean_url(url):
    if not url: return ""
    return str(url).strip().rstrip("/")

GALLERY_PER_PAGE = 60

def get_gallery_display_data(history, config, page=0):
    start = page * GALLERY_PER_PAGE
    end = start + GALLERY_PER_PAGE
    subset = history[start:end]
    return [(history_utils.resolve_thumbnail_path(item, config), item.get("caption", "")) for item in subset]

def get_page_label(page, history):
    total = len(history)
    max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
    return f"Page {page + 1} / {max_page + 1} (Total: {total})"

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

def handle_save_settings(url, bat_path, backup_path, real_out_path, q_tags_str, d_tags_str, t_tags_str, m_tags_str, s_tags_str, c_tags_str, res_df, neg_prompt, ext_name, ext_url):
    q_list, q_def = parse_tagged_str(q_tags_str)
    d_list, d_def = parse_tagged_str(d_tags_str)
    t_list, t_def = parse_tagged_str(t_tags_str)
    m_list, m_def = parse_tagged_str(m_tags_str)
    s_list, s_def = parse_tagged_str(s_tags_str)
    c_list, c_def = parse_tagged_str(c_tags_str)
    
    success = config_utils.update_and_save_config_v2(
        url, bat_path, backup_path, real_out_path, 
        q_list, q_def, d_list, d_def, t_list, t_def, m_list, m_def, s_list, s_def, c_list, c_def,
        res_df, neg_prompt, ext_name, ext_url
    )
    return "✅ 保存完了。再起動後に反映されます。" if success else "❌ 保存失敗。"

def predict(prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, history, quality_tags, 
            y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, decade_tags, period_tags, meta_tags, safety_tags, custom_tags, current_comfy_url,
            config, workflow_file):
    
    output_image, status, saved_entry = generation_manager.generate_and_save(
        prompt, neg_prompt, seed, randomize_seed, cfg, steps, width, height, sampler_name, 
        quality_tags, y1_en, y1_val, y2_en, y2_val, y3_en, y3_val, 
        decade_tags, period_tags, meta_tags, safety_tags, custom_tags, 
        current_comfy_url, workflow_file, config
    )
    if saved_entry:
        history.insert(0, saved_entry)
        # 生成後は1ページ目(index 0)に戻す
        return output_image, status, history, get_gallery_display_data(history, config, 0), 0, get_page_label(0, history)
    return output_image, status, history, gr.update(), gr.update(), gr.update()

def check_server_status(url):
    target = clean_url(url)
    try:
        parsed = urlparse(target)
        return "🟢 Running" if system_manager.check_comfy_status(parsed.hostname or "127.0.0.1", parsed.port or 8188) else "🔴 Stopped"
    except: return "❌ Error"

def launch_server(bat, url):
    if not bat: return "❌ Path is empty."
    return system_manager.launch_comfy(bat, clean_url(url)) or "🚀 Process Started"

def on_image_select(evt: gr.SelectData, history, page, config):
    # ページネーションを考慮したインデックス計算
    real_index = (page * GALLERY_PER_PAGE) + evt.index
    
    if not history or real_index >= len(history): 
        return [
            -1, "", "", "", "", "", "", "", "", 
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), 
            gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
            gr.update(visible=False, value=None)
        ]
    
    item = history[real_index]
    q = ", ".join(item.get("quality_tags", []))
    d = ", ".join(item.get("decade_tags", []))
    p = ", ".join(item.get("period_tags", []))
    m = ", ".join(item.get("meta_tags", []))
    s = ", ".join(item.get("safety_tags", []))
    c = ", ".join(item.get("custom_tags", []))
    
    original_image_path = history_utils.resolve_image_path(item, config)
    
    return [
        real_index,
        q, d, p, m, s, c, 
        item.get("prompt", ""),
        item.get("neg_prompt", ""),
        gr.update(visible=True),  # Delete
        gr.update(visible=False), # Confirm
        gr.update(visible=True),  # Restore
        gr.update(visible=True),  # TagAccordion
        gr.update(visible=True),  # Prompt
        gr.update(visible=True),  # NegPromptAccordion
        gr.update(visible=True, value=original_image_path)
    ]

def restore_from_history_by_index(idx, history):
    if idx < 0 or not history or idx >= len(history): return [gr.update()] * 22
    s = history[idx]
    return (
        s["prompt"], s["neg_prompt"], s["seed"], True, s["cfg"], s["steps"], s["width"], s["height"], 
        s.get("sampler_name", "euler_ancestral"), s.get("quality_tags", []),
        s.get("y1_en", False), s.get("y1_val", "2026"), s.get("y2_en", False), s.get("y2_val", "2025"),
        s.get("y3_en", False), s.get("y3_val", "2024"),
        s.get("decade_tags", []), s.get("period_tags", []), s.get("meta_tags", []), s.get("safety_tags", []),
        s.get("custom_tags", []), gr.update(selected=0)
    )

def load_latest_history_on_load():
    current_cfg = config_utils.load_config() 
    hist = history_utils.load_history(current_cfg)
    # 初期ロード時はページ0
    return hist, get_gallery_display_data(hist, current_cfg, 0), 0, get_page_label(0, hist)

def load_history_state_only():
    """起動時用: 内部データだけ更新し、重いギャラリー描画はスキップする"""
    current_cfg = config_utils.load_config() 
    hist = history_utils.load_history(current_cfg)
    # Galleryは gr.update() で「変更なし」を返す
    return hist, gr.update(), 0, get_page_label(0, hist)

def handle_delete_entry(idx, history, page):
    if idx < 0: 
        return (history, gr.update(), -1, "", "", "", "", "", "", "", "",
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                page, gr.update(),
                gr.update(visible=False, value=None))
    
    current_config = config_utils.load_config()
    new_h = history_utils.delete_history_entry(current_config, history, idx)
    
    if not new_h:
        return (new_h, [], -1, "", "", "", "", "", "", "", "",
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False),
                0, get_page_label(0, []),
                gr.update(visible=False, value=None))
    
    # 削除後にページ範囲外にならないよう調整
    total = len(new_h)
    max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
    if page > max_page: page = max_page
    
    new_gallery = get_gallery_display_data(new_h, current_config, page)
    new_label = get_page_label(page, new_h)

    new_idx = idx
    if new_idx >= len(new_h):
        new_idx = len(new_h) - 1
    
    item = new_h[new_idx]
    q = ", ".join(item.get("quality_tags", []))
    d = ", ".join(item.get("decade_tags", []))
    p = ", ".join(item.get("period_tags", []))
    m = ", ".join(item.get("meta_tags", []))
    s = ", ".join(item.get("safety_tags", []))
    c = ", ".join(item.get("custom_tags", []))
    prompt = item.get("prompt", "")
    neg = item.get("neg_prompt", "")
    
    original_image_path = history_utils.resolve_image_path(item, current_config)
    
    return (
        new_h, new_gallery, new_idx, 
        q, d, p, m, s, c, prompt, neg,
        gr.update(visible=True),  # Delete
        gr.update(visible=False), # Confirm
        gr.update(visible=True),  # Restore
        gr.update(visible=True),  # TagAccordion
        gr.update(visible=True),  # PromptPreview
        gr.update(visible=True),  # NegPromptAccordion
        page, new_label,          # Page State & Label
        gr.update(visible=True, value=original_image_path)
    )

def handle_clear_history(history):
    current_config = config_utils.load_config()
    history_utils.clear_history(current_config)
    return [], [], "", gr.update(visible=False), gr.update(visible=False), gr.update(visible=True), 0, get_page_label(0, []), gr.update(visible=False, value=None)

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

def next_page(page, history, config):
    total = len(history)
    max_page = max(0, (total - 1) // GALLERY_PER_PAGE)
    new_page = min(page + 1, max_page)
    return new_page, get_gallery_display_data(history, config, new_page), get_page_label(new_page, history)

def prev_page(page, history, config):
    new_page = max(0, page - 1)
    return new_page, get_gallery_display_data(history, config, new_page), get_page_label(new_page, history)
