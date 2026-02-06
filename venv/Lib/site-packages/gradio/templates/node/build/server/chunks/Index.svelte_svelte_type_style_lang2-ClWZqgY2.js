import './async-Djx13DAD.js';
import { d as attr_class, a as attr, g as attr_style, j as stringify } from './index-B7gr0Dsc.js';
import './2-BcDJ5I6-.js';
import { b } from './utils.svelte-D8Xdzglu.js';
import { e } from './Check-THd8EJll.js';
import { h } from './Copy-DNPvPwdp.js';
import { P } from './MarkdownCode-C4GlXfPx.js';
import { w } from './IconButton-7VBZdgpA.js';
import { y } from './IconButtonWrapper-DlgTGGi-.js';

function K(m,r){m.component(t=>{let{elem_classes:c=[],visible:f=true,value:e$1,min_height:s$1=void 0,rtl:u=false,sanitize_html:d=true,line_breaks:h$1=false,latex_delimiters:_=[],header_links:g=false,height:n=void 0,show_copy_button:v=false,loading_status:y$1=void 0,theme_mode:k,onchange:z=()=>{},oncopy:b$1=l=>{}}=r,o=false,a;async function w$1(){"clipboard"in navigator&&(await navigator.clipboard.writeText(e$1),b$1({value:e$1}),C());}function C(){o=true,a&&clearTimeout(a),a=setTimeout(()=>{o=false;},1e3);}t.push(`<div${attr_class(`prose ${stringify(c?.join(" ")||"")}`,"svelte-1xjkzpp",{hide:!f})} data-testid="markdown"${attr("dir",u?"rtl":"ltr")}${attr_style(n?`max-height: ${b(n)}; overflow-y: auto;`:"",{"min-height":s$1&&y$1?.status!=="pending"?b(s$1):void 0})}>`),v?(t.push("<!--[-->"),y(t,{children:l=>{w(l,{Icon:o?e:h,onclick:w$1,label:o?"Copied conversation":"Copy conversation"});}})):t.push("<!--[!-->"),t.push("<!--]--> "),P(t,{message:e$1,latex_delimiters:_,sanitize_html:d,line_breaks:h$1,chatbot:false,header_links:g,theme_mode:k}),t.push("<!----></div>");});}

export { K };
//# sourceMappingURL=Index.svelte_svelte_type_style_lang2-ClWZqgY2.js.map
