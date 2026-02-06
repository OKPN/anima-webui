import json

def get_js_emphasis(delta, elem_id="prompt_input_area"):
    """プロンプトの強調ウェイトを増減させるJavaScriptコードを生成する"""
    return f"""
    () => {{
        const delta = {delta};
        const ta = document.querySelector('#{elem_id} textarea');
        if (!ta) return;
        
        let start = ta.selectionStart;
        let end = ta.selectionEnd;
        let txt = ta.value;
        
        function replace(s, e, replacement) {{
            let newFull = txt.substring(0, s) + replacement + txt.substring(e);
            ta.value = newFull;
            ta.dispatchEvent(new Event('input', {{ bubbles: true }}));
            // 置換後は新しい文字列全体を選択状態にする（連続操作のため）
            ta.setSelectionRange(s, s + replacement.length);
            ta.focus();
        }}

        let targetStart = -1;
        let targetEnd = -1;
        let content = "";
        let weight = 0.0; // デフォルト (括弧なし状態)

        // 1. 選択範囲がある場合、その文字列自体が (...) かチェック
        if (start !== end) {{
            let selText = txt.substring(start, end);
            if (selText.startsWith('(') && selText.endsWith(')')) {{
                let inside = selText.substring(1, selText.length - 1);
                let lastColon = inside.lastIndexOf(':');
                
                let wParsed = NaN;
                if (lastColon !== -1) {{
                    wParsed = parseFloat(inside.substring(lastColon + 1));
                }}

                if (!isNaN(wParsed)) {{
                    // (text:0.1) の形式
                    weight = wParsed;
                    content = inside.substring(0, lastColon);
                    targetStart = start;
                    targetEnd = end;
                }} else {{
                    // (text) の形式 -> ComfyUI標準では1.1相当だが、ここでは解析不能として扱うか、
                    // あるいは 1.1 として扱う。ユーザー基準に合わせるなら一旦無視して中身だけ抽出も可だが、
                    // 既存の括弧を尊重して 1.1 スタートとする
                    weight = 1.1;
                    content = inside;
                    targetStart = start;
                    targetEnd = end;
                }}
            }}
        }}

        // 2. まだ特定できていない場合、カーソル位置周辺の括弧を探す
        if (targetStart === -1) {{
            let openIdx = txt.lastIndexOf('(', Math.min(start, end) - 1);
            if (openIdx !== -1) {{
                let closeIdx = txt.indexOf(')', openIdx);
                // カーソルが括弧の範囲内（境界含む）にあるか
                if (closeIdx !== -1 && closeIdx >= Math.max(start, end) - 1) {{
                    let inside = txt.substring(openIdx + 1, closeIdx);
                    let lastColon = inside.lastIndexOf(':');
                    let wParsed = NaN;
                    if (lastColon !== -1) {{
                        wParsed = parseFloat(inside.substring(lastColon + 1));
                    }}
                    
                    if (!isNaN(wParsed)) {{
                        weight = wParsed;
                        content = inside.substring(0, lastColon);
                    }} else {{
                        weight = 1.1;
                        content = inside;
                    }}
                    targetStart = openIdx;
                    targetEnd = closeIdx + 1;
                }}
            }}
        }}
        
        // 3. それでも特定できない場合、カーソル位置の単語または選択範囲を新規対象とする
        if (targetStart === -1) {{
            if (start !== end) {{
                content = txt.substring(start, end);
                targetStart = start;
                targetEnd = end;
            }} else {{
                let s = start;
                // カンマまたは改行が見つかるまで戻る (スペースや括弧は無視してフレーズ全体を取る)
                while (s > 0 && !/[,\\n]/.test(txt[s-1])) s--;
                let e = end;
                // カンマまたは改行が見つかるまで進む
                while (e < txt.length && !/[,\\n]/.test(txt[e])) e++;
                
                // 範囲内の前後の空白を除去して、実体のある部分だけを対象にする
                while (s < e && /\\s/.test(txt[s])) s++;
                while (e > s && /\\s/.test(txt[e-1])) e--;

                if (s < e) {{
                    content = txt.substring(s, e);
                    targetStart = s;
                    targetEnd = e;
                }} else {{
                    return;
                }}
            }}
            weight = 0.0;
        }}
        
        weight += delta;
        weight = Math.round(weight * 10) / 10;
        
        // 0.0 になったら括弧を外す、それ以外は (text:x.x) にする
        // 浮動小数点の誤差を考慮して判定
        let newStr = (Math.abs(weight) < 0.001) ? content : `(${{content}}:${{weight}})`;
        replace(targetStart, targetEnd, newStr);
    }}
    """

