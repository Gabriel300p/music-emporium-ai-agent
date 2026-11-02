"""Single-page UI served by `emporio_agent.web` (no external assets, no build step)."""

PAGE = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Empório da Música · Atendente virtual</title>
<style>
/* Layout: conversa à esquerda, "o que o agente consultou" à direita. Detalhes técnicos ficam recolhidos. */
:root{
  --bg:#f4f6f8; --surface:#ffffff; --fg:#17212b; --muted:#566574; --line:#d8dfe6;
  --accent:#3a4ec2; --accent-fg:#ffffff; --accent-soft:#e7eafb;
  --user:#e7eafb; --bot:#ffffff;
  --ok:#17794a; --ok-bg:#e1f2e9; --warn:#8a5a08; --warn-bg:#faedcf; --bad:#b3261e; --bad-bg:#fbe3e0;
  --code:#edf1f5;
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  color-scheme:light;
}
@media (prefers-color-scheme:dark){:root{
  --bg:#0e151c; --surface:#16202a; --fg:#e3e9ef; --muted:#97a6b5; --line:#2a3744;
  --accent:#8c9bff; --accent-fg:#0e151c; --accent-soft:#222a52; --user:#222a52; --bot:#16202a;
  --ok:#5ccf92; --ok-bg:#14301f; --warn:#efb24a; --warn-bg:#392c11; --bad:#ff8c82; --bad-bg:#3c1b19; --code:#1d2934;
  color-scheme:dark}}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 var(--sans);display:flex;flex-direction:column}
