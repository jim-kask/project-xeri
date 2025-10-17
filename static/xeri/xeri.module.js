import { cardSVG } from "../playing-cards/js/card-svg.js";

const state = {
  pile: [],
  hand: [],
  oppHand: [],
  stock: [],
  captures: [],
  oppCaptures: [],
  xeriPts: 0,
  oppXeriPts: 0,
  selected: -1,
};

const handEl = document.getElementById("hand");
const pileEl = document.getElementById("center-pile");
const playBtn = document.getElementById("playBtn");
const pop = document.getElementById("xeri-pop");
const scoreboard = document.getElementById("scoreboard");

// --- helpers ---
function makeDeck(){
  const s=["S","H","D","C"], r=["A","2","3","4","5","6","7","8","9","10","J","Q","K"];
  const d=[]; s.forEach(S=>r.forEach(R=>d.push({suit:S,rank:R})));
  return d;
}
function shuffle(a){ for(let i=a.length-1;i>0;i--){ const j=Math.floor(Math.random()*(i+1)); [a[i],a[j]]=[a[j],a[i]]; } return a; }
function top(){ return state.pile[state.pile.length-1]; }
function canCapture(t, card){ if(!t) return false; if(card.rank==="J" && state.pile.length>0) return true; return t.rank===card.rank; }
function xeriPtsBefore(card){
  if(state.pile.length!==1) return 0;
  const only=state.pile[0];
  if(card.rank==="J") return (only.rank==="J")?10:0; // Denexa default
  return (only.rank===card.rank)?10:0;
}

// --- rendering ---
function renderPile(){
  pileEl.innerHTML="";
  state.pile.forEach((c,i)=>{
    const el=document.createElement("div");
    el.className="card";
    el.style.zIndex=1+i;
    el.style.transform=`translate(${i}px,${i}px)`;
    el.innerHTML=cardSVG({rank:c.rank,suit:c.suit,faceUp:true});
    pileEl.appendChild(el);
  });
}
function renderHand(){
  handEl.innerHTML="";
  state.hand.forEach((c,i)=>{
    const el=document.createElement("div");
    el.className="card";
    if(i===state.selected) el.classList.add("selected");
    el.innerHTML=cardSVG({rank:c.rank,suit:c.suit,faceUp:true});
    el.addEventListener("click",()=>{
      state.selected=(state.selected===i?-1:i);
      playBtn.disabled=(state.selected<0);
      renderHand();
    });
    handEl.appendChild(el);
  });
}
function updateBoard(){
  scoreboard.textContent=`You: ${state.captures.length} | CPU: ${state.oppCaptures.length} — Xeri(+): ${state.xeriPts}/${state.oppXeriPts}`;
}
function flashXeri(){ pop.classList.add("show"); setTimeout(()=>pop.classList.remove("show"), 700); }

// --- flow ---
function maybeDeal(){
  if(state.hand.length===0 && state.oppHand.length===0){
    if(state.stock.length>0){
      state.hand=state.stock.splice(0,6);
      state.oppHand=state.stock.splice(0,6);
      renderHand();
    } else {
      alert("Round finished!");
    }
  }
}
function cpuPlay(){
  let idx = state.oppHand.findIndex(c=>canCapture(top(), c));
  if(idx<0) idx = Math.floor(Math.random()*state.oppHand.length);
  const card = state.oppHand.splice(idx,1)[0];
  const x = xeriPtsBefore(card);
  if(canCapture(top(), card)){
    const taken=[...state.pile, card]; state.pile=[];
    state.oppCaptures.push(...taken); if(x>0) state.oppXeriPts+=x;
  } else { state.pile.push(card); }
  renderPile(); updateBoard(); maybeDeal();
}
function playerPlay(){
  if(state.selected<0) return;
  const card = state.hand.splice(state.selected,1)[0];
  state.selected=-1; playBtn.disabled=true;
  const x = xeriPtsBefore(card);
  if(canCapture(top(), card)){
    const taken=[...state.pile, card]; state.pile=[];
    state.captures.push(...taken); if(x>0){ state.xeriPts+=x; flashXeri(); }
  } else { state.pile.push(card); }
  renderPile(); renderHand(); updateBoard(); maybeDeal();
  setTimeout(cpuPlay, 500);
}

// --- boot ---
function boot(){
  const deck = shuffle(makeDeck());
  state.hand    = deck.splice(0,6);
  state.oppHand = deck.splice(0,6);
  state.pile    = deck.splice(0,4);
  // redeal if top Jack or last two equal
  while(state.pile.length && (
    state.pile.at(-1).rank==="J" ||
    (state.pile.length>=2 && state.pile.at(-1).rank===state.pile.at(-2).rank)
  )){
    deck.push(...state.pile); shuffle(deck); state.pile=deck.splice(0,4);
  }
  state.stock = deck;
  renderPile(); renderHand(); updateBoard();
}

document.getElementById("playBtn").addEventListener("click", playerPlay);
boot();
