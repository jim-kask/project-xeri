// cards-core.js
import { cardSVG } from "./card-svg.js";

const SUITS = ["S","H","D","C"];
const RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"];

export function makeDeck(){
  const deck = [];
  for(const s of SUITS){
    for(const r of RANKS){
      deck.push({ rank:r, suit:s, faceUp:true, id:`${r}${s}-${Math.random().toString(36).slice(2,8)}` });
    }
  }
  return deck;
}

export function shuffle(deck){
  for(let i = deck.length -1; i>0; i--){
    const j = Math.floor(Math.random()*(i+1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

export function flipAll(deck){
  const anyDown = deck.some(c => !c.faceUp);
  for(const c of deck){ c.faceUp = anyDown ? true : false; }
}

export function renderDeck(container, deck){
  container.innerHTML = "";
  for(const card of deck){
    const el = document.createElement("div");
    el.className = "card";
    el.innerHTML = cardSVG({ rank:card.rank, suit:card.suit, faceUp:card.faceUp });
    el.title = `${card.rank} of ${longSuit(card.suit)} (click to flip)`;
    el.addEventListener("click", () => {
      card.faceUp = !card.faceUp;
      el.innerHTML = cardSVG(card);
    });
    container.appendChild(el);
  }
}

function longSuit(s){
  return {S:"Spades", H:"Hearts", D:"Diamonds", C:"Clubs"}[s] || s;
}
