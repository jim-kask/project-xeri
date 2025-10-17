// SVG playing card renderer (no external assets)
// Usage: renderCardSVG({ rank:"A", suit:"♠", faceDown:false, width:120 })

const SUIT_COLORS = {
  "♠": "#111",
  "♣": "#111",
  "♥": "#c9242b",
  "♦": "#c9242b",
};

const SUIT_NAMES = {
  "♠": "spade",
  "♥": "heart",
  "♦": "diamond",
  "♣": "club",
};

function pipPath(suit) {
  // Simple, clean pip shapes (heart/diamond custom; spade/club stylized)
  switch (suit) {
    case "♥": return "M 50 70 C 35 50, 20 50, 20 65 C 20 80, 40 90, 50 100 C 60 90, 80 80, 80 65 C 80 50, 65 50, 50 70 Z";
    case "♦": return "M 50 20 L 80 60 L 50 100 L 20 60 Z";
    case "♠": return "M 50 20 C 20 45, 30 80, 50 100 C 70 80, 80 45, 50 20 Z M 43 95 h14 v20 h-14 Z";
    case "♣": return "M 50 40 a18 18 0 1 1 0.1 0 M 30 60 a18 18 0 1 1 0.1 0 M 70 60 a18 18 0 1 1 0.1 0 M 43 78 h14 v22 h-14 Z";
  }
}

export function renderCardSVG({ rank, suit, faceDown = false, width = 140, rounded = 12 }) {
  const fill = SUIT_COLORS[suit] || "#111";
  const viewW = 200, viewH = 280; // aspect 5:7
  const height = Math.round((width * viewH) / viewW);

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${viewW} ${viewH}`);
  svg.setAttribute("width", width);
  svg.setAttribute("height", height);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", faceDown ? "Playing card back" : `${rank} of ${SUIT_NAMES[suit] || "suit"}`);
  svg.classList.add("pcard");

  // Card background
  const rect = document.createElementNS(svg.namespaceURI, "rect");
  rect.setAttribute("x", "2");
  rect.setAttribute("y", "2");
  rect.setAttribute("rx", rounded);
  rect.setAttribute("ry", rounded);
  rect.setAttribute("width", viewW - 4);
  rect.setAttribute("height", viewH - 4);
  rect.setAttribute("fill", faceDown ? "url(#pcard-back)" : "#fff");
  rect.setAttribute("stroke", "#d0d4d9");
  rect.setAttribute("stroke-width", "3");
  svg.appendChild(rect);

  // Define back pattern once per page
  ensureDefs(svg.ownerDocument || document);

  if (faceDown) return svg;

  // Corner rank + suit (top-left)
  const gTL = document.createElementNS(svg.namespaceURI, "g");
  gTL.setAttribute("transform", "translate(14, 22)");
  const rankText = textEl(svg, rank, 0, 0, fill, 28, "700", "start", "hanging", "ui-sans-serif, system-ui, Segoe UI, Roboto, Helvetica, Arial");
  const suitText = textEl(svg, suit, 2, 24, fill, 22, "700", "start", "hanging", "ui-sans-serif, system-ui, Segoe UI, Roboto, Helvetica, Arial");
  gTL.append(rankText, suitText);
  svg.appendChild(gTL);

  // Corner (bottom-right, rotated)
  const gBR = document.createElementNS(svg.namespaceURI, "g");
  gBR.setAttribute("transform", `translate(${viewW - 14}, ${viewH - 22}) rotate(180)`);
  gBR.append(rankText.cloneNode(true), suitText.cloneNode(true));
  svg.appendChild(gBR);

  // Center pip (scaled)
  const center = document.createElementNS(svg.namespaceURI, "path");
  center.setAttribute("d", pipPath(suit));
  center.setAttribute("fill", fill);
  center.setAttribute("opacity", "0.9");
  center.setAttribute("transform", "translate(0,10) scale(1.4)");
  svg.appendChild(center);

  // For numbered cards, add small pips grid (simple pass for v1)
  const number = parseInt(rank, 10);
  if (!Number.isNaN(number)) {
    placeNumberPips(svg, suit, fill, number);
  }

  return svg;
}

function textEl(svg, txt, x, y, fill, size, weight, anchor, baseline, family) {
  const t = document.createElementNS(svg.namespaceURI, "text");
  t.textContent = txt;
  t.setAttribute("x", x);
  t.setAttribute("y", y);
  t.setAttribute("fill", fill);
  t.setAttribute("font-size", size);
  t.setAttribute("font-weight", weight);
  t.setAttribute("text-anchor", anchor);
  t.setAttribute("dominant-baseline", baseline);
  t.setAttribute("font-family", family);
  return t;
}

function ensureDefs(doc) {
  if (doc.getElementById("pcard-back")) return;
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.style.position = "absolute";
  svg.style.width = "0";
  svg.style.height = "0";
  const defs = document.createElementNS(svg.namespaceURI, "defs");
  const pattern = document.createElementNS(svg.namespaceURI, "pattern");
  pattern.setAttribute("id", "pcard-back");
  pattern.setAttribute("patternUnits", "userSpaceOnUse");
  pattern.setAttribute("width", "16");
  pattern.setAttribute("height", "16");
  const r = document.createElementNS(svg.namespaceURI, "rect");
  r.setAttribute("width", "16"); r.setAttribute("height", "16"); r.setAttribute("fill", "#1f3b64");
  const c1 = document.createElementNS(svg.namespaceURI, "circle");
  c1.setAttribute("cx", "4"); c1.setAttribute("cy", "4"); c1.setAttribute("r", "1.5"); c1.setAttribute("fill", "#fff");
  const c2 = document.createElementNS(svg.namespaceURI, "circle");
  c2.setAttribute("cx", "12"); c2.setAttribute("cy", "12"); c2.setAttribute("r", "1.5"); c2.setAttribute("fill", "#fff");
  pattern.append(r, c1, c2);
  defs.appendChild(pattern);
  svg.appendChild(defs);
  document.body.appendChild(svg);
}

function placeNumberPips(svg, suit, fill, n) {
  const path = pipPath(suit);
  const g = document.createElementNS(svg.namespaceURI, "g");
  const positions = {
    2: [[100, 70], [100, 210]],
    3: [[100, 55], [100, 140], [100, 225]],
    4: [[65, 75], [135, 75], [65, 205], [135, 205]],
    5: [[65, 75], [135, 75], [100, 140], [65, 205], [135, 205]],
    6: [[65, 65], [135, 65], [65, 140], [135, 140], [65, 215], [135, 215]],
    7: [[100, 45], [65, 90], [135, 90], [65, 140], [135, 140], [65, 210], [135, 210]],
    8: [[65, 60], [135, 60], [65, 110], [135, 110], [65, 170], [135, 170], [65, 220], [135, 220]],
    9: [[100, 45], [65, 80], [135, 80], [65, 120], [135, 120], [100, 155], [65, 200], [135, 200], [100, 235]],
    10:[[65, 55],[135,55],[65,95],[135,95],[65,135],[135,135],[65,175],[135,175],[65,215],[135,215]],
  };
  const pts = positions[n] || [];
  for (const [x, y] of pts) {
    const p = document.createElementNS(svg.namespaceURI, "path");
    p.setAttribute("d", path);
    p.setAttribute("fill", fill);
    p.setAttribute("transform", `translate(${x - 50}, ${y - 60}) scale(0.5)`);
    g.appendChild(p);
  }
  svg.appendChild(g);
}
