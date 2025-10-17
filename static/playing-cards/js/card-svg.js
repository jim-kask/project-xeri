// card-svg.js
// Minimal flat SVG cards with rounded corners, classic suits, blue dotted back.
// Face cards (J/Q/K) use simple geometric silhouettes.

const SUIT_SYMBOL = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
};

const SUIT_COLOR = {
  S: "var(--black)",
  C: "var(--black)",
  H: "var(--red)",
  D: "var(--red)",
};

function pipText(suit, x, y, size = 26, anchor = "middle") {
  return `
    <text x="${x}" y="${y}" font-size="${size}" text-anchor="${anchor}"
      font-family="Segoe UI Symbol, 'DejaVu Sans', Arial, sans-serif"
      fill="${SUIT_COLOR[suit]}">${SUIT_SYMBOL[suit]}</text>
  `;
}

function corner(rank, suit, x, y) {
  const color = SUIT_COLOR[suit];
  return `
    <g transform="translate(${x},${y})">
      <text x="0" y="0" font-size="26" font-weight="700" fill="${color}"
            font-family="Inter, system-ui, Segoe UI, Arial">${rank}</text>
      <text x="0" y="20" font-size="20"
            font-family="Segoe UI Symbol, 'DejaVu Sans', Arial"
            fill="${color}">${SUIT_SYMBOL[suit]}</text>
    </g>
  `;
}

/** Super-simple silhouettes for J/Q/K */

/** ===== Classic mirrored face cards (modern vector replica) =====
 *  - Full figure, mirrored vertically (like a real deck)
 *  - Palette switches for red/black suits
 *  - Still lightweight SVG geometry (good performance)
 */

const FACE_PALETTE = {
  red:   { suit: "var(--red)",   gold: "#D4AF37", dark: "#111318", light: "#ffffff", accent: "#E23B3B" },
  black: { suit: "var(--black)", gold: "#D4AF37", dark: "#111318", light: "#ffffff", accent: "#E23B3B" },
};

function facePaletteForSuit(suit){
  return (suit === "H" || suit === "D") ? FACE_PALETTE.red : FACE_PALETTE.black;
}

function faceHalf(kind, suit){
  const p = facePaletteForSuit(suit);
  // Shared badge with suit symbol on the chest
  const chestBadge = `
    <circle cx="95" cy="150" r="14" fill="${p.light}" stroke="${p.dark}" stroke-width="2"/>
    <text x="95" y="154" font-size="16" text-anchor="middle"
      font-family="Segoe UI Symbol, 'DejaVu Sans', Arial" fill="${p.suit}">${SUIT_SYMBOL[suit]}</text>
  `;

  // Head + hair + face
  const head = `
    <g>
      <ellipse cx="95" cy="78" rx="22" ry="26" fill="${p.light}" stroke="${p.dark}" stroke-width="2"/>
      <path d="M75 72 q10 10 40 0" fill="none" stroke="${p.dark}" stroke-width="2" stroke-linecap="round"/>
      <circle cx="88" cy="78" r="2" fill="${p.dark}"/>
      <circle cx="102" cy="78" r="2" fill="${p.dark}"/>
      <path d="M88 88 q7 6 14 0" fill="none" stroke="${p.dark}" stroke-width="2" stroke-linecap="round"/>
      <path d="M72 63 q23 -16 46 0 q2 8 -3 12 q-20 8 -40 0 q-5 -4 -3 -12 z" fill="${p.suit}" stroke="${p.dark}" stroke-width="2"/>
    </g>
  `;

  // Neck + collar
  const neck = `
    <rect x="88" y="100" width="14" height="10" rx="3" fill="${p.light}" stroke="${p.dark}" stroke-width="2"/>
    <path d="M76 112 h38 q8 0 10 8 v6 h-58 v-6 q2-8 10-8z" fill="${p.gold}" stroke="${p.dark}" stroke-width="2"/>
  `;

  // Torso pattern (classic red/black + gold motif)
  const torso = `
    <g>
      <rect x="58" y="126" width="74" height="52" rx="10" fill="${p.light}" stroke="${p.dark}" stroke-width="2"/>
      <path d="M58 152 h74" stroke="${p.dark}" stroke-width="2"/>
      <path d="M58 137 h74" stroke="${p.dark}" stroke-width="2" opacity=".7"/>
      <path d="M70 130 h50 v18 h-50z" fill="${p.suit}" opacity=".12"/>
      <path d="M62 130 h10 v10 h-10z M120 130 h10 v10 h-10z M62 168 h10 v10 h-10z M120 168 h10 v10 h-10z"
            fill="${p.gold}" stroke="${p.dark}" stroke-width="1.5"/>
      ${chestBadge}
    </g>
  `;

  // Weapon / attribute per face
  let attribute = "";
  if (kind === "K") {
    // Crown + sword
    attribute = `
      <polygon points="70,48 80,34 95,48 110,34 120,48" fill="${p.gold}" stroke="${p.dark}" stroke-width="2"/>
      <rect x="128" y="110" width="6" height="68" rx="3" fill="${p.dark}"/>
      <path d="M131 112 v-46" stroke="${p.dark}" stroke-width="3"/>
      <polygon points="128,62 134,62 131,52" fill="${p.dark}"/>
    `;
  } else if (kind === "Q") {
    // Tiara + flower
    attribute = `
      <path d="M74 52 q21 -20 42 0" fill="${p.gold}" stroke="${p.dark}" stroke-width="2"/>
      <g transform="translate(132,132)">
        <circle r="7" fill="${p.suit}" stroke="${p.dark}" stroke-width="1.5"/>
        <circle cx="0" cy="0" r="2.3" fill="${p.gold}"/>
        <path d="M0 -12 v-8" stroke="${p.dark}" stroke-width="2"/>
      </g>
    `;
  } else {
    // Jester cap + halberd
    attribute = `
      <path d="M72 50 q12 -16 46 0 q-6 10 -10 10 q-12 -4 -26 0 q-5 0 -10 -10z"
            fill="${p.suit}" stroke="${p.dark}" stroke-width="2"/>
      <path d="M126 92 v56" stroke="${p.dark}" stroke-width="3"/>
      <path d="M126 92 l16 -10 v20 z" fill="${p.suit}" stroke="${p.dark}" stroke-width="2"/>
    `;
  }

  return `
    <g>
      ${attribute}
      ${head}
      ${neck}
      ${torso}
    </g>
  `;
}

