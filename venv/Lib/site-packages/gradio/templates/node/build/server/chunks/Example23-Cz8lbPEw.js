import './async-Djx13DAD.js';
import { d as attr_class, e as ensure_array_like, a as attr } from './index-B7gr0Dsc.js';
import { c } from './Image-Bw5_tidM.js';
import './2-BcDJ5I6-.js';
import './MarkdownCode.svelte_svelte_type_style_lang-CEOwFz9S.js';
import { Q as Qu } from './Video2-pxW-QOKm.js';
import { e as escape_html } from './escaping-CBnpiEl5.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';
import './index5-BoOEKc6P.js';
import './dev-fallback-Bc5Ork7Y.js';
import './prism-python-nJ51fapt.js';

function I(o,e){o.component(t=>{let{value:l={text:"",files:[]},type:a,selected:u=false}=e;t.push(`<div${attr_class("container svelte-xz0m7l",void 0,{table:a==="table",gallery:a==="gallery",selected:u,border:l})}><p>${escape_html(l.text?l.text:"")}</p> <!--[-->`);const m=ensure_array_like(l.files);for(let p=0,c$1=m.length;p<c$1;p++){let s$1=m[p];s$1.mime_type&&s$1.mime_type.includes("image")?(t.push("<!--[-->"),c(t,{src:s$1.url})):(t.push("<!--[!-->"),s$1.mime_type&&s$1.mime_type.includes("video")?(t.push("<!--[-->"),Qu(t,{src:s$1.url,alt:"",loop:true,is_stream:false})):(t.push("<!--[!-->"),s$1.mime_type&&s$1.mime_type.includes("audio")?(t.push("<!--[-->"),t.push(`<audio${attr("src",s$1.url)} controls></audio>`)):(t.push("<!--[!-->"),t.push(`${escape_html(s$1.orig_name)}`)),t.push("<!--]-->")),t.push("<!--]-->")),t.push("<!--]-->");}t.push("<!--]--></div>");});}

export { I as default };
//# sourceMappingURL=Example23-Cz8lbPEw.js.map
