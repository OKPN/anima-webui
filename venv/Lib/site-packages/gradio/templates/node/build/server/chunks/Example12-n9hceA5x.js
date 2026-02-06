import { f as fallback } from './async-Djx13DAD.js';
import { d as attr_class, c as bind_props } from './index-B7gr0Dsc.js';
import { e as escape_html } from './escaping-CBnpiEl5.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';

function r(c,e){c.component(d=>{let i=e.value,t=e.type,n=fallback(e.selected,false),s$1=e.choices,m=i.map(a=>s$1.find(f=>f[1]===a)?.[0]).filter(a=>a!==void 0).join(", ");d.push(`<div${attr_class("svelte-25nhtv",void 0,{table:t==="table",gallery:t==="gallery",selected:n})}>${escape_html(m)}</div>`),bind_props(e,{value:i,type:t,selected:n,choices:s$1});});}

export { r as default };
//# sourceMappingURL=Example12-n9hceA5x.js.map