function faceClassic(kind, suit){
  // Draw top half, then mirror vertically around card center (y=129)
  const top = faceHalf(kind, suit);
  return `
    <g>
      ${top}
      <g transform="scale(1,-1) translate(0,-258)">${top}</g>
    </g>
  `;
}


function backPattern() {
  // blue dotted diamonds
  return `
  <defs>
    <pattern id="dotPattern" width="10" height="10" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="10" height="10" fill="var(--blue-back)"/>
      <circle cx="5" cy="5" r="1.2" fill="#d6e2f7" opacity=".9"/>
    </pattern>
  </defs>
  <rect x="6" y="6" width="178" height="246" rx="12" ry="12" fill="url(#dotPattern)"/>
  `;
}

export function cardSVG({ rank, suit, faceUp = true }) {
  // viewBox sized to nice rounded card (190x258)
  if (!faceUp) {
    return `
      <svg viewBox="0 0 190 258" aria-hidden="true" role="img">
        <defs></defs>
        <rect x="1" y="1" width="188" height="256" rx="16" ry="16" fill="#fff"/>
        <rect x="1" y="1" width="188" height="256" rx="16" ry="16" fill="none" stroke="#d9e0ea"/>
        ${backPattern()}
      </svg>
    `;
  }


const color = SUIT_COLOR[suit];
const isFace = ["J","Q","K"].includes(rank);

// pips layout for numbers (A uses single large pip)
let centerContent = "";
if (isFace) {
  // NEW: use modern classic mirrored faces
  centerContent = faceClassic(rank, suit);
} else if (rank === "A") {
  centerContent = pipText(suit, 95, 140, 74);
} else {
  // Simple symmetric grid (works well and is readable)
  const pip = (x,y)=>pipText(suit,x,y,28);
  const rows = {
    "2":[[95,90],[95,190]],
    "3":[[95,80],[95,140],[95,200]],
    "4":[[65,95],[125,95],[65,190],[125,190]],
    "5":[[65,95],[125,95],[95,145],[65,200],[125,200]],
    "6":[[65,95],[125,95],[65,150],[125,150],[65,205],[125,205]],
    "7":[[65,80],[125,80],[65,135],[95,160],[125,135],[65,210],[125,210]],
    "8":[[65,80],[125,80],[65,130],[125,130],[65,180],[125,180],[65,230],[125,230]],
    "9":[[65,70],[125,70],[65,115],[125,115],[95,145],[65,190],[125,190],[65,235],[125,235]],
    "10":[[65,70],[125,70],[65,110],[125,110],[65,150],[125,150],[65,190],[125,190],[65,230],[125,230]]
  }[rank] || [];
  centerContent = rows.map(([x,y])=>pip(x,y)).join("");
}



  return `
    <svg viewBox="0 0 190 258" aria-label="${rank} of ${suit}">
      <rect x="1" y="1" width="188" height="256" rx="16" ry="16" fill="#fff"/>
      <rect x="1" y="1" width="188" height="256" rx="16" ry="16" fill="none" stroke="#d9e0ea"/>
      ${corner(rank, suit, 12, 28)}
      <g transform="rotate(180,95,129)">${corner(rank, suit, 12, 28)}</g>
      ${centerContent}
    </svg>
  `;
}