def get_autocomplete_js(all_tags, target_ids):
    """
    オートコンプリート機能を有効化するJavaScriptコードを生成する。
    all_tags: 候補となるタグのリスト (Python list)
    target_ids: 対象のGradio TextboxのElem IDのリスト (例: ["prompt_input_area", "neg_prompt_input_area"])
    """
    # タグデータをJSON文字列としてJSに埋め込む (1回のみ)
    tags_json = json.dumps(all_tags)
    target_ids_json = json.dumps(target_ids)

    return f"""
    () => {{
        const TAGS = {tags_json};
        const TARGET_IDS = {target_ids_json};
        const MAX_CANDIDATES = 20;

        // グローバル初期化チェック
        if (window._ac_global_initialized) return;
        window._ac_global_initialized = true;

        function setupAutocomplete(targetId) {{
            const container = document.querySelector('#' + targetId);
            if (!container) return;
            
            const textarea = container.querySelector("textarea");
            if (!textarea) return;

            // 候補表示用のリスト要素を作成
            const suggestionBox = document.createElement("ul");
            suggestionBox.id = "ac-suggestion-box-" + targetId;
            suggestionBox.style.position = "fixed";
            suggestionBox.style.display = "none";
            suggestionBox.style.zIndex = "9999";
            suggestionBox.style.backgroundColor = "var(--background-fill-primary)";
            suggestionBox.style.border = "1px solid var(--border-color-primary)";
            suggestionBox.style.borderRadius = "4px";
            suggestionBox.style.padding = "0";
            suggestionBox.style.margin = "0";
            suggestionBox.style.listStyle = "none";
            suggestionBox.style.maxHeight = "300px";
            suggestionBox.style.overflowY = "auto";
            suggestionBox.style.boxShadow = "0 4px 6px rgba(0,0,0,0.3)";
            suggestionBox.style.width = "250px";
            document.body.appendChild(suggestionBox);

            let currentFocus = -1;
            let currentCandidates = [];

            // キャレット座標取得用のミラーDivを作成
            const mirrorDiv = document.createElement("div");
            mirrorDiv.style.position = "absolute";
            mirrorDiv.style.top = "0";
            mirrorDiv.style.left = "0";
            mirrorDiv.style.visibility = "hidden";
            mirrorDiv.style.whiteSpace = "pre-wrap";
            mirrorDiv.style.wordWrap = "break-word";
            document.body.appendChild(mirrorDiv);

            function getCaretCoordinates() {{
                const style = window.getComputedStyle(textarea);
                ['fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'letterSpacing', 'lineHeight', 'textTransform', 'wordSpacing', 'textIndent', 'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft', 'borderWidth', 'boxSizing', 'width'].forEach(prop => {{
                    mirrorDiv.style[prop] = style[prop];
                }});
                
                const text = textarea.value.substring(0, textarea.selectionStart);
                const span = document.createElement("span");
                span.textContent = text;
                mirrorDiv.textContent = "";
                mirrorDiv.appendChild(span);
                
                const span2 = document.createElement("span");
                span2.textContent = ".";
                mirrorDiv.appendChild(span2);
                
                const rect = textarea.getBoundingClientRect();
                return {{
                    top: rect.top + span2.offsetTop - textarea.scrollTop,
                    left: rect.left + span2.offsetLeft - textarea.scrollLeft
                }};
            }}

            function closeList() {{
                suggestionBox.style.display = "none";
                currentFocus = -1;
                currentCandidates = [];
            }}

            function insertTag(tag) {{
                const text = textarea.value;
                const cursor = textarea.selectionStart;
                
                // カーソル直前の単語範囲を探す
                let start = cursor - 1;
                while (start >= 0 && !/[,\\n]/.test(text[start])) start--;
                start++; // 区切り文字の次へ

                // 既存の入力文字を置換
                const before = text.substring(0, start);
                const after = text.substring(cursor);
                
                // 前の文字がスペースでなければスペースを追加（行頭などは除く）
                let prefix = "";
                if (start > 0 && text[start-1] !== " " && text[start-1] !== "\\n") {{
                    // カンマの後ろならスペースを入れる
                    if (text[start-1] === ",") prefix = " ";
                }}

                const newText = before + prefix + tag + ", " + after;
                textarea.value = newText;
                
                // イベント発火
                textarea.dispatchEvent(new Event("input", {{ bubbles: true }}));
                
                // カーソル移動
                const newCursor = start + prefix.length + tag.length + 2;
                textarea.setSelectionRange(newCursor, newCursor);
                textarea.focus();
                closeList();
            }}

            function updateList(query) {{
                suggestionBox.innerHTML = "";
                currentFocus = -1;
                
                if (!query) {{
                    closeList();
                    return;
                }}

                // 部分一致検索 (先頭一致を優先してもよい)
                const q = query.toLowerCase().trim();
                // スペースを含むタグも考慮し、単純なincludes検索
                // パフォーマンスのため、ヒット数が上限を超えたら打ち切り
                currentCandidates = [];
                for (let tag of TAGS) {{
                    if (tag.includes(q)) {{
                        currentCandidates.push(tag);
                        if (currentCandidates.length >= MAX_CANDIDATES) break;
                    }}
                }}

                if (currentCandidates.length === 0) {{
                    closeList();
                    return;
                }}

                currentCandidates.forEach((tag, index) => {{
                    const li = document.createElement("li");
                    li.textContent = tag;
                    li.style.padding = "4px 8px";
                    li.style.cursor = "pointer";
                    li.style.borderBottom = "1px solid var(--border-color-primary)";
                    
                    li.addEventListener("click", () => insertTag(tag));
                    li.addEventListener("mouseover", () => {{
                        setActive(index);
                    }});
                    
                    suggestionBox.appendChild(li);
                }});

                const coords = getCaretCoordinates();
                suggestionBox.style.top = (coords.top + 24) + "px"; // 少し下に表示
                suggestionBox.style.left = coords.left + "px";
                suggestionBox.style.display = "block";
                
                setActive(0);
            }}

            function setActive(index) {{
                const items = suggestionBox.getElementsByTagName("li");
                for (let i = 0; i < items.length; i++) {{
                    items[i].style.backgroundColor = i === index ? "var(--secondary-500)" : "transparent";
                    items[i].style.color = i === index ? "white" : "var(--body-text-color)";
                }}
                currentFocus = index;
            }}

            textarea.addEventListener("input", () => {{
                const cursor = textarea.selectionStart;
                const text = textarea.value;
                
                // カーソル直前の「カンマまたは改行」までの文字列を取得
                let start = cursor - 1;
                while (start >= 0 && !/[,\\n]/.test(text[start])) start--;
                start++; 
                
                const currentWord = text.substring(start, cursor).trim();
                
                // 2文字以上入力したら補完開始
                if (currentWord.length >= 2) {{
                    updateList(currentWord);
                }} else {{
                    closeList();
                }}
            }});

            textarea.addEventListener("keydown", (e) => {{
                if (suggestionBox.style.display === "block") {{
                    if (e.key === "ArrowDown") {{
                        e.preventDefault();
                        currentFocus++;
                        if (currentFocus >= currentCandidates.length) currentFocus = 0;
                        setActive(currentFocus);
                    }} else if (e.key === "ArrowUp") {{
                        e.preventDefault();
                        currentFocus--;
                        if (currentFocus < 0) currentFocus = currentCandidates.length - 1;
                        setActive(currentFocus);
                    }} else if (e.key === "Enter" || e.key === "Tab") {{
                        if (currentFocus > -1) {{
                            e.preventDefault();
                            insertTag(currentCandidates[currentFocus]);
                        }}
                    }} else if (e.key === "Escape") {{
                        closeList();
                    }}
                }}
            }});

            // クリックで閉じる
            document.addEventListener("click", (e) => {{
                if (e.target !== textarea && e.target !== suggestionBox) {{
                    closeList();
                }}
            }});
        }}

        // 全ターゲットに対してセットアップ実行
        TARGET_IDS.forEach(id => setupAutocomplete(id));
    }}
    """