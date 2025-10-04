// --- Boot ---
const root = document.getElementById('stress-root');
const username = root.dataset.username;
const room = root.dataset.room;
const socket = io('/stress');

socket.emit('join', { username, room });

// --- Elements ---
const handDiv   = document.getElementById('your-hand');
const oppCount  = document.getElementById('opp-count');
const pileLeft  = document.getElementById('pile-left');
const pileRight = document.getElementById('pile-right');
const drawBtn   = document.getElementById('draw-btn');
const hintBar   = document.getElementById('hint-bar');

// --- Local UI state ---
let currentState = null;
let selectedCard = null;

// --- Helpers ---
const rank = (card) => parseInt(card.slice(0, -1), 10);

const canPlayClientSide = (card, pileIndex) => {
  if (!currentState || !currentState.center) return false;
  const top = currentState.center[pileIndex];
  if (!top) return false;
  return Math.abs(rank(card) - rank(top)) === 1;
};

const countValidMoves = (hand) => {
  if (!currentState || !currentState.center || currentState.center.length < 2) {
    return { total: 0, left: 0, right: 0 };
  }
  let left = 0, right = 0;
  hand.forEach(card => {
    if (canPlayClientSide(card, 0)) left++;
    if (canPlayClientSide(card, 1)) right++;
  });
  return { total: left + right, left, right };
};

const clearSelection = () => {
  selectedCard = null;
  [...handDiv.querySelectorAll('.card')].forEach(el => el.classList.remove('selected'));
  [pileLeft, pileRight].forEach(p => p.classList.remove('playable', 'invalid'));
  updateHint(); // refresh message when selection cleared
};

const markPlayablePiles = () => {
  [pileLeft, pileRight].forEach((p, idx) => {
    p.classList.toggle('playable', selectedCard ? canPlayClientSide(selectedCard, idx) : false);
  });
};

const updateHint = () => {
  if (!currentState) return;
  // Remove any previous state classes
  hintBar.classList.remove('hint-ok', 'hint-warn');

  const hand = currentState.your_hand || [];
  const moves = countValidMoves(hand);

  if (selectedCard) {
    const l = canPlayClientSide(selectedCard, 0);
    const r = canPlayClientSide(selectedCard, 1);
    if (l || r) {
      hintBar.textContent = `Selected ${selectedCard}. Valid pile${l && r ? 's' : ''}: ${l ? 'Left' : ''}${l && r ? ' & ' : ''}${r ? 'Right' : ''}. Click a pile to play.`;
      hintBar.classList.add('hint-ok');
    } else {
      hintBar.textContent = `Selected ${selectedCard}. No valid pile — pick another card or press Draw.`;
      hintBar.classList.add('hint-warn');
    }
    return;
  }

  if (moves.total > 0) {
    hintBar.innerHTML = `You have <strong>${moves.total}</strong> valid move${moves.total === 1 ? '' : 's'} — Left: <strong>${moves.left}</strong>, Right: <strong>${moves.right}</strong>. Select a card, then click a pile.`;
    hintBar.classList.add('hint-ok');
  } else {
    hintBar.textContent = 'No valid moves detected. You may need to press Draw.';
    hintBar.classList.add('hint-warn');
  }
};

// --- Render ---
const render = (state) => {
  currentState = state;

  // Opponent + center piles
  oppCount.textContent = state.opponent_count + ' cards';
  pileLeft.textContent  = state.center[0] || '?';
  pileRight.textContent = state.center[1] || '?';

  // Your hand
  handDiv.innerHTML = '';
  state.your_hand.forEach(card => {
    const c = document.createElement('button');
    c.type = 'button';
    c.className = 'card';
    c.textContent = card;
    c.onclick = () => {
      if (selectedCard === card) {
        clearSelection();
        return;
      }
      selectedCard = card;
      [...handDiv.querySelectorAll('.card')].forEach(el => el.classList.remove('selected'));
      c.classList.add('selected');
      markPlayablePiles();
      updateHint();
    };
    handDiv.appendChild(c);
  });

  // If the selected card got played, clear selection
  if (selectedCard && !state.your_hand.includes(selectedCard)) {
    clearSelection();
  } else {
    // keep pile highlights in sync
    markPlayablePiles();
    updateHint();
  }
};

// --- Socket handlers ---
socket.on('update_state', (state) => render(state));
socket.on('room_full', (msg) => alert(msg?.message || 'Room is full.'));
socket.on('no_draw', (msg) => alert(msg?.message || 'Cannot draw.'));

// Optional: if you added invalid_play on the server
socket.on('invalid_play', () => {
  // brief “shake” is handled via .invalid class; we can also warn here if you want.
});

// --- Actions ---
drawBtn.onclick = () => socket.emit('draw_request', { room });

// Click piles to attempt play
[pileLeft, pileRight].forEach((pileEl) => {
  pileEl.addEventListener('click', () => {
    if (!selectedCard) return;

    const pileIndex = parseInt(pileEl.dataset.pile, 10) || 0;

    // Client-side guard for quick feedback
    if (!canPlayClientSide(selectedCard, pileIndex)) {
      pileEl.classList.add('invalid');
      setTimeout(() => pileEl.classList.remove('invalid'), 200);
      return;
    }

    socket.emit('play_card', { username, room, card: selectedCard, pile: pileIndex });
    clearSelection(); // optimistic; server will re-render
  });
});
