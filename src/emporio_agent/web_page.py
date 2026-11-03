"""Single-page UI served by `emporio_agent.web` (no external assets, no build step)."""

PAGE = r"""<!doctype html>
<html lang="pt-BR" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Empório da Música · Atendente virtual</title>
<style>
/* Layout: barra superior única; conversa à esquerda; painel "o que o agente consultou" à direita.
   Visual inspirado no shadcn/ui (zinc): bordas de 1px, raio de 8px, uma cor de destaque, estados só com ponto colorido. */
:root{
  --background:#09090b; --foreground:#fafafa; --card:#0c0c0f; --muted:#18181b; --muted-foreground:#a1a1aa;
  --accent:#27272a; --border:#27272a; --input:#27272a; --ring:#d4d4d8;
  --primary:#fafafa; --primary-foreground:#18181b;
  --ok:#22c55e; --warn:#f59e0b; --bad:#ef4444;
  --radius:8px; --shadow:0 10px 30px rgba(0,0,0,.55);
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,"SF Mono",Menlo,Consolas,monospace;
  color-scheme:dark;
}
:root[data-theme="light"]{
  --background:#ffffff; --foreground:#09090b; --card:#ffffff; --muted:#f4f4f5; --muted-foreground:#71717a;
  --accent:#f4f4f5; --border:#e4e4e7; --input:#e4e4e7; --ring:#18181b;
  --primary:#18181b; --primary-foreground:#fafafa;
  --ok:#16a34a; --warn:#b45309; --bad:#dc2626; --shadow:0 10px 30px rgba(0,0,0,.18);
  color-scheme:light;
}
*{box-sizing:border-box}
html,body{height:100%}
body{margin:0;background:var(--background);color:var(--foreground);font:14px/1.6 var(--sans);display:flex;flex-direction:column;-webkit-font-smoothing:antialiased}
button,input,select,textarea{font:inherit;color:inherit}
a{color:var(--foreground);text-underline-offset:3px}
.ic{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round;flex:none}
.ic.lg{width:20px;height:20px}
[hidden]{display:none!important}

/* ---------- botões ---------- */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:8px;height:36px;padding:0 14px;border-radius:var(--radius);
  border:1px solid transparent;background:transparent;font-size:13px;font-weight:500;cursor:pointer;white-space:nowrap;
  transition:background-color .15s,border-color .15s,opacity .15s}
.btn:disabled{opacity:.5;cursor:default}
.btn.primary{background:var(--primary);color:var(--primary-foreground)}
.btn.primary:hover:not(:disabled){opacity:.9}
.btn.outline{border-color:var(--border)}
.btn.outline:hover:not(:disabled),.btn.ghost:hover:not(:disabled){background:var(--accent)}
.btn.icon{width:36px;padding:0}
.btn.sm{height:30px;padding:0 10px;font-size:12px}
:focus-visible{outline:2px solid var(--ring);outline-offset:2px}

/* ---------- barra superior ---------- */
.topbar{display:flex;align-items:center;gap:8px;padding:12px 20px;border-bottom:1px solid var(--border);flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:10px;margin-right:auto;min-width:0}
.logo{width:32px;height:32px;border-radius:var(--radius);background:var(--primary);color:var(--primary-foreground);display:grid;place-items:center}
.brand b{font-size:14px;font-weight:600;display:block;line-height:1.25}
.brand span{font-size:12px;font-weight:400;color:var(--muted-foreground);display:block;line-height:1.25}
.seg{display:inline-flex;padding:3px;border-radius:var(--radius);background:var(--muted);border:1px solid var(--border)}
.seg button{border:0;background:transparent;color:var(--muted-foreground);height:28px;padding:0 12px;border-radius:6px;font-size:13px;font-weight:500;cursor:pointer}
.seg button[aria-pressed=true]{background:var(--background);color:var(--foreground);box-shadow:0 0 0 1px var(--border)}
.dot{width:8px;height:8px;border-radius:50%;background:var(--muted-foreground);flex:none}
.dot.ok{background:var(--ok)} .dot.warn{background:var(--warn)} .dot.bad{background:var(--bad)}
.alerts{display:flex;flex-direction:column;gap:6px;padding:8px 16px 0}
.alerts:empty{display:none}
.alert{display:flex;gap:8px;align-items:flex-start;padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--muted);font-size:13px;color:var(--muted-foreground)}
.alert .ic{margin-top:2px}
.alert.warn{border-color:color-mix(in srgb,var(--warn) 45%,var(--border));color:var(--foreground)} .alert.warn .ic{color:var(--warn)}
.alert.bad{border-color:color-mix(in srgb,var(--bad) 45%,var(--border));color:var(--foreground)} .alert.bad .ic{color:var(--bad)}

/* ---------- layout ---------- */
main{flex:1;min-height:0;display:grid;grid-template-columns:minmax(0,1fr) 9px var(--aside-w,520px)}
.col{display:flex;flex-direction:column;min-height:0;min-width:0}
.split{position:relative;cursor:col-resize;touch-action:none;outline:none}
.split::before{content:"";position:absolute;left:4px;top:0;bottom:0;width:1px;background:var(--border);transition:background-color .15s,width .15s,left .15s}
.split:hover::before,.split.drag::before,.split:focus-visible::before{background:var(--ring);width:3px;left:3px}
body.dragging{cursor:col-resize;user-select:none}
.side{container-type:inline-size}
.scroll{flex:1;min-height:0;overflow-y:auto}

/* ---------- conversa ---------- */
/* tipografia: 15px no chat, 13px nos detalhes, 12px em rótulos; pesos 400 (texto), 500 (rótulos e ações), 600 (títulos e valores) */
.log{padding:28px 20px 12px;display:flex;flex-direction:column;gap:28px;max-width:740px;width:100%;margin:0 auto}
.empty{margin:auto;max-width:640px;width:100%;padding:24px 16px;text-align:center}
.empty .logo{width:44px;height:44px;margin:0 auto 14px}
.empty h1{margin:0;font-size:22px;font-weight:600;letter-spacing:-.01em}
.empty p{margin:6px 0 0;color:var(--muted-foreground)}
.empty .hint{display:inline-flex;gap:6px;align-items:center;margin-top:14px;font-size:13px}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;margin-top:24px;text-align:left}
.card-btn{display:flex;gap:12px;align-items:flex-start;padding:12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card);cursor:pointer;text-align:left;
  transition:background-color .15s,border-color .15s}
.card-btn:hover:not(:disabled){background:var(--accent);border-color:var(--ring)}
.card-btn:disabled{opacity:.5;cursor:default}
.card-btn .tile{width:32px;height:32px;border-radius:6px;background:var(--muted);border:1px solid var(--border);display:grid;place-items:center;flex:none}
.card-btn b{display:block;font-size:13.5px;font-weight:600}
.card-btn .w{display:block;font-size:12px;color:var(--muted-foreground);margin-top:1px}
.card-btn .q{display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:12px;color:var(--foreground);opacity:.8;margin-top:6px;line-height:1.4}
.row{display:flex;gap:12px;align-items:flex-start}
.row.user{justify-content:flex-end}
.avatar{width:30px;height:30px;border-radius:50%;background:var(--muted);border:1px solid var(--border);display:grid;place-items:center;flex:none;margin-top:2px}
/* bubble */
.bubble{max-width:min(640px,100%);overflow-wrap:anywhere;font-size:15px;line-height:1.65}
/* user */
.row.user .bubble{background:var(--muted);border:1px solid var(--border);padding:9px 14px;border-radius:14px 14px 4px 14px;white-space:pre-wrap;font-size:14.5px}
/* bot */
.row.bot .bubble{padding:2px 0}
.bubble p{margin:0 0 10px} .bubble p:last-child{margin-bottom:0}
.bubble ul{margin:2px 0 12px;padding-left:20px} .bubble li{margin:5px 0}
.bubble strong{font-weight:600}
.srcs{display:flex;flex-wrap:wrap;gap:6px;margin-top:12px}
.badge{display:inline-flex;align-items:center;gap:5px;height:24px;padding:0 10px;border:1px solid var(--border);border-radius:999px;font-size:11.5px;font-weight:500;color:var(--muted-foreground);background:transparent}
button.badge{cursor:pointer;font-family:inherit}
button.badge:hover{background:var(--accent);color:var(--foreground)}
.srcs .lab{font-size:11.5px;color:var(--muted-foreground);align-self:center;margin-right:2px}
.badge .ic{width:12px;height:12px}
.typing{display:inline-flex;gap:4px;padding:8px 0}
.typing i{width:6px;height:6px;border-radius:50%;background:var(--muted-foreground);animation:blink 1.2s infinite ease-in-out}
.typing i:nth-child(2){animation-delay:.15s} .typing i:nth-child(3){animation-delay:.3s}
@keyframes blink{0%,80%,100%{opacity:.25}40%{opacity:1}}
.errrow{display:flex;gap:10px;align-items:flex-start;padding:10px 12px;border:1px solid color-mix(in srgb,var(--bad) 45%,var(--border));border-radius:var(--radius);background:var(--card);max-width:620px}
.errrow .ic{color:var(--bad);margin-top:2px}
.errrow .actions{display:flex;gap:8px;margin-top:8px}
.dock{padding:8px 20px 14px}
.dock-in{max-width:760px;margin:0 auto}
.composer{position:relative;border:1px solid var(--input);border-radius:var(--radius);background:transparent}
.composer:focus-within{border-color:var(--ring);box-shadow:0 0 0 1px var(--ring)}
.composer textarea{display:block;width:100%;resize:none;height:52px;max-height:160px;padding:12px 14px 4px;border:0;background:transparent;line-height:1.45;outline:none}
.tools{display:flex;align-items:center;gap:8px;padding:6px 8px 8px}
.tools .sp{flex:1}
.tools .btn.icon{width:32px;height:32px}
.menu{position:absolute;left:0;bottom:calc(100% + 8px);width:min(580px,100%);max-height:min(440px,52vh);overflow-y:auto;background:var(--background);border:1px solid var(--border);border-radius:10px;box-shadow:var(--shadow);padding:6px;z-index:20}
.menu h4{margin:6px 8px 4px;font-size:11px;font-weight:500;color:var(--muted-foreground);text-transform:uppercase;letter-spacing:.05em}
.mi{display:grid;grid-template-columns:32px 1fr;gap:12px;width:100%;padding:8px;border:0;border-radius:6px;background:transparent;text-align:left;cursor:pointer;align-items:center}
.mi:hover,.mi:focus-visible{background:var(--accent);outline:none}
.mi .tile{width:32px;height:32px;border-radius:6px;background:var(--muted);border:1px solid var(--border);display:grid;place-items:center}
.mi b{display:block;font-size:13px;font-weight:500}
.mi .q{display:block;font-size:13px;color:var(--foreground);overflow-wrap:anywhere}
.mi .w{display:block;font-size:12px;color:var(--muted-foreground)}
.foot{margin-top:8px;font-size:11px;color:var(--muted-foreground);text-align:center}

/* ---------- painel lateral ---------- */
.panel-h{padding:18px 18px 12px}
.panel-h h2{margin:0;font-size:13px;font-weight:600;letter-spacing:.01em}
.kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;padding:0 18px 16px}
.kpi{border:1px solid var(--border);border-radius:10px;background:var(--card);padding:11px 14px;min-width:0}
.kpi .l{display:flex;align-items:center;gap:6px;color:var(--muted-foreground);font-size:12px;font-weight:400;white-space:nowrap}
.kpi .l span{overflow:hidden;text-overflow:ellipsis}
.kpi .v{font-size:20px;font-weight:600;letter-spacing:-.015em;line-height:1.3;margin-top:4px;font-variant-numeric:tabular-nums;white-space:nowrap}
@container (max-width:470px){.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
.turns{padding:0 18px 24px;display:flex;flex-direction:column;gap:10px}
.none{padding:22px 4px;color:var(--muted-foreground);font-size:13px;text-align:center}
.turn{border:1px solid var(--border);border-radius:10px;background:var(--card)}
.t-head{display:flex;align-items:center;gap:12px;width:100%;padding:12px 14px;border:0;background:transparent;text-align:left;cursor:pointer;border-radius:10px;min-height:46px}
.t-head:hover{background:var(--accent)}
.t-head .n{font-family:var(--mono);font-size:11px;color:var(--muted-foreground);flex:none}
.t-head .q{flex:1;min-width:0;font-size:13px;font-weight:400;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.t-head .chev{transition:transform .15s;color:var(--muted-foreground);flex:none}
.turn.open .t-head .chev{transform:rotate(180deg)}
.turn.open .t-head{border-bottom-left-radius:0;border-bottom-right-radius:0}
.t-body{border-top:1px solid var(--border);padding:4px 14px 12px}
.turn:not(.open) .t-body{display:none}
.step{display:grid;grid-template-columns:116px minmax(0,1fr) auto;gap:4px 14px;align-items:center;padding:12px 0;border-bottom:1px solid var(--border)}
.step:last-of-type{border-bottom:0;padding-bottom:10px}
.s-src{display:flex;align-items:center;gap:8px;font-size:13px;font-weight:500;white-space:nowrap}
.s-src .ic{color:var(--muted-foreground)}
.s-txt{font-size:13px;color:var(--muted-foreground);overflow-wrap:anywhere}
.t-meta{display:flex;align-items:center;gap:6px;padding-top:10px;font-size:12px;color:var(--muted-foreground);flex-wrap:wrap}
.t-meta .ic{width:13px;height:13px}
.step .btn.ghost{color:var(--muted-foreground);font-weight:400}
.step .btn.ghost:hover:not(:disabled){color:var(--foreground)}
@container (max-width:470px){.step{grid-template-columns:minmax(0,1fr) auto}.s-txt{grid-column:1 / -1;grid-row:2}}

/* ---------- progresso e cartões de resposta ---------- */
.pline{display:flex;align-items:center;gap:10px;padding:4px 0;color:var(--muted-foreground);font-size:13px}
.pline[hidden]{display:none}
.streamtxt{white-space:pre-wrap;overflow-wrap:anywhere}
.dot.live{background:var(--warn);animation:blink 1.1s infinite ease-in-out}

/* ---------- modais ---------- */
dialog{border:1px solid var(--border);border-radius:12px;background:var(--background);color:var(--foreground);padding:0;width:min(440px,calc(100vw - 32px));box-shadow:var(--shadow)}
dialog::backdrop{background:rgba(0,0,0,.6)}
dialog.drawer{position:fixed;inset:0 0 0 auto;margin:0;height:100dvh;max-height:none;width:min(580px,100vw);border-radius:0;border-width:0 0 0 1px}
.drawer .dlg-b{overflow-y:auto;max-height:calc(100dvh - 76px);padding-bottom:20px}
.drawer .quote{border:1px solid var(--border);border-radius:var(--radius);background:var(--card);padding:12px 14px;font-size:13px;line-height:1.6;white-space:pre-wrap;overflow-wrap:anywhere}
.drawer .quote b{display:block;font-size:12px;font-weight:500;color:var(--muted-foreground);margin-bottom:6px}
.drawer .st-line{display:flex;align-items:center;gap:8px;font-size:13px}
.drawer .lab{font-size:12px;font-weight:500;margin:4px 0 2px}
.drawer pre{margin:0;padding:10px 12px;border-radius:6px;background:var(--muted);border:1px solid var(--border);overflow:auto;font:12px/1.5 var(--mono);white-space:pre-wrap;overflow-wrap:anywhere}
.dlg-h{display:flex;align-items:flex-start;justify-content:space-between;gap:12px;padding:18px 20px 0}
.dlg-h h3{margin:0;font-size:16px;font-weight:600}
.dlg-b{padding:12px 20px 4px;display:flex;flex-direction:column;gap:12px}
.dlg-b p{margin:0;color:var(--muted-foreground)}
.dlg-f{display:flex;justify-content:flex-end;gap:8px;padding:16px 20px 20px}
.status{display:flex;align-items:center;gap:8px;padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--muted);font-size:13px}
.field{display:flex;flex-direction:column;gap:6px}
.field label{font-size:12px;font-weight:500}
.input{height:36px;width:100%;padding:0 12px;border:1px solid var(--input);border-radius:var(--radius);background:transparent;min-width:0}
.input:focus-visible{outline:none;border-color:var(--ring);box-shadow:0 0 0 1px var(--ring)}
select.input{padding-right:8px}
.inline{position:relative}
.inline .input{padding-right:44px}
.inline .btn{position:absolute;right:2px;top:2px;width:32px;height:32px}
.hint-s{font-size:12px;color:var(--muted-foreground)}
#toast{position:fixed;left:50%;bottom:18px;transform:translateX(-50%);background:var(--primary);color:var(--primary-foreground);padding:8px 14px;border-radius:var(--radius);font-size:13px;max-width:90vw;z-index:50}

@media (max-width:900px){
  html,body{height:auto} body{display:block}
  main{display:block} .split{display:none} .col.chat{border-bottom:1px solid var(--border)}
  .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}
  .scroll{overflow:visible} .col{min-height:0}
  .brand span{display:none}
}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
</style>
</head>
<body>
<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
<defs>
<symbol id="i-music" viewBox="0 0 24 24"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></symbol>
<symbol id="i-tag" viewBox="0 0 24 24"><path d="M12.586 2.586A2 2 0 0 0 11.172 2H4a2 2 0 0 0-2 2v7.172a2 2 0 0 0 .586 1.414l8.704 8.704a2.426 2.426 0 0 0 3.42 0l6.58-6.58a2.426 2.426 0 0 0 0-3.42z"/><circle cx="7.5" cy="7.5" r=".5"/></symbol>
<symbol id="i-wallet" viewBox="0 0 24 24"><path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/></symbol>
<symbol id="i-percent" viewBox="0 0 24 24"><line x1="19" y1="5" x2="5" y2="19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/></symbol>
<symbol id="i-package" viewBox="0 0 24 24"><path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><path d="m3.3 7 7.703 4.734a2 2 0 0 0 1.994 0L20.7 7"/><path d="m7.5 4.27 9 5.15"/></symbol>
<symbol id="i-shield-alert" viewBox="0 0 24 24"><path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="M12 8v4"/><path d="M12 16h.01"/></symbol>
<symbol id="i-undo-2" viewBox="0 0 24 24"><path d="M9 14 4 9l5-5"/><path d="M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5a5.5 5.5 0 0 1-5.5 5.5H11"/></symbol>
<symbol id="i-store" viewBox="0 0 24 24"><path d="m2 7 4.41-4.41A2 2 0 0 1 7.83 2h8.34a2 2 0 0 1 1.42.59L22 7"/><path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/><path d="M15 22v-4a2 2 0 0 0-2-2h-2a2 2 0 0 0-2 2v4"/><path d="M2 7h20"/></symbol>
<symbol id="i-circle-help" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/></symbol>
<symbol id="i-lock" viewBox="0 0 24 24"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></symbol>
<symbol id="i-key" viewBox="0 0 24 24"><circle cx="7.5" cy="15.5" r="4.5"/><path d="m10.7 12.3 9.8-9.8"/><path d="m16 7 3 3"/><path d="m14 9 2 2"/></symbol>
<symbol id="i-sliders" viewBox="0 0 24 24"><line x1="21" y1="4" x2="14" y2="4"/><line x1="10" y1="4" x2="3" y2="4"/><line x1="21" y1="12" x2="12" y2="12"/><line x1="8" y1="12" x2="3" y2="12"/><line x1="21" y1="20" x2="16" y2="20"/><line x1="12" y1="20" x2="3" y2="20"/><line x1="14" y1="2" x2="14" y2="6"/><line x1="8" y1="10" x2="8" y2="14"/><line x1="16" y1="18" x2="16" y2="22"/></symbol>
<symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/></symbol>
<symbol id="i-moon" viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/></symbol>
<symbol id="i-download" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></symbol>
<symbol id="i-plus" viewBox="0 0 24 24"><path d="M5 12h14"/><path d="M12 5v14"/></symbol>
<symbol id="i-send" viewBox="0 0 24 24"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></symbol>
<symbol id="i-chevron" viewBox="0 0 24 24"><path d="m6 9 6 6 6-6"/></symbol>
<symbol id="i-x" viewBox="0 0 24 24"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></symbol>
<symbol id="i-eye" viewBox="0 0 24 24"><path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/></symbol>
<symbol id="i-eye-off" viewBox="0 0 24 24"><path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/></symbol>
<symbol id="i-bot" viewBox="0 0 24 24"><path d="M12 8V4H8"/><rect x="4" y="8" width="16" height="12" rx="2"/><path d="M2 14h2"/><path d="M20 14h2"/><path d="M15 13v2"/><path d="M9 13v2"/></symbol>
<symbol id="i-alert" viewBox="0 0 24 24"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/></symbol>
<symbol id="i-database" viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5V19A9 3 0 0 0 21 19V5"/><path d="M3 12A9 3 0 0 0 21 12"/></symbol>
<symbol id="i-book" viewBox="0 0 24 24"><path d="M12 7v14"/><path d="M3 18a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1h5a4 4 0 0 1 4 4 4 4 0 0 1 4-4h5a1 1 0 0 1 1 1v13a1 1 0 0 1-1 1h-6a3 3 0 0 0-3 3 3 3 0 0 0-3-3z"/></symbol>
<symbol id="i-message" viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></symbol>
<symbol id="i-search" viewBox="0 0 24 24"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></symbol>
<symbol id="i-layers" viewBox="0 0 24 24"><path d="M12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83z"/><path d="M2 12a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 12"/><path d="M2 17a1 1 0 0 0 .58.91l8.6 3.91a2 2 0 0 0 1.65 0l8.58-3.9A1 1 0 0 0 22 17"/></symbol>
<symbol id="i-timer" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></symbol>
<symbol id="i-sparkles" viewBox="0 0 24 24"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/><path d="M4 17v2"/><path d="M5 18H3"/></symbol>
<symbol id="i-external" viewBox="0 0 24 24"><path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/></symbol>
</defs>
</svg>

<header class="topbar">
  <div class="brand">
    <div class="logo"><svg class="ic lg"><use href="#i-music"/></svg></div>
    <div><b>Empório da Música</b><span>Atendente virtual · protótipo</span></div>
  </div>
  <div class="seg" role="group" aria-label="Modo de resposta">
    <button type="button" id="mode-llm" aria-pressed="false" title="O modelo de linguagem decide o que consultar">Modelo real</button>
    <button type="button" id="mode-offline" aria-pressed="true" title="Respostas por regras simples, sem chave e sem custo">Offline</button>
  </div>
  <button type="button" class="btn outline" id="keybtn" aria-haspopup="dialog"><span class="dot" id="keydot"></span><span id="keylabel">Chave</span></button>
  <button type="button" class="btn ghost icon" id="reset" aria-label="Nova conversa" title="Nova conversa"><svg class="ic"><use href="#i-plus"/></svg></button>
  <button type="button" class="btn ghost icon" id="export" aria-label="Exportar conversa em Markdown" title="Exportar conversa (.md)"><svg class="ic"><use href="#i-download"/></svg></button>
  <button type="button" class="btn ghost icon" id="settingsbtn" aria-label="Ajustes" title="Ajustes: dados, modelo e endpoint" aria-haspopup="dialog"><svg class="ic"><use href="#i-sliders"/></svg></button>
  <button type="button" class="btn ghost icon" id="themebtn" aria-label="Alternar tema" title="Alternar tema"><svg class="ic" id="themeic"><use href="#i-sun"/></svg></button>
</header>
<div class="alerts" id="alerts" aria-live="polite"></div>

<main id="main">
  <section class="col chat" aria-label="Conversa">
    <div class="scroll" id="scroll"><div class="log" id="log" aria-live="polite"></div></div>
    <div class="dock">
      <div class="dock-in">
        <form class="composer" id="form">
          <textarea id="msg" placeholder="Escreva uma mensagem como cliente" maxlength="2000" aria-label="Mensagem" rows="2"></textarea>
          <div class="tools">
            <button type="button" class="btn outline sm" id="sugbtn" aria-haspopup="menu" aria-expanded="false" aria-controls="suggest-menu"><svg class="ic"><use href="#i-sparkles"/></svg>Sugestões<svg class="ic"><use href="#i-chevron"/></svg></button>
            <span class="sp"></span>
            <button class="btn primary icon" id="send" type="submit" aria-label="Enviar" title="Enviar (Enter)"><svg class="ic"><use href="#i-send"/></svg></button>
          </div>
          <div class="menu" id="suggest-menu" role="menu" aria-label="Perguntas sugeridas" hidden></div>
        </form>
        <div class="foot" id="foot"></div>
      </div>
    </div>
  </section>
  <div class="split" id="splitter" role="separator" aria-orientation="vertical" aria-label="Redimensionar o painel de consultas (setas esquerda e direita; duplo clique restaura)" tabindex="0"></div>
  <aside class="col side" aria-label="O que o agente consultou">
    <div class="scroll">
      <div class="panel-h"><h2>O que o agente consultou</h2></div>
      <div class="kpis" id="kpis"></div>
      <div class="turns" id="turns"></div>
    </div>
  </aside>
</main>

<dialog id="key-dialog" aria-labelledby="key-title">
  <div class="dlg-h"><h3 id="key-title">Chave da OpenAI</h3>
    <button type="button" class="btn ghost icon sm" data-close aria-label="Fechar"><svg class="ic"><use href="#i-x"/></svg></button></div>
  <form id="keyform" autocomplete="off">
    <div class="dlg-b">
      <div class="status"><span class="dot" id="kdot"></span><span id="kstate"></span></div>
      <p>Necessária só para o modo <b>Modelo real</b>. A chave fica na memória deste programa e não é gravada em arquivo nem exportada.</p>
      <div class="field">
        <label for="keyinput">Cole a chave</label>
        <div class="inline">
          <input class="input" type="password" id="keyinput" placeholder="sk-..." autocomplete="off" spellcheck="false">
          <button type="button" class="btn ghost icon" id="keyeye" aria-label="Mostrar chave" title="Mostrar ou ocultar"><svg class="ic" id="eyeic"><use href="#i-eye"/></svg></button>
        </div>
        <a class="hint-s" href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer">Criar uma chave na OpenAI</a>
      </div>
    </div>
    <div class="dlg-f">
      <button type="button" class="btn outline" id="keyclear" hidden>Remover</button>
      <button type="button" class="btn outline" data-close>Cancelar</button>
      <button type="submit" class="btn primary" id="keysave">Salvar</button>
    </div>
  </form>
</dialog>

<dialog id="settings-dialog" aria-labelledby="set-title">
  <div class="dlg-h"><h3 id="set-title">Ajustes</h3>
    <button type="button" class="btn ghost icon sm" data-close aria-label="Fechar"><svg class="ic"><use href="#i-x"/></svg></button></div>
  <div class="dlg-b">
    <div class="field"><label for="data">Dados</label><select class="input" id="data"></select></div>
    <div class="field"><label for="model">Modelo (modo real)</label>
      <input class="input" type="text" id="model" list="models" autocomplete="off" spellcheck="false">
      <datalist id="models"><option value="gpt-4.1-mini"><option value="gpt-4.1"><option value="gpt-4o-mini"></datalist></div>
    <div class="status"><span class="dot" id="epdot"></span><span id="eptext"></span></div>
  </div>
  <div class="dlg-f"><button type="button" class="btn primary" data-close>Concluir</button></div>
</dialog>
<dialog id="drawer" class="drawer" aria-labelledby="drawer-title">
  <div class="dlg-h"><h3 id="drawer-title">Dados da consulta</h3>
    <button type="button" class="btn ghost icon sm" data-close aria-label="Fechar"><svg class="ic"><use href="#i-x"/></svg></button></div>
  <div class="dlg-b" id="drawer-body"></div>
</dialog>
<div id="toast" role="status" hidden></div>

<script>
(function(){
"use strict";
/*PURE-START*/
var SOURCES={
  search_products:{name:"Catálogo",icon:"database"},
  search_promotions:{name:"Promoções",icon:"percent"},
  order_status:{name:"Pedidos",icon:"package"},
  search_policies:{name:"Manual",icon:"book"}
};
var OK_STATES=["ok","verified"], WARN_STATES=["not_verified","verification_required","no_evidence","locked"];
function fmtInt(n){return Number(n||0).toLocaleString("pt-BR")}
function fmtTokens(n){return n>=10000?(n/1000).toFixed(1).replace(".",",")+" mil":fmtInt(n)}
function fmtSecs(s){return s<0.1?"< 0,1 s":(s<10?s.toFixed(1).replace(".",",")+" s":Math.round(s)+" s")}
function newStats(){return {turns:0,calls:0,by:{},tin:0,tout:0,secs:[]}}
function statusOf(c){var s=c&&c.output&&c.output.status;return OK_STATES.indexOf(s)>=0?"ok":(WARN_STATES.indexOf(s)>=0?"warn":"bad")}
function turnStatus(r){
  if(r.error)return "bad";
  var t=r.tools||[];if(!t.length)return "none";
  var worst="ok";
  t.forEach(function(c){var s=statusOf(c);if(s==="bad")worst="bad";else if(s==="warn"&&worst!=="bad")worst="warn"});
  return worst;
}
function addTurn(st,r){
  st.turns+=1;
  (r.tools||[]).forEach(function(c){st.calls+=1;st.by[c.tool]=(st.by[c.tool]||0)+1});
  var u=r.usage||{};st.tin+=u.tokens_in||0;st.tout+=u.tokens_out||0;
  if(typeof r.seconds==="number")st.secs.push(r.seconds);
  return st;
}
function kpiValues(st,mode){
  var parts=[];
  Object.keys(SOURCES).forEach(function(k){if(st.by[k])parts.push(SOURCES[k].name+" "+st.by[k])});
  var avg=st.secs.length?st.secs.reduce(function(a,b){return a+b},0)/st.secs.length:null;
  var llm=mode==="llm";
  return {
    turns:{v:fmtInt(st.turns),tip:"Respostas nesta conversa"},
    calls:{v:fmtInt(st.calls),tip:parts.length?("Consultas às fontes: "+parts.join(", ")):"Nenhuma consulta ainda"},
    tokens:{v:llm?fmtTokens(st.tin+st.tout):"—",tip:llm?("Entrada "+fmtInt(st.tin)+" · saída "+fmtInt(st.tout)):"Tokens só são contados no modo Modelo real"},
    time:{v:avg===null?"—":fmtSecs(avg),tip:"Tempo médio por resposta"}
  };
}
function bold(text){return text.split(/(\*\*[^*\n]+\*\*)/).filter(Boolean).map(function(p){
  return /^\*\*[^*]+\*\*$/.test(p)?{b:true,t:p.slice(2,-2)}:{b:false,t:p}})}
function blocks(text){
  var out=[],cur=null;
  String(text).replace(/\r/g,"").split("\n").forEach(function(line){
    var m=/^\s*(?:[-•*]|\d+[.)])\s+(.*)$/.exec(line);
    if(m){if(!cur||cur.type!=="ul"){cur={type:"ul",items:[]};out.push(cur)}cur.items.push(m[1]);return}
    if(!line.trim()){cur=null;return}
    if(cur&&cur.type==="p"){cur.text+=" "+line.trim();return}
    cur={type:"p",text:line.trim()};out.push(cur);
  });
  return out;
}
function describe(c){
  var o=c.output||{},st=o.status;
  switch(c.tool){
    case "search_products":return st==="ok"?("Encontrou "+o.matches+" produto(s) no catálogo."):"Consultou o catálogo, sem resultado utilizável.";
    case "search_promotions":return st==="ok"?("Listou "+o.matches+" produto(s) em promoção ativa."):"Consultou as promoções, sem resultado.";
    case "order_status":
      if(st==="verified")return "Pedido e e-mail conferem; o status foi liberado.";
      if(st==="not_verified")return "Pedido e e-mail não conferem; nada do pedido foi revelado.";
      if(st==="locked")return "Verificação bloqueada após falhas; encaminhado à equipe.";
      return "Faltavam dados para verificar o pedido.";
    case "search_policies":return st==="ok"?("Trouxe "+((o.results||[]).length)+" trecho(s) do manual, páginas "+(o.results||[]).map(function(r){return r.page}).join(", ")+"."):"Procurou no manual e não achou trecho relevante.";
  }
  return "Executou "+c.tool+".";
}
var ING={search_products:"o catálogo",search_promotions:"as promoções",order_status:"os pedidos",search_policies:"o manual"};
function stageText(ev){
  if(ev.type==="tool_start")return "Consultando "+(ING[ev.tool]||"uma fonte")+"…";
  if(ev.type==="tool")return "Escrevendo a resposta…";
  return "Pensando…";
}
function parseNdjson(buf){
  var parts=String(buf).split("\n"),rest=parts.pop(),events=[];
  parts.forEach(function(l){if(!l.trim())return;try{events.push(JSON.parse(l))}catch(e){}});
  return {events:events,rest:rest};
}
function metaText(r,mode){
  var u=r.usage||{},total=fmtSecs(r.seconds||0);
  if(mode!=="llm")return "Modo offline · "+total;
  var each=u.seconds_each||[],parts=[total+" no total"];
  if(each.length)parts.push("API: "+each.map(fmtSecs).join(" + "));
  parts.push(fmtTokens((u.tokens_in||0)+(u.tokens_out||0))+" tokens");
  return parts.join(" · ");
}
function badgeInfo(tools){
  var seen={},out=[];
  (tools||[]).forEach(function(c){
    var def=SOURCES[c.tool];if(!def||seen[c.tool])return;seen[c.tool]=1;
    var label=def.name;
    if(c.tool==="search_policies"){
      var pages=[];((c.output&&c.output.results)||[]).forEach(function(r){if(pages.indexOf(r.page)<0)pages.push(r.page)});
      if(pages.length)label="Manual · p. "+pages.join(", ");
    }
    out.push({tool:c.tool,label:label,call:c});
  });
  return out;
}
/*PURE-END*/

var $=function(s){return document.querySelector(s)};
var cfg=null,sid=newId(),mode="offline",busy=false,stats=newStats(),lastText="",theme="dark";
var SVGNS="http://www.w3.org/2000/svg";

function newId(){var a=new Uint8Array(16);crypto.getRandomValues(a);return Array.prototype.map.call(a,function(b){return ("0"+b.toString(16)).slice(-2)}).join("")}
function el(tag,cls,text){var e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e}
function ic(name,cls){var s=document.createElementNS(SVGNS,"svg");s.setAttribute("class","ic"+(cls?" "+cls:""));
  var u=document.createElementNS(SVGNS,"use");u.setAttribute("href","#i-"+name);s.appendChild(u);return s}
function toast(text){var t=$("#toast");t.textContent=text;t.hidden=false;clearTimeout(toast.t);toast.t=setTimeout(function(){t.hidden=true},3200)}
function api(path,opts){
  return fetch(path,opts).then(function(r){
    var ct=r.headers.get("content-type")||"";
    return (ct.indexOf("json")>=0?r.json():r.text()).then(function(d){return {status:r.status,data:d,headers:r.headers}});
  });
}
function post(path,body){return api(path,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})}
function selected(){return cfg.sources.filter(function(s){return s.key===$("#data").value})[0]}
function keyKnown(){return !!(cfg&&cfg.has_key)}

/* ---------- tema ---------- */
function applyTheme(t){
  theme=t;document.documentElement.setAttribute("data-theme",t);
  $("#themeic").firstChild.setAttribute("href",t==="dark"?"#i-sun":"#i-moon");
  try{localStorage.setItem("emporio-theme",t)}catch(e){}
}

/* ---------- avisos, chave, rodapé ---------- */
function alertRow(kind,text){var a=el("div","alert "+kind);a.appendChild(ic("alert"));a.appendChild(el("span",null,text));return a}
function renderAlerts(){
  var box=$("#alerts");box.textContent="";
  var src=selected();
  if(mode==="llm"&&src&&src.private)box.appendChild(alertRow("bad","Dados originais em uso: no modo Modelo real, trechos do manual e de pedidos reais são enviados à API."));
}
function renderKeyState(){
  var ok=keyKnown();
  $("#keydot").className="dot "+(ok?"ok":"warn");
  $("#keylabel").textContent=ok?"Chave configurada":"Sem chave";
  $("#kdot").className="dot "+(ok?"ok":"warn");
  var where={ui:"Configurada, colada nesta tela.",env:"Configurada pela variável de ambiente OPENAI_API_KEY."}[cfg.key_source];
  $("#kstate").textContent=where||"Não configurada.";
  $("#keyclear").hidden=cfg.key_source!=="ui";
}
function renderEndpoint(){
  var ok=cfg.endpoint_is_openai;
  $("#epdot").className="dot "+(ok?"ok":"warn");
  $("#eptext").textContent="Endpoint: "+cfg.endpoint_host+(ok?"":" (não é a OpenAI)");
}
function renderFoot(){
  var s=selected();
  var base=s?(s.private?"Dados originais (privados)":"Dados de teste sanitizados · manual de políticas sintético"):"";
  $("#foot").textContent=(mode==="offline"?"Modo offline: respostas por regras, sem modelo de linguagem":"")+(mode==="offline"&&base?" · ":"")+base;
}
function openDialog(id){var d=$(id);if(!d.open)d.showModal()}

/* ---------- KPIs e painel ---------- */
var KPI_DEF=[["turns","Turnos","message"],["calls","Consultas","search"],["tokens","Tokens","layers"],["time","Tempo médio","timer"]];
function renderKpis(){
  var box=$("#kpis");box.textContent="";
  var v=kpiValues(stats,mode);
  KPI_DEF.forEach(function(d){
    var k=el("div","kpi");k.title=v[d[0]].tip;
    var l=el("div","l");l.appendChild(ic(d[2]));l.appendChild(el("span",null,d[1]));k.appendChild(l);
    k.appendChild(el("div","v",v[d[0]].v));box.appendChild(k);
  });
}
function emptyTurns(){var t=$("#turns");t.textContent="";t.appendChild(el("div","none","As consultas de cada resposta aparecem aqui."))}
function setOpen(card,open){
  card.classList.toggle("open",open);
  var h=card.querySelector(".t-head");if(h)h.setAttribute("aria-expanded",String(open));
}
function openDrawer(n,c){
  var def=SOURCES[c.tool]||{name:c.tool,icon:"search"};
  $("#drawer-title").textContent=def.name+" · resposta #"+n;
  var b=$("#drawer-body");b.textContent="";
  var line=el("div","st-line");line.appendChild(el("span","dot "+statusOf(c)));
  line.appendChild(el("span",null,(c.output&&c.output.status)||"?"));b.appendChild(line);
  b.appendChild(el("p",null,describe(c)));
  if(c.tool==="search_policies"&&c.output&&(c.output.results||[]).length){
    b.appendChild(el("div","lab","Trechos do manual"));
    c.output.results.forEach(function(r){var q=el("div","quote");q.appendChild(el("b",null,"Página "+r.page));q.appendChild(document.createTextNode(String(r.excerpt||"").trim()));b.appendChild(q)});
  }
  b.appendChild(el("div","lab","Argumentos enviados à fonte"));b.appendChild(el("pre",null,JSON.stringify(c.args,null,2)));
  b.appendChild(el("div","lab","Resposta bruta da fonte"));b.appendChild(el("pre",null,JSON.stringify(c.output,null,2)));
  openDialog("#drawer");
}
function startTurn(n,question){
  var box=$("#turns");var none=box.querySelector(".none");if(none)none.remove();
  Array.prototype.forEach.call(box.querySelectorAll(".turn"),function(c){setOpen(c,false)});
  var card=el("section","turn");
  var h=el("button","t-head");h.type="button";
  h.appendChild(el("span","n","#"+n));h.appendChild(el("span","q",question));
  var dot=el("span","dot live");h.appendChild(dot);h.appendChild(ic("chevron","chev"));
  h.addEventListener("click",function(){setOpen(card,!card.classList.contains("open"))});
  card.appendChild(h);
  var body=el("div","t-body");card.appendChild(body);box.appendChild(card);setOpen(card,true);
  card.scrollIntoView({block:"nearest"});
  return {n:n,card:card,body:body,dot:dot,pending:[]};
}
function liveStep(T,tool){
  var def=SOURCES[tool]||{name:tool,icon:"search"};
  var row=el("div","step");
  var src=el("span","s-src");var d=el("span","dot live");src.appendChild(d);src.appendChild(ic(def.icon));src.appendChild(el("span",null,def.name));
  var txt=el("span","s-txt","Consultando "+(ING[tool]||"a fonte")+"…");
  row.appendChild(src);row.appendChild(txt);T.body.appendChild(row);
  var p={tool:tool,row:row,dot:d,src:src,txt:txt};T.pending.push(p);return p;
}
function doneStep(T,c){
  var p=null;
  for(var i=0;i<T.pending.length;i++){if(T.pending[i].tool===c.tool){p=T.pending.splice(i,1)[0];break}}
  if(!p)p=liveStep(T,c.tool);
  p.dot.className="dot "+statusOf(c);p.src.title="Status: "+((c.output&&c.output.status)||"?");
  p.txt.textContent=describe(c);
  var btn=el("button","btn ghost sm","Ver dados");btn.type="button";btn.addEventListener("click",function(){openDrawer(T.n,c)});
  p.row.appendChild(btn);
}
function finishTurn(T,r){
  T.pending.forEach(function(p){p.row.remove()});T.pending=[];
  if(!T.body.querySelector(".step")){
    var s=el("div","step");s.appendChild(el("span","s-src",r.error?"Erro":"Sem consulta"));
    s.appendChild(el("span","s-txt",r.error?r.error:"Respondeu sem consultar nenhuma fonte."));T.body.appendChild(s);
  }
  T.dot.className="dot "+({ok:"ok",warn:"warn",bad:"bad",none:""}[turnStatus(r)]||"");
  var meta=el("div","t-meta");meta.appendChild(ic("timer"));meta.appendChild(el("span",null,metaText(r,mode)));T.body.appendChild(meta);
}
function discardTurn(T){if(T&&T.card)T.card.remove();if(!$("#turns .turn")&&!$("#turns .none"))emptyTurns()}
function addTurnCard(n,question,r){
  var T=startTurn(n,question);
  (r.tools||[]).forEach(function(c){liveStep(T,c.tool);doneStep(T,c)});
  finishTurn(T,r);return T;
}

/* ---------- conversa ---------- */
function renderRich(parent,text){
  blocks(text).forEach(function(b){
    if(b.type==="ul"){var ul=el("ul");b.items.forEach(function(it){var li=el("li");inline(li,it);ul.appendChild(li)});parent.appendChild(ul)}
    else{var p=el("p");inline(p,b.text);parent.appendChild(p)}
  });
}
function inline(parent,text){bold(text).forEach(function(p){parent.appendChild(p.b?el("strong",null,p.t):document.createTextNode(p.t))})}
function removeEmpty(){var e=$("#log .empty");if(e)e.remove()}
function scrollDown(){var s=$("#scroll");s.scrollTop=s.scrollHeight}
function addUser(text){removeEmpty();var r=el("div","row user");r.appendChild(el("div","bubble",text));$("#log").appendChild(r);scrollDown()}
function botRow(){var r=el("div","row bot");var a=el("div","avatar");a.appendChild(ic("bot"));r.appendChild(a);var b=el("div","bubble");r.appendChild(b);return {row:r,bubble:b}}
function addTyping(){
  var x=botRow();
  var line=el("div","pline");var dots=el("div","typing");dots.appendChild(el("i"));dots.appendChild(el("i"));dots.appendChild(el("i"));
  var stage=el("span",null,"Pensando…");line.appendChild(dots);line.appendChild(stage);
  var txt=el("div","streamtxt");txt.hidden=true;
  x.bubble.appendChild(line);x.bubble.appendChild(txt);$("#log").appendChild(x.row);scrollDown();
  return {
    stage:function(s){stage.textContent=s},
    append:function(d){line.hidden=true;txt.hidden=false;txt.textContent+=d;scrollDown()},
    clear:function(){txt.textContent="";txt.hidden=true;line.hidden=false},
    remove:function(){x.row.remove()}
  };
}
function addBot(text,tools,n){
  var x=botRow();renderRich(x.bubble,text);
  var badges=badgeInfo(tools);
  if(badges.length){
    var srcs=el("div","srcs");srcs.appendChild(el("span","lab","Fonte"));
    badges.forEach(function(bi){
      var bd=el("button","badge");bd.type="button";bd.title="Ver os dados desta consulta";
      bd.appendChild(ic(SOURCES[bi.tool].icon));bd.appendChild(el("span",null,bi.label));
      bd.addEventListener("click",function(){openDrawer(n,bi.call)});srcs.appendChild(bd);
    });
    x.bubble.appendChild(srcs);
  }
  $("#log").appendChild(x.row);scrollDown();
}
function addError(text){
  var e=el("div","errrow");e.appendChild(ic("alert"));
  var c=el("div");c.appendChild(el("div",null,text));
  var ac=el("div","actions");
  if(/chave/i.test(text)){var k=el("button","btn outline sm","Abrir chave");k.type="button";k.addEventListener("click",function(){openKey()});ac.appendChild(k)}
  if(lastText){var r=el("button","btn outline sm","Tentar de novo");r.type="button";r.addEventListener("click",function(){e.remove();send(lastText,true)});ac.appendChild(r)}
  c.appendChild(ac);e.appendChild(c);$("#log").appendChild(e);scrollDown();
}
function renderEmpty(){
  var log=$("#log");log.textContent="";
  var e=el("div","empty");
  var lg=el("div","logo");lg.appendChild(ic("music","lg"));e.appendChild(lg);
  e.appendChild(el("h1",null,"Como posso ajudar?"));
  e.appendChild(el("p",null,"Pergunte sobre produtos, pedidos ou políticas da loja."));
  var cards=el("div","cards");
  cfg.samples.forEach(function(s){
    var b=el("button","card-btn");b.type="button";b.title=s.q;
    var tile=el("span","tile");tile.appendChild(ic(s.icon));b.appendChild(tile);
    var tx=el("span");tx.appendChild(el("b",null,s.label));tx.appendChild(el("span","w",s.tests));tx.appendChild(el("span","q","\u201c"+s.q+"\u201d"));b.appendChild(tx);
    b.addEventListener("click",function(){send(s.q)});cards.appendChild(b);
  });
  e.appendChild(cards);
  if(!keyKnown()){
    var h=el("div","hint badge");h.appendChild(ic("key"));h.appendChild(el("span",null,"Modo offline: respostas por regras. "));
    var a=el("button","btn ghost sm","Adicionar chave");a.type="button";a.addEventListener("click",function(){openKey()});h.appendChild(a);e.appendChild(h);
  }
  log.appendChild(e);
}
/* ---------- menu de sugestões ---------- */
function renderMenu(){
  var m=$("#suggest-menu");m.textContent="";
  m.appendChild(el("h4",null,"Perguntas sugeridas"));
  cfg.samples.forEach(function(s){
    var b=el("button","mi");b.type="button";b.setAttribute("role","menuitem");
    var tile=el("span","tile");tile.appendChild(ic(s.icon));b.appendChild(tile);
    var tx=el("span");tx.appendChild(el("b",null,s.label));tx.appendChild(el("span","q",s.q));tx.appendChild(el("span","w","Testa: "+s.tests));b.appendChild(tx);
    b.addEventListener("click",function(){toggleMenu(false);send(s.q)});m.appendChild(b);
  });
}
function toggleMenu(show){
  var m=$("#suggest-menu"),b=$("#sugbtn");
  var open=show===undefined?m.hidden:show;
  m.hidden=!open;b.setAttribute("aria-expanded",String(open));
  if(open){var f=m.querySelector(".mi");if(f)f.focus()}
}
function setBusy(v){busy=v;$("#send").disabled=v;$("#sugbtn").disabled=v;Array.prototype.forEach.call(document.querySelectorAll(".card-btn"),function(x){x.disabled=v})}
function chatStream(payload,onEvent){
  return fetch("/api/chat/stream",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)}).then(function(r){
    var ct=r.headers.get("content-type")||"";
    if(ct.indexOf("ndjson")<0||!r.body||!r.body.getReader){
      return (ct.indexOf("json")>=0?r.json():r.text()).then(function(d){return {status:r.status,data:d}});
    }
    var reader=r.body.getReader(),dec=new TextDecoder(),buf="",fin=null;
    function feed(events){events.forEach(function(ev){if(ev.type==="done")fin=ev;else onEvent(ev)})}
    function pump(){
      return reader.read().then(function(x){
        if(x.value)buf+=dec.decode(x.value,{stream:!x.done});
        var p=parseNdjson(buf);buf=p.rest;feed(p.events);
        if(x.done){
          if(buf.trim())feed(parseNdjson(buf+"\n").events);
          return {status:200,data:fin||{reply:null,error:"A resposta foi interrompida antes de terminar.",trace:[],tools:[],usage:{},seconds:0}};
        }
        return pump();
      });
    }
    return pump();
  });
}
function send(text,retry){
  text=(text||"").trim();if(!text||busy)return;
  if(mode==="llm"&&!keyKnown()){openKey();return}
  toggleMenu(false);lastText=text;setBusy(true);
  if(!retry)addUser(text);
  $("#msg").value="";
  var typing=addTyping(),turn=null;
  function ensure(){if(!turn)turn=startTurn(stats.turns+1,text);return turn}
  function onEvent(ev){
    if(ev.type==="status"){ensure();typing.stage(stageText(ev))}
    else if(ev.type==="tool_start"){liveStep(ensure(),ev.tool);typing.clear();typing.stage(stageText(ev))}
    else if(ev.type==="tool"){doneStep(ensure(),ev);typing.clear();typing.stage(stageText(ev))}
    else if(ev.type==="delta"){typing.append(ev.text)}
  }
  chatStream({session:sid,message:text,mode:mode,model:$("#model").value.trim(),data:$("#data").value},onEvent).then(function(res){
    typing.remove();var d=res.data;
    if(res.status!==200){discardTurn(turn);addError((d&&d.error)||("Erro "+res.status));return}
    if(d.error)addError(d.error);else addBot(d.reply,d.tools,stats.turns+1);
    if(!turn){turn=startTurn(stats.turns+1,text);(d.tools||[]).forEach(function(c){liveStep(turn,c.tool);doneStep(turn,c)})}
    finishTurn(turn,d);addTurn(stats,d);renderKpis();
  }).catch(function(e){typing.remove();discardTurn(turn);addError("Não consegui falar com o programa local: "+e.message)})
    .then(function(){setBusy(false);$("#msg").focus()});
}
function newChat(announce){
  var old=sid;sid=newId();stats=newStats();lastText="";
  renderEmpty();renderKpis();emptyTurns();
  post("/api/reset",{session:old});
  if(announce)toast(announce);
}
function setMode(m,silent){
  if(m==="llm"&&!keyKnown()){openKey();return}
  mode=m;
  $("#mode-llm").setAttribute("aria-pressed",String(m==="llm"));
  $("#mode-offline").setAttribute("aria-pressed",String(m==="offline"));
  renderAlerts();renderFoot();
  if(!silent)newChat(m==="llm"?"Modo Modelo real":"Modo Offline");
}
function doExport(){
  api("/api/export?session="+encodeURIComponent(sid)).then(function(res){
    if(res.status!==200){toast("Nada para exportar ainda.");return}
    var cd=res.headers.get("content-disposition")||"";var m=/filename="([^"]+)"/.exec(cd);
    var blob=new Blob([res.data],{type:"text/markdown;charset=utf-8"});var a=document.createElement("a");
    a.href=URL.createObjectURL(blob);a.download=m?m[1]:"conversa.md";document.body.appendChild(a);a.click();a.remove();
    setTimeout(function(){URL.revokeObjectURL(a.href)},1000);toast("Conversa exportada.");
  });
}

/* ---------- chave ---------- */
function openKey(){renderKeyState();$("#keyinput").value="";$("#keyinput").type="password";$("#eyeic").firstChild.setAttribute("href","#i-eye");openDialog("#key-dialog");setTimeout(function(){$("#keyinput").focus()},30)}
function loadConfig(){return api("/api/config").then(function(r){cfg=r.data;return cfg})}
function saveKey(value){
  return post("/api/key",{key:value}).then(function(res){
    if(res.status!==200){toast((res.data&&res.data.error)||"Não foi possível salvar a chave.");return false}
    return loadConfig().then(function(){renderKeyState();return true});
  });
}

/* ---------- inicialização ---------- */
try{var saved=localStorage.getItem("emporio-theme");if(saved==="light"||saved==="dark")theme=saved}catch(e){}
applyTheme(theme);
loadConfig().then(function(){
  var sel=$("#data");cfg.sources.forEach(function(s){var o=document.createElement("option");o.value=s.key;o.textContent=s.label+(s.private?" (privado)":"");sel.appendChild(o)});
  sel.value=cfg.default_source;$("#model").value=cfg.default_model;
  renderKeyState();renderEndpoint();renderFoot();renderMenu();
  mode=keyKnown()?"llm":"offline";
  $("#mode-llm").setAttribute("aria-pressed",String(mode==="llm"));
  $("#mode-offline").setAttribute("aria-pressed",String(mode==="offline"));
  renderAlerts();renderFoot();renderEmpty();renderKpis();emptyTurns();
}).catch(function(e){$("#log").appendChild(addErrorFallback(e))});
function addErrorFallback(e){var d=el("div","alert bad");d.appendChild(ic("alert"));d.appendChild(el("span",null,"Não consegui carregar a configuração: "+e.message));return d}

$("#mode-llm").addEventListener("click",function(){if(mode!=="llm")setMode("llm")});
$("#mode-offline").addEventListener("click",function(){if(mode!=="offline")setMode("offline")});
$("#keybtn").addEventListener("click",openKey);
$("#settingsbtn").addEventListener("click",function(){renderEndpoint();openDialog("#settings-dialog")});
$("#themebtn").addEventListener("click",function(){applyTheme(theme==="dark"?"light":"dark")});
$("#reset").addEventListener("click",function(){newChat("Nova conversa")});
$("#export").addEventListener("click",doExport);
$("#data").addEventListener("change",function(){renderAlerts();renderFoot();newChat("Dados alterados")});
Array.prototype.forEach.call(document.querySelectorAll("dialog"),function(d){
  d.addEventListener("click",function(e){if(e.target===d)d.close()});
  Array.prototype.forEach.call(d.querySelectorAll("[data-close]"),function(b){b.addEventListener("click",function(){d.close()})});
});
$("#keyeye").addEventListener("click",function(){
  var i=$("#keyinput"),show=i.type==="password";i.type=show?"text":"password";
  $("#eyeic").firstChild.setAttribute("href",show?"#i-eye-off":"#i-eye");
});
$("#keyform").addEventListener("submit",function(e){
  e.preventDefault();var v=$("#keyinput").value.trim();if(!v){toast("Cole a chave primeiro.");return}
  saveKey(v).then(function(ok){if(!ok)return;$("#key-dialog").close();mode="llm";setMode("llm",true);$("#mode-llm").setAttribute("aria-pressed","true");$("#mode-offline").setAttribute("aria-pressed","false");renderAlerts();newChat("Chave configurada · Modelo real ativo")});
});
$("#keyclear").addEventListener("click",function(){
  saveKey("").then(function(ok){if(!ok)return;$("#key-dialog").close();mode="offline";$("#mode-llm").setAttribute("aria-pressed","false");$("#mode-offline").setAttribute("aria-pressed","true");renderAlerts();newChat("Chave removida · Modo Offline")});
});
$("#form").addEventListener("submit",function(e){e.preventDefault();send($("#msg").value)});
$("#sugbtn").addEventListener("click",function(e){e.stopPropagation();toggleMenu()});
document.addEventListener("click",function(e){var m=$("#suggest-menu");if(!m.hidden&&!$("#form").contains(e.target))toggleMenu(false)});
$("#suggest-menu").addEventListener("keydown",function(e){
  var items=Array.prototype.slice.call(this.querySelectorAll(".mi")),i=items.indexOf(document.activeElement);
  if(e.key==="ArrowDown"){e.preventDefault();items[Math.min(items.length-1,i+1)].focus()}
  else if(e.key==="ArrowUp"){e.preventDefault();items[Math.max(0,i-1)].focus()}
});
document.addEventListener("keydown",function(e){if(e.key==="Escape"&&!$("#suggest-menu").hidden){toggleMenu(false);$("#sugbtn").focus()}});

/* ---------- painel redimensionável ---------- */
var MIN_SIDE=360,MIN_CHAT=420,mainEl=$("#main"),asideW=0;
function defaultSide(){return Math.round(Math.min(640,Math.max(440,window.innerWidth*0.42)))}
function setSide(px,save){
  var max=Math.max(MIN_SIDE,window.innerWidth-MIN_CHAT);
  asideW=Math.round(Math.max(MIN_SIDE,Math.min(px,max)));
  mainEl.style.setProperty("--aside-w",asideW+"px");
  $("#splitter").setAttribute("aria-valuenow",String(asideW));
  if(save){try{localStorage.setItem("emporio-aside",String(asideW))}catch(e){}}
}
var savedSide=NaN;try{savedSide=parseInt(localStorage.getItem("emporio-aside"),10)}catch(e){}
setSide(isNaN(savedSide)?defaultSide():savedSide,false);
(function(){
  var sp=$("#splitter"),drag=false;
  sp.addEventListener("pointerdown",function(e){drag=true;sp.setPointerCapture(e.pointerId);sp.classList.add("drag");document.body.classList.add("dragging");e.preventDefault()});
  sp.addEventListener("pointermove",function(e){if(drag)setSide(window.innerWidth-e.clientX-4,false)});
  function end(e){if(!drag)return;drag=false;sp.classList.remove("drag");document.body.classList.remove("dragging");setSide(asideW,true)}
  sp.addEventListener("pointerup",end);sp.addEventListener("pointercancel",end);
  sp.addEventListener("dblclick",function(){setSide(defaultSide(),true)});
  sp.addEventListener("keydown",function(e){
    if(e.key==="ArrowLeft"){e.preventDefault();setSide(asideW+24,true)}
    else if(e.key==="ArrowRight"){e.preventDefault();setSide(asideW-24,true)}
    else if(e.key==="Home"){e.preventDefault();setSide(defaultSide(),true)}
  });
  window.addEventListener("resize",function(){setSide(asideW,false)});
})();
$("#msg").addEventListener("keydown",function(e){if(e.key==="Enter"&&!e.shiftKey&&!e.isComposing){e.preventDefault();send($("#msg").value)}});
})();
</script>
</body>
</html>
"""
