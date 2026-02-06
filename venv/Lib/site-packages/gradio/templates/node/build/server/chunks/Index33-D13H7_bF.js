import './async-Djx13DAD.js';
import { b as spread_props, a as attr } from './index-B7gr0Dsc.js';
import './2-BcDJ5I6-.js';
import { g } from './utils.svelte-D8Xdzglu.js';
import { G } from './Block-2-03Azgw.js';
import { c } from './BlockTitle-BMhqhFUP.js';
import './MarkdownCode.svelte_svelte_type_style_lang-CEOwFz9S.js';
import { R } from './index3-DJJ90pOI.js';
import { e as escape_html } from './escaping-CBnpiEl5.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';
import './index5-BoOEKc6P.js';
import './dev-fallback-Bc5Ork7Y.js';
import './Info-BkROehVS.js';
import './MarkdownCode-C4GlXfPx.js';
import './index35-CkjPw9xb.js';
import 'path';
import 'url';
import 'fs';
import './prism-python-nJ51fapt.js';
import './spring-DyDQVd5U.js';
import './IconButton-7VBZdgpA.js';
import './Clear-CiR-WD8W.js';

let f=0;function j(r,o){r.component(m=>{let{$$slots:b,$$events:_,...u}=o,e=new g(u);e.props.value,e.props.value;const p=`range_id_${f++}`;let n=e.props.minimum??0;(()=>{const t=e.props.minimum,a=e.props.maximum,i=e.props.value;return i>a?100:i<t?0:(i-t)/(a-t)*100})();let l=!e.shared.interactive;G(m,{visible:e.shared.visible,elem_id:e.shared.elem_id,elem_classes:e.shared.elem_classes,container:e.shared.container,scale:e.shared.scale,min_width:e.shared.min_width,children:t=>{R(t,spread_props([{autoscroll:e.shared.autoscroll,i18n:e.i18n},e.shared.loading_status,{on_clear_status:()=>e.dispatch("clear_status",e.shared.loading_status)}])),t.push(`<!----> <div class="wrap svelte-8epfm4"><div class="head svelte-8epfm4"><label${attr("for",p)} class="svelte-8epfm4">`),c(t,{show_label:e.shared.show_label,info:e.props.info,children:a=>{a.push(`<!---->${escape_html(e.shared.label||"Slider")}`);},$$slots:{default:true}}),t.push(`<!----></label> <div class="tab-like-container svelte-8epfm4"><input${attr("aria-label",`number input for ${e.shared.label}`)} data-testid="number-input" type="number"${attr("value",e.props.value)}${attr("min",e.props.minimum)}${attr("max",e.props.maximum)}${attr("step",e.props.step)}${attr("disabled",l,true)} class="svelte-8epfm4"/> `),e.props.buttons?.includes("reset")??true?(t.push("<!--[-->"),t.push(`<button class="reset-button svelte-8epfm4"${attr("disabled",l,true)} aria-label="Reset to default value" data-testid="reset-button">↺</button>`)):t.push("<!--[!-->"),t.push(`<!--]--></div></div> <div class="slider_input_container svelte-8epfm4"><span class="min_value svelte-8epfm4">${escape_html(n)}</span> <input type="range"${attr("id",p)} name="cowbell"${attr("value",e.props.value)}${attr("min",e.props.minimum)}${attr("max",e.props.maximum)}${attr("step",e.props.step)}${attr("disabled",l,true)}${attr("aria-label",`range slider for ${e.shared.label}`)} class="svelte-8epfm4"/> <span class="max_value svelte-8epfm4">${escape_html(e.props.maximum)}</span></div></div>`);},$$slots:{default:true}});});}

export { j as default };
//# sourceMappingURL=Index33-D13H7_bF.js.map
