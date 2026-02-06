import './async-Djx13DAD.js';
import { b as spread_props } from './index-B7gr0Dsc.js';
import { t as tick } from './index-server-lqjMX237.js';
import { p as pt } from './Textbox-I_4BrUJH.js';
import { R } from './index3-DJJ90pOI.js';
import { G } from './Block-2-03Azgw.js';
import './MarkdownCode.svelte_svelte_type_style_lang-CEOwFz9S.js';
import './2-BcDJ5I6-.js';
import { g } from './utils.svelte-D8Xdzglu.js';
export { default as BaseExample } from './Example2-Bga9nSuW.js';
import './escaping-CBnpiEl5.js';
import './context-BZS6UlnY.js';
import './uneval-DjLoL4oF.js';
import './clone-BLo8hHdj.js';
import './BlockTitle-BMhqhFUP.js';
import './Info-BkROehVS.js';
import './MarkdownCode-C4GlXfPx.js';
import './index35-CkjPw9xb.js';
import 'path';
import 'url';
import 'fs';
import './IconButton-7VBZdgpA.js';
import './Check-THd8EJll.js';
import './Copy-DNPvPwdp.js';
import './Send-DqNOmoCe.js';
import './Square-DrWSae15.js';
import './IconButtonWrapper-DlgTGGi-.js';
import './spring-DyDQVd5U.js';
import './Clear-CiR-WD8W.js';
import './prism-python-nJ51fapt.js';
import './index5-BoOEKc6P.js';
import './dev-fallback-Bc5Ork7Y.js';

function A(p,i){p.component(l=>{let{$$slots:g$1,$$events:w,...n}=i;const s$1=new g(n);let u=s$1.shared.label||"Textbox";s$1.props.value=s$1.props.value??"",s$1.props.value;async function d(a){!s$1.shared||!s$1.props||(s$1.props.validation_error=null,s$1.props.value=a,await tick(),s$1.dispatch("input"));}function c(a){!s$1.shared||!s$1.props||(s$1.props.validation_error=null,s$1.props.value=a);}let e=true,r;function h(a){G(a,{visible:s$1.shared.visible,elem_id:s$1.shared.elem_id,elem_classes:s$1.shared.elem_classes,scale:s$1.shared.scale,min_width:s$1.shared.min_width,allow_overflow:false,padding:s$1.shared.container,rtl:s$1.props.rtl,children:o=>{s$1.shared.loading_status?(o.push("<!--[-->"),R(o,spread_props([{autoscroll:s$1.shared.autoscroll,i18n:s$1.i18n},s$1.shared.loading_status,{show_validation_error:false,on_clear_status:()=>s$1.dispatch("clear_status",s$1.shared.loading_status)}]))):o.push("<!--[!-->"),o.push("<!--]--> "),pt(o,{label:u,info:s$1.props.info,show_label:s$1.shared.show_label,lines:s$1.props.lines,type:s$1.props.type,rtl:s$1.props.rtl,text_align:s$1.props.text_align,max_lines:s$1.props.max_lines,placeholder:s$1.props.placeholder,submit_btn:s$1.props.submit_btn,stop_btn:s$1.props.stop_btn,buttons:s$1.props.buttons,autofocus:s$1.props.autofocus,container:s$1.shared.container,autoscroll:s$1.shared.autoscroll,max_length:s$1.props.max_length,html_attributes:s$1.props.html_attributes,validation_error:s$1.shared?.loading_status?.validation_error||s$1.shared?.validation_error,onchange:c,oninput:d,onsubmit:()=>{s$1.shared.validation_error=null,s$1.dispatch("submit");},onblur:()=>s$1.dispatch("blur"),onselect:t=>s$1.dispatch("select",t),onfocus:()=>s$1.dispatch("focus"),onstop:()=>s$1.dispatch("stop"),oncopy:t=>s$1.dispatch("copy",t),oncustombuttonclick:t=>{s$1.dispatch("custom_button_click",{id:t});},disabled:!s$1.shared.interactive,get value(){return s$1.props.value},set value(t){s$1.props.value=t,e=false;}}),o.push("<!---->");},$$slots:{default:true}});}do e=true,r=l.copy(),h(r);while(!e);l.subsume(r);});}

export { pt as BaseTextbox, A as default };
//# sourceMappingURL=Index18-Dxse-nhV.js.map
