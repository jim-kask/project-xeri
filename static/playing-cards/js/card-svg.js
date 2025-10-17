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
function faceSilhouette(kind, suit) {
  const color = SUIT_COLOR[suit];
  // base bust
  const bust = `
    <circle cx="95" cy="90" r="26" fill="${color}" />
    <rect x="62" y="122" rx="18" ry="18" width="66" height="42" fill="${color}" />
  `;
  // variants
  let adorn = "";
  if (kind === "K") {
    adorn = `<polygon points="69,65 85,50 95,66 105,50 121,65" fill="${color}" />`;
  } else if (kind === "Q") {
    adorn = `
      <ellipse cx="95" cy="68" rx="22" ry="10" fill="${color}" />
      <circle cx="110" cy="63" r="3" fill="#fff" opacity=".9"/>
    `;
  } else if (kind === "J") {
    adorn = `<path d="M70 66 Q95 45 120 66" fill="none" stroke="${color}" stroke-width="10" stroke-linecap="round"/>`;
  }
  return `<g>${adorn}${bust}</g>`;
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
    centerContent = faceSilhouette(rank, suit);
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
