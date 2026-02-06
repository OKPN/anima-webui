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