button,input,select,textarea{font:inherit;color:inherit}
a{color:var(--accent)}
header{background:var(--surface);border-bottom:1px solid var(--line);padding:10px 16px}
.bar{display:flex;flex-wrap:wrap;gap:8px 12px;align-items:center}
h1{font-size:1.02rem;margin:0 8px 0 0;font-weight:650}
h1 small{display:block;font-weight:400;font-size:.74rem;color:var(--muted)}
.seg{display:inline-flex;border:1px solid var(--line);border-radius:6px;overflow:hidden}
.seg button{border:0;background:var(--bg);padding:7px 12px;cursor:pointer;font-size:.88rem}
.seg button[aria-pressed=true]{background:var(--accent);color:var(--accent-fg);font-weight:600}
.btn{border:1px solid var(--line);background:var(--bg);border-radius:6px;padding:7px 12px;cursor:pointer;font-size:.88rem}
.btn:hover{border-color:var(--accent)}
.btn.primary{background:var(--accent);color:var(--accent-fg);border-color:var(--accent);font-weight:600}
.btn:disabled{opacity:.55;cursor:default}
.sp{flex:1}
.chip{display:inline-block;font-family:var(--mono);font-size:.72rem;padding:1px 7px;border-radius:4px;background:var(--code);color:var(--muted);white-space:nowrap}
.chip.ok{background:var(--ok-bg);color:var(--ok)} .chip.warn{background:var(--warn-bg);color:var(--warn)} .chip.bad{background:var(--bad-bg);color:var(--bad)}
.adv{margin-top:8px;font-size:.86rem}
.adv summary{cursor:pointer;color:var(--muted);display:inline-block}
.adv .row{display:flex;flex-wrap:wrap;gap:10px 16px;margin-top:8px;align-items:flex-end}
label.f{display:flex;flex-direction:column;font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);gap:2px}
select,input[type=text],input[type=password]{background:var(--bg);border:1px solid var(--line);border-radius:6px;padding:6px 8px;font-size:.9rem;min-width:0}
input#model{width:11rem}
.panel{margin-top:10px;padding:12px 14px;border:1px solid var(--line);border-radius:8px;background:var(--bg)}
.panel[hidden]{display:none}
.panel p{margin:0 0 8px;font-size:.88rem}
.keyrow{display:flex;gap:8px;flex-wrap:wrap}
.keyrow input{flex:1;min-width:14rem}
.banner{margin-top:8px;padding:7px 10px;border-radius:6px;font-size:.86rem}
.banner.warn{background:var(--warn-bg);color:var(--warn)} .banner.bad{background:var(--bad-bg);color:var(--bad)} .banner.info{background:var(--accent-soft);color:var(--accent)}
main{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr)}
section{display:flex;flex-direction:column;min-height:0;min-width:0}
section.chat{border-right:1px solid var(--line)}
section>h2{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:0;padding:10px 16px 6px;font-weight:600}
.scroll{flex:1;min-height:0;overflow-y:auto;padding:4px 16px 16px;display:flex;flex-direction:column;gap:10px}
.msg{max-width:88%;padding:9px 12px;border-radius:10px;border:1px solid var(--line);white-space:pre-wrap;overflow-wrap:anywhere}
.msg.user{align-self:flex-end;background:var(--user);border-color:transparent}
.msg.bot{align-self:flex-start;background:var(--bot)}
.msg.err{align-self:flex-start;background:var(--bad-bg);color:var(--bad);border-color:transparent}
.msg.pending{color:var(--muted)}
.welcome{border:1px solid var(--line);border-radius:10px;background:var(--surface);padding:14px 16px}
.welcome h3{margin:0 0 4px;font-size:1.02rem}
.welcome h4{margin:12px 0 2px;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
.welcome p,.welcome ul,.welcome ol{margin:4px 0;font-size:.9rem}
.welcome ul,.welcome ol{padding-left:20px}
.samples{border-top:1px solid var(--line);padding:6px 16px 0}
.samples summary{cursor:pointer;font-size:.78rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);padding:6px 0}
.sgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(15rem,1fr));gap:6px;padding:2px 0 8px;max-height:11rem;overflow-y:auto}
.sbtn{text-align:left;border:1px solid var(--line);background:var(--surface);border-radius:8px;padding:6px 10px;cursor:pointer;display:flex;flex-direction:column;gap:1px}
.sbtn:hover{border-color:var(--accent)} .sbtn:disabled{opacity:.55;cursor:default}
.sbtn span{font-size:.84rem;overflow-wrap:anywhere} .sbtn small{font-size:.72rem;color:var(--muted)}
form.composer{display:flex;gap:8px;padding:10px 16px 14px}
textarea{flex:1;resize:none;height:3.2rem;border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:var(--surface)}
.turn{border:1px solid var(--line);border-radius:8px;background:var(--surface);padding:10px 12px}
.turn h3{margin:0 0 6px;font-size:.82rem;display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-weight:600}
.turn h3 .q{font-weight:400;color:var(--muted);overflow-wrap:anywhere}
.meta{font-size:.76rem;color:var(--muted);margin:2px 0 6px}
.did{margin:4px 0 6px;font-size:.88rem}
details.t{border-top:1px solid var(--line);padding:6px 0}
details.t:first-of-type{border-top:0}
details.t summary{cursor:pointer;display:flex;gap:8px;align-items:center;font-size:.84rem}
pre{background:var(--code);border-radius:6px;padding:8px 10px;margin:6px 0;overflow:auto;max-height:18rem;font:.76rem/1.45 var(--mono);white-space:pre-wrap;overflow-wrap:anywhere}
.pre-label{font-size:.68rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin-top:6px}
.none{color:var(--muted);font-size:.86rem}
#status{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);background:var(--fg);color:var(--bg);padding:7px 12px;border-radius:6px;font-size:.85rem;max-width:90vw}
#status[hidden]{display:none}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
@media (max-width:860px){
  html,body{height:auto} body{display:block}
  main{display:block} section.chat{border-right:0;border-bottom:1px solid var(--line)}
  .scroll{max-height:none;overflow:visible} input#model{width:9rem}
}
@media (prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style>
</head>
<body>
<header>
  <div class="bar">
    <h1>Empório da Música<small>Atendente virtual · protótipo</small></h1>
    <div class="seg" role="group" aria-label="Modo de resposta">
      <button type="button" id="mode-llm" aria-pressed="true" title="O modelo de linguagem real decide o que consultar">Modelo real</button>
      <button type="button" id="mode-offline" aria-pressed="false" title="Respostas por regras simples, sem chave e sem custo">Offline</button>
    </div>
    <button type="button" class="btn" id="keybtn" aria-expanded="false" aria-controls="keypanel">Chave</button>
    <span class="chip" id="keychip"></span>
    <span class="sp"></span>
    <button type="button" class="btn" id="reset">Nova conversa</button>
    <button type="button" class="btn" id="export">Exportar .md</button>
  </div>
  <div class="panel" id="keypanel" hidden>
    <p><b>Chave da OpenAI.</b> O modo &ldquo;Modelo real&rdquo; precisa de uma chave de API da OpenAI (<a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">onde criar</a>). Sem chave, use o modo Offline.</p>
    <form class="keyrow" id="keyform" autocomplete="off">
      <input type="password" id="keyinput" placeholder="Cole a chave aqui" aria-label="Chave da OpenAI" autocomplete="off" spellcheck="false">
      <button class="btn primary" type="submit">Usar esta chave</button>
      <button class="btn" type="button" id="keyclear" hidden>Remover chave</button>
    </form>
    <p class="none" style="margin-top:8px">A chave fica só na memória deste programa, neste computador. Não é gravada em arquivo, não aparece nos logs nem na conversa exportada e só é enviada à API configurada.</p>
  </div>
  <details class="adv">
    <summary>Avançado: dados, modelo e endpoint</summary>
    <div class="row">
      <label class="f">Dados<select id="data"></select></label>
      <label class="f" id="model-wrap">Modelo<input type="text" id="model" list="models" autocomplete="off" spellcheck="false"></label>
      <datalist id="models"><option value="gpt-4.1-mini"><option value="gpt-4.1"><option value="gpt-4o-mini"></datalist>
      <span>Endpoint: <span class="chip" id="endpoint"></span></span>
    </div>
  </details>
  <div id="banners"></div>
</header>
<main>
  <section class="chat" aria-label="Conversa">
    <h2>Conversa</h2>
    <div class="scroll" id="log" aria-live="polite"></div>
    <details class="samples" id="samplebox" open>
      <summary>Perguntas para testar</summary>
      <div class="sgrid" id="samples"></div>
    </details>
    <form class="composer" id="form">
      <textarea id="msg" placeholder="Escreva como um cliente (Enter envia, Shift+Enter quebra a linha)" maxlength="2000" aria-label="Mensagem"></textarea>
      <button class="btn primary" id="send" type="submit">Enviar</button>
    </form>
  </section>
  <section aria-label="O que o agente consultou">
    <h2>O que o agente consultou</h2>
    <div class="scroll" id="tools"></div>
  </section>
</main>
<div id="status" role="status" hidden></div>
<script>
(function(){
"use strict";
var $=function(s){return document.querySelector(s)};
var cfg=null, sid=newSid(), turns=0, busy=false, mode="offline";
var TOOL_NAMES={search_products:"catálogo de produtos",search_promotions:"promoções",order_status:"pedidos",search_policies:"manual de políticas"};

function newSid(){var a=new Uint8Array(16);crypto.getRandomValues(a);return Array.prototype.map.call(a,function(b){return ("0"+b.toString(16)).slice(-2)}).join("")}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function flash(text){var s=$("#status");s.textContent=text;s.hidden=false;clearTimeout(flash.t);flash.t=setTimeout(function(){s.hidden=true},3800)}
function statusClass(s){
  if(s==="ok"||s==="verified")return "ok";
  if(s==="not_verified"||s==="verification_required"||s==="no_evidence")return "warn";
  return "bad";
}
function api(path,opts){
  return fetch(path,opts).then(function(r){
    var ct=r.headers.get("content-type")||"";
    return (ct.indexOf("json")>=0?r.json():r.text()).then(function(d){return {status:r.status,data:d,headers:r.headers}});
  });
}
function post(path,body){return api(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})}
function selected(){return cfg.sources.filter(function(s){return s.key===$("#data").value})[0]}

function renderBanners(){
  var box=$("#banners");box.textContent="";
  var src=selected();
  if(src&&src.private){
    if(mode==="llm")box.appendChild(el("div","banner bad","Fonte original no modo Modelo real: trechos do manual interno e dados de pedidos de clientes reais serão enviados à API."));
    else box.appendChild(el("div","banner info","Fonte original no modo Offline: nada sai desta máquina."));
  }
  if(mode==="llm"&&!cfg.endpoint_is_openai)box.appendChild(el("div","banner warn","O endpoint é "+cfg.endpoint_host+", não api.openai.com. Para usar a OpenAI, reinicie com --base-url https://api.openai.com/v1."));
}
function renderKey(){
  var k=$("#keychip");
  var label={ui:"chave: colada na tela",env:"chave: do ambiente",none:"sem chave"}[cfg.key_source]||"sem chave";
  k.textContent=label;k.className="chip "+(cfg.has_key?"ok":"warn");
  $("#keyclear").hidden=cfg.key_source!=="ui";
}
function toggleKeyPanel(show){
  var p=$("#keypanel");var open=show===undefined?p.hidden:show;
  p.hidden=!open;$("#keybtn").setAttribute("aria-expanded",String(open));
  if(open)$("#keyinput").focus();
}
function setMode(m){
  mode=m;
  $("#mode-llm").setAttribute("aria-pressed",String(m==="llm"));
  $("#mode-offline").setAttribute("aria-pressed",String(m==="offline"));
  $("#model-wrap").style.display=m==="llm"?"":"none";
  renderBanners();
  if(m==="llm"&&!cfg.has_key)toggleKeyPanel(true);
}
function li(parent,text){parent.appendChild(el("li",null,text))}
function welcome(note){
  var w=el("div","welcome");
  if(note)w.appendChild(el("p","none",note));
  w.appendChild(el("h3",null,"Olá! Eu sou o atendente virtual da Empório da Música."));
  w.appendChild(el("p",null,"Este é um protótipo para a equipe da loja em Campo Grande/MS. Converse como um cliente e veja, ao lado, o que eu consultei para responder."));
  w.appendChild(el("h4",null,"O que eu faço"));
  var a=el("ul");li(a,"Consulto preço, estoque e promoções do catálogo.");li(a,"Verifico o status de um pedido, com o número do pedido e o e-mail da compra.");li(a,"Respondo regras da loja (troca, devolução, horário, pagamento) com base no manual.");w.appendChild(a);
  w.appendChild(el("h4",null,"O que eu não faço"));
  var b=el("ul");li(b,"Não faço compras, trocas nem reembolsos: encaminho para a equipe.");li(b,"Não tenho dados em tempo real: o catálogo e os pedidos vêm de arquivos CSV.");li(b,"Não respondo assuntos fora da loja.");w.appendChild(b);
  w.appendChild(el("h4",null,"Como testar"));
  var c=el("ol");li(c,cfg.has_key?"A chave da OpenAI está configurada: o modo Modelo real já funciona.":"Para usar o modelo real, clique em Chave e cole a sua chave da OpenAI. Sem chave, o modo Offline responde por regras simples.");li(c,"Escolha uma pergunta em “Perguntas para testar” ou escreva a sua.");li(c,"Veja à direita quais fontes foram consultadas e, se quiser, a saída bruta como prova.");w.appendChild(c);
  var src=selected();
  w.appendChild(el("p","none","Dados em uso: "+(src?src.label:"")+(src&&!src.private?". São dados de teste sanitizados; o manual de políticas desta base é um documento sintético de uma página.":".")));
  return w;
}
function restart(note){
  sid=newSid();turns=0;
  var log=$("#log");log.textContent="";log.appendChild(welcome(note));
  var t=$("#tools");t.textContent="";t.appendChild(el("p","none","Nada ainda. Cada resposta lista aqui o que o agente consultou."));
  $("#samplebox").open=true;
}
function addMsg(cls,text){
  var w=$("#log .welcome");if(w)w.remove();
  var m=el("div","msg "+cls,text);var log=$("#log");log.appendChild(m);log.scrollTop=log.scrollHeight;return m;
}
function pretty(v){try{return JSON.stringify(v,null,2)}catch(e){return String(v)}}
function describe(c){
  var o=c.output||{},st=o.status;
  switch(c.tool){
    case "search_products":return st==="ok"?("Consultou o catálogo e encontrou "+o.matches+" produto(s)."):"Consultou o catálogo sem resultado utilizável.";
    case "search_promotions":return st==="ok"?("Consultou as promoções ativas: "+o.matches+" produto(s)."):"Consultou as promoções sem resultado.";
    case "order_status":
      if(st==="verified")return "Pedido e e-mail conferiram; o status foi liberado.";
      if(st==="not_verified")return "Pedido e e-mail não conferem; nenhum dado do pedido foi revelado.";
      return "Faltavam dados para verificar o pedido.";
    case "search_policies":return st==="ok"?("Consultou o manual e trouxe "+((o.results||[]).length)+" trecho(s), páginas "+(o.results||[]).map(function(r){return r.page}).join(", ")+"."):"Procurou no manual e não achou trecho relevante.";
  }
  return "Executou "+c.tool+".";
}
function renderTools(n,question,r){
  var box=$("#tools");var hint=box.querySelector(".none");if(hint&&!hint.classList.contains("keep"))hint.remove();
  var t=el("div","turn");
  var h=el("h3");h.appendChild(el("span",null,"Turno "+n));h.appendChild(el("span","q",question.length>70?question.slice(0,70)+"…":question));t.appendChild(h);
  var u=r.usage||{};
  t.appendChild(el("div","meta",mode==="llm"?(u.calls+" chamadas ao modelo · "+u.tokens_in+" tokens de entrada · "+u.tokens_out+" de saída · "+(r.seconds||0).toFixed(1)+" s"):("modo offline · "+(r.seconds||0).toFixed(2)+" s")));
  if(r.error)t.appendChild(el("div","msg err",r.error));
  var tools=r.tools||[];
  if(!tools.length&&!r.error)t.appendChild(el("div","none","Respondeu sem consultar nenhuma fonte."));
  tools.forEach(function(c,i){
    var d=el("details","t");if(i===0)d.open=true;
    var s=el("summary");s.appendChild(el("b",null,TOOL_NAMES[c.tool]||c.tool));
    var st=(c.output&&c.output.status)||"?";s.appendChild(el("span","chip "+statusClass(st),st));d.appendChild(s);
    d.appendChild(el("div","did",describe(c)));
    d.appendChild(el("div","pre-label","Argumentos enviados à ferramenta"));d.appendChild(el("pre",null,pretty(c.args)));
    d.appendChild(el("div","pre-label","Saída bruta (a prova)"));d.appendChild(el("pre",null,pretty(c.output)));
    t.appendChild(d);
  });
  box.appendChild(t);box.scrollTop=box.scrollHeight;
}
function setBusy(b){busy=b;$("#send").disabled=b;Array.prototype.forEach.call(document.querySelectorAll(".sbtn"),function(x){x.disabled=b})}
function send(text){
  text=(text||"").trim();if(!text||busy)return;
  if(mode==="llm"&&!cfg.has_key){toggleKeyPanel(true);flash("Cole a chave da OpenAI ou escolha o modo Offline.");return}
  setBusy(true);
  addMsg("user",text);$("#msg").value="";$("#samplebox").open=false;
  var pending=addMsg("bot pending","Consultando…");
  post("/api/chat",{session:sid,message:text,mode:mode,model:$("#model").value.trim(),data:$("#data").value}).then(function(res){
    pending.remove();
    var d=res.data;
    if(res.status!==200){addMsg("err",(d&&d.error)||("Erro "+res.status));return}
    turns+=1;
    if(d.error)addMsg("err",d.error);else addMsg("bot",d.reply);
    renderTools(turns,text,d);
  }).catch(function(e){pending.remove();addMsg("err","Não consegui falar com o programa local: "+e.message)}).then(function(){setBusy(false);$("#msg").focus()});
}
function doExport(){
  api("/api/export?session="+encodeURIComponent(sid)).then(function(res){
    if(res.status!==200){flash("Nada para exportar ainda.");return}
    var cd=res.headers.get("content-disposition")||"";var m=/filename="([^"]+)"/.exec(cd);
    var blob=new Blob([res.data],{type:"text/markdown;charset=utf-8"});var a=document.createElement("a");
    a.href=URL.createObjectURL(blob);a.download=m?m[1]:"conversa.md";document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(a.href)},1000);flash("Conversa exportada.");
  });
}
function reset(note){var old=sid;restart(note);post("/api/reset",{session:old})}
function loadConfig(){return api("/api/config").then(function(res){cfg=res.data;return cfg})}
function renderSamples(){
  var box=$("#samples");box.textContent="";
  cfg.samples.forEach(function(s){
    var b=el("button","sbtn");b.type="button";b.appendChild(el("span",null,s.q));b.appendChild(el("small",null,s.tests));
    b.addEventListener("click",function(){send(s.q)});box.appendChild(b);
  });
}
function saveKey(value){
  return post("/api/key",{key:value}).then(function(res){
    if(res.status!==200){flash((res.data&&res.data.error)||"Não foi possível salvar a chave.");return false}
    return loadConfig().then(function(){renderKey();return true});
  });
}

