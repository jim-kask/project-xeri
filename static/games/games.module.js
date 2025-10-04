// /static/games/games.module.js
// Self-contained games UI that does NOT touch chat.


(function(){
const TPL = /*html*/`
<style>
:host{display:block;height:100%}
.wrap{height:100%;background:#e9eef3;border-radius:20px;padding:12px;box-sizing:border-box;}
.title{font:600 18px/1.2 system-ui;margin:4px 0 12px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(120px,1fr));gap:12px}
.card{background:#0f172a;color:#e2e8f0;border-radius:14px;padding:12px;cursor:pointer;display:flex;flex-direction:column;align-items:center;gap:6px;box-shadow:0 3px 10px rgba(0,0,0,.12)}
.card:hover{transform:translateY(-1px)}
.btn{border:0;border-radius:10px;padding:8px 12px;cursor:pointer}
.btn.primary{background:#2563eb;color:#fff}
.btn.ghost{background:#0f172a;color:#e2e8f0}
.row{display:flex;gap:8px;align-items:center}
.bar{display:flex;justify-content:space-between;align-items:center;margin:6px 0 12px}
.tables{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}
.tile{background:#0f172a;color:#e2e8f0;border-radius:12px;padding:10px;}
.muted{opacity:.7}
.pill{display:inline-block;background:#334155;color:#e2e8f0;border-radius:999px;padding:2px 8px;margin-left:6px;font-size:12px}
.section{background:#0f172a;color:#e2e8f0;border-radius:12px;padding:10px;margin:8px 0}
.cards{display:flex;gap:8px;flex-wrap:wrap;min-height:60px}
.cardv{background:#fff;border-radius:10px;padding:8px 10px;min-width:40px;text-align:center;cursor:pointer}
.cardv.disabled{opacity:.5;cursor:not-allowed}
.players{display:flex;gap:6px;flex-wrap:wrap}
.badge{background:#334155;color:#e2e8f0;border-radius:999px;padding:2px 8px;font-size:12px}
.badge.turn{background:#16a34a}
</style>
<div class="wrap">
<div id="screen"></div>
</div>
`;


class XeriGamesApp extends HTMLElement{
constructor(){ super(); this.attachShadow({mode:'open'}).innerHTML = TPL; this.$ = (q)=>this.shadowRoot.querySelector(q); this.state={route:'gallery', params:{}, user:'guest'}; }
connectedCallback(){ }


init(opts){ this.state.user = opts?.username||'guest'; this.render(); }


navigate(route, params={}){ this.state.route=route; this.state.params=params; this.render(); }


// --- API helpers
async api(path, opts){ const r=await fetch(path, Object.assign({headers:{'Content-Type':'application/json'}}, opts)); return r.json(); }


// --- SOCKET (lazy)
sock(){ if(this._io) return this._io; this._io = io('/games', {transports:['websocket']}); return this._io; }


// --- RENDERS
async render(){
const root = this.$('#screen');
if(this.state.route==='gallery'){
const games = await this.api('/api/games');
root.innerHTML = `
<div class="title">Games</div>
<div class="grid">
${games.map(g=>`<div class="card" data-id="${g.id}">
<div style="font-size:28px">${g.icon||'🃏'}</div>
<div>${g.name}</div>
</div>`).join('')}
</div>`;
root.querySelectorAll('.card').forEach(el=>{
el.addEventListener('click',()=> this.navigate('tables', {gameId: el.dataset.id}));
});
}


if(this.state.route==='tables'){
const {gameId} = this.state.params; const meta = await this.api(`/api/games/${gameId}`);
const tables = await this.api(`/api/games/${gameId}/tables`);
root.innerHTML = `
  <div class="bar">
    <div class="row">
      <!-- TODO: Add content here (buttons, tables list, etc.) -->
    </div>
  </div>
`;
})();  // ← keep this closure AFTER the backtick
