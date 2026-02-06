import { f as fallback } from './async-Djx13DAD.js';
import { d as attr_class, c as bind_props } from './index-B7gr0Dsc.js';
import { e as escape_html } from './escaping-CBnpiEl5.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';

function u(n,e){n.component(f=>{let t=e.value,a=e.type,c=fallback(e.selected,false),i=e.choices,s$1;if(t===null)s$1="";else {let d=i.find(m=>m[1]===t);s$1=d?d[0]:"";}f.push(`<div${attr_class("svelte-g2dls0",void 0,{table:a==="table",gallery:a==="gallery",selected:c})}>${escape_html(s$1)}</div>`),bind_props(e,{value:t,type:a,selected:c,choices:i});});}

export { u as default };
//# sourceMappingURL=Example26-B6QkjPTd.js.map
