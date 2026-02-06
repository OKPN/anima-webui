import './async-Djx13DAD.js';
import { b as spread_props } from './index-B7gr0Dsc.js';
import './2-BcDJ5I6-.js';
import { g } from './utils.svelte-D8Xdzglu.js';
import { a, P as u } from './Plot-BB92vav8.js';
import { G } from './Block-2-03Azgw.js';
import './MarkdownCode.svelte_svelte_type_style_lang-CEOwFz9S.js';
import { k } from './BlockLabel-DYKzuObf.js';
import { y } from './IconButtonWrapper-DlgTGGi-.js';
import { v } from './FullscreenButton-BWDCMn7M.js';
import { R } from './index3-DJJ90pOI.js';
import './escaping-CBnpiEl5.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';
import './index5-BoOEKc6P.js';
import './dev-fallback-Bc5Ork7Y.js';
import './Empty-uaeWNu3s.js';
import './prism-python-nJ51fapt.js';
import './IconButton-7VBZdgpA.js';
import './Maximize-DxOGYNPn.js';
import './spring-DyDQVd5U.js';
import './Clear-CiR-WD8W.js';

function E(i,n){i.component(p=>{let{$$slots:B,$$events:k$1,...u$1}=n;const s$1=new g(u$1);let l=false,e=true,a$1;function r(c){G(c,{padding:false,elem_id:s$1.shared.elem_id,elem_classes:s$1.shared.elem_classes,visible:s$1.shared.visible,container:s$1.shared.container,scale:s$1.shared.scale,min_width:s$1.shared.min_width,allow_overflow:false,get fullscreen(){return l},set fullscreen(o){l=o,e=false;},children:o=>{k(o,{show_label:s$1.shared.show_label,label:s$1.shared.label||s$1.i18n("plot.plot"),Icon:u}),o.push("<!----> "),s$1.props.buttons&&s$1.props.buttons.length>0||s$1.props.show_fullscreen_button?(o.push("<!--[-->"),y(o,{buttons:s$1.props.buttons??[],on_custom_button_click:t=>{s$1.dispatch("custom_button_click",{id:t});},children:t=>{s$1.props.show_fullscreen_button?(t.push("<!--[-->"),v(t,{fullscreen:l})):t.push("<!--[!-->"),t.push("<!--]-->");}})):o.push("<!--[!-->"),o.push("<!--]--> "),R(o,spread_props([{autoscroll:s$1.shared.autoscroll,i18n:s$1.i18n},s$1.shared.loading_status,{on_clear_status:()=>s$1.dispatch("clear_status",s$1.shared.loading_status)}])),o.push("<!----> "),a(o,{value:s$1.props.value,theme_mode:s$1.props.theme_mode,show_label:s$1.shared.show_label,caption:s$1.props.caption,bokeh_version:s$1.props.bokeh_version,show_actions_button:s$1.props.show_actions_button,_selectable:s$1.props._selectable,x_lim:s$1.props.x_lim,show_fullscreen_button:s$1.props.show_fullscreen_button,on_change:()=>s$1.dispatch("change")}),o.push("<!---->");},$$slots:{default:true}});}do e=true,a$1=p.copy(),r(a$1);while(!e);p.subsume(a$1);});}

export { a as BasePlot, E as default };
//# sourceMappingURL=Index16-CkpvFIc-.js.map
