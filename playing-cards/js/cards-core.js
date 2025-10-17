// Minimal playing cards core (ES module)

/** Suits and ranks (A high; tweak as needed) */
export const SUITS = ["♠", "♥", "♦", "♣"];
export const RANKS = ["A","2","3","4","5","6","7","8","9","10","J","Q","K"];

/** Fresh ordered 52-card deck */
export function createDeck() {
  const deck = [];
  for (const suit of SUITS) {
    for (const rank of RANKS) {
      deck.push({ suit, rank, code: `${rank}${suit}` });
    }
  }
  return deck;
}

/** Fisher–Yates shuffle (in place) */
export function shuffle(deck, rng = Math.random) {
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

/** Deal n cards; returns [hand, remaining] */
export function deal(deck, n = 1) {
  const hand = deck.slice(0, n);
  const remaining = deck.slice(n);
  return [hand, remaining];
}

/** Helpers */
const rankOrder = new Map(RANKS.map((r, i) => [r, i]));
export function compareCards(a, b) {
  if (a.suit !== b.suit) return a.suit.localeCompare(b.suit);
  return rankOrder.get(a.rank) - rankOrder.get(b.rank);
}

export function serialize(card) { return `${card.rank}${card.suit}`; }
export function parse(code) {
  const suit = code.slice(-1);
  const rank = code.slice(0, -1);
  if (!SUITS.includes(suit) || !RANKS.includes(rank)) throw new Error("Bad code");
  return { suit, rank, code };
}