loadConfig().then(function(){
  var sel=$("#data");cfg.sources.forEach(function(s){var o=document.createElement("option");o.value=s.key;o.textContent=s.label+(s.private?" (privado)":"");sel.appendChild(o)});
  sel.value=cfg.default_source;
  $("#model").value=cfg.default_model;
  var ep=$("#endpoint");ep.textContent=cfg.endpoint_host;ep.className="chip "+(cfg.endpoint_is_openai?"ok":"warn");
  renderKey();renderSamples();
  mode=cfg.has_key?"llm":"offline";
  restart();setMode(mode);
  if(!cfg.has_key)toggleKeyPanel(true);
}).catch(function(e){document.body.insertBefore(el("p","banner bad","Não consegui carregar a configuração: "+e.message),document.body.firstChild)});

$("#mode-llm").addEventListener("click",function(){if(mode!=="llm"){setMode("llm");reset("Modo alterado para Modelo real. Nova conversa.")}});
$("#mode-offline").addEventListener("click",function(){if(mode!=="offline"){setMode("offline");reset("Modo alterado para Offline. Nova conversa.")}});
$("#data").addEventListener("change",function(){renderBanners();reset("Fonte de dados alterada. Nova conversa.")});
$("#reset").addEventListener("click",function(){reset("Nova conversa.")});
$("#export").addEventListener("click",doExport);
$("#keybtn").addEventListener("click",function(){toggleKeyPanel()});
$("#keyform").addEventListener("submit",function(e){
  e.preventDefault();var v=$("#keyinput").value.trim();if(!v){flash("Cole a chave primeiro.");return}
  saveKey(v).then(function(ok){
    if(!ok)return;
    $("#keyinput").value="";toggleKeyPanel(false);setMode("llm");reset("Chave configurada. Modo Modelo real ativo.");flash("Chave configurada.");
  });
});
$("#keyclear").addEventListener("click",function(){
  saveKey("").then(function(ok){if(ok){setMode(cfg.has_key?"llm":"offline");reset("Chave removida.");flash("Chave removida da memória.")}});
});
$("#form").addEventListener("submit",function(e){e.preventDefault();send($("#msg").value)});
$("#msg").addEventListener("keydown",function(e){if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();send($("#msg").value)}});
})();
</script>
</body>
</html>
"""
