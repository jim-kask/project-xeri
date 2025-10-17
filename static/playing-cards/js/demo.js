import { createDeck, shuffle } from "./cards-core.js";
import { renderCardSVG } from "./card-svg.js";

const grid = document.querySelector("#cards-grid");
const btnShuffle = document.querySelector("#btn-shuffle");
const btnFaces = document.querySelector("#btn-faces");

let deck = createDeck();
shuffle(deck);

function draw() {
  grid.innerHTML = "";
  deck.forEach(card => {
    const wrap = document.createElement("div");
    wrap.className = "pcard-wrap";

    // front/back container to allow flip
    const face = document.createElement("div");
    face.className = "pcard-face";

    const front = renderCardSVG({ rank: card.rank, suit: card.suit, faceDown: false, width: 120 });
    front.classList.add("pcard-front");

    const back = renderCardSVG({ rank: card.rank, suit: card.suit, faceDown: true, width: 120 });
    back.classList.add("pcard-back");

    face.appendChild(front);
    face.appendChild(back);

    // click to flip
    wrap.addEventListener("click", () => {
      face.classList.toggle("flipped");
    });

    wrap.appendChild(face);
    grid.appendChild(wrap);
  });
}

btnShuffle.addEventListener("click", () => {
  shuffle(deck);
  draw();
});

btnFaces.addEventListener("click", () => {
  // Toggle all to faces/back
  document.querySelectorAll(".pcard-face").forEach(el => el.classList.toggle("flipped"));
});

draw();
