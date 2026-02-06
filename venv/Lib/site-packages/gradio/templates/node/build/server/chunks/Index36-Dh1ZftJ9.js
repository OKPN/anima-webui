import './async-Djx13DAD.js';
import { b as spread_props, d as attr_class, g as attr_style, i as slot, c as bind_props } from './index-B7gr0Dsc.js';
import { G } from './Block-2-03Azgw.js';
import './MarkdownCode.svelte_svelte_type_style_lang-CEOwFz9S.js';
import './2-BcDJ5I6-.js';
import { g } from './utils.svelte-D8Xdzglu.js';
import { R } from './index3-DJJ90pOI.js';
import { e as escape_html } from './escaping-CBnpiEl5.js';
import { y } from './Index.svelte_svelte_type_style_lang-Bhqv9Lv_.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';
import './prism-python-nJ51fapt.js';
import './index5-BoOEKc6P.js';
import './dev-fallback-Bc5Ork7Y.js';
import './spring-DyDQVd5U.js';
import './IconButton-7VBZdgpA.js';
import './Clear-CiR-WD8W.js';

function v(p,l){p.component(a=>{let{open:e=true,label:n="",onexpand:d,oncollapse:s$1}=l;a.push(`<button${attr_class("label-wrap svelte-e5lyqv",void 0,{open:e})}><span class="svelte-e5lyqv">${escape_html(n)}</span> <span class="icon svelte-e5lyqv"${attr_style("",{transform:e?"rotate(0)":"rotate(90deg)"})}>▼</span></button> <div${attr_style("",{display:e?"block":"none"})}><!--[-->`),slot(a,l,"default",{},null),a.push("<!--]--></div>"),bind_props(l,{open:e});});}function C(p,l){p.component(a=>{let{$$slots:e,$$events:n,...d}=l;const s$1=new g(d);let u=s$1.shared.label||"";G(a,{elem_id:s$1.shared.elem_id,elem_classes:s$1.shared.elem_classes,visible:s$1.shared.visible,children:o=>{s$1.shared.loading_status?(o.push("<!--[-->"),R(o,spread_props([{autoscroll:s$1.shared.autoscroll,i18n:s$1.i18n},s$1.shared.loading_status]))):o.push("<!--[!-->"),o.push("<!--]--> "),v(o,{label:u,open:s$1.props.open,onexpand:()=>{s$1.dispatch("expand"),s$1.dispatch("gradio_expand");},oncollapse:()=>s$1.dispatch("collapse"),children:c=>{y(c,{children:i=>{i.push("<!--[-->"),slot(i,l,"default",{},null),i.push("<!--]-->");},$$slots:{default:true}});},$$slots:{default:true}}),o.push("<!---->");},$$slots:{default:true}});});}

export { C as default };
//# sourceMappingURL=Index36-Dh1ZftJ9.js.map
