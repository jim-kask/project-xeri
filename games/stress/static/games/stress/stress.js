// --- Boot ---
const root = document.getElementById('stress-root');
const username = root.dataset.username;
const room = root.dataset.room;
const socket = io('/stress');

// Elements
const lobby       = document.getElementById('lobby');
const lobbyStatus = document.getElementById('lobby-status');
const readyBtn    = document.getElementById('ready-btn');
const unreadyBtn  = document.getElementById('unready-btn');

const board   = document.querySelector('.stress-board');
const handDiv = document.getElementById('your-hand');
const oppCount = document.getElementById('opp-count');
const pileLeft = document.getElementById('pile-left');
const pileRight = document.getElementById('pile-right');
const drawBtn = document.getElementById('draw-btn');
const hintBar = document.getElementById('hint-bar');

let currentState = null;
let selectedCard = null;
let joined = false;

// ---- join flow (with password retry) ----
function attemptJoin(password) {
  socket.emit('join', { username, room, password });
}

socket.on('connect', () => attemptJoin());
socket.on('join_denied', (info) => {
  if (info?.reason === 'password_required') {
    const pw = prompt('This table is locked. Enter password:');
    if (pw !== null) attemptJoin(pw);
  } else if (info?.reason === 'room_full') {
    alert('Room is full.');
  }
});

// ---- lobby + ready ----
socket.on('lobby', (data) => {
  const players = data.players || [];
  const ready = new Set(data.ready || []);
  const iAmReady = ready.has(username);
  const bothPresent = players.length === 2;

  lobby.style.display = 'flex';
  board.style.display = data.started ? 'flex' : 'none';

  if (!data.started) {
    // status text
    if (!bothPresent) {
      lobbyStatus.textContent = `Waiting for players… (${players.length}/2)`;
    } else {
      const other = players.find(p => p !== username) || 'opponent';
      lobbyStatus.textContent = ready.size === 2
        ? 'Both ready. Starting…'
        : `Both players present. Waiting for Ready from ${iAmReady ? other : 'you'}.`;
    }

    // buttons
    readyBtn.style.display   = iAmReady ? 'none' : 'inline-block';
    unreadyBtn.style.display = iAmReady ? 'inline-block' : 'none';
  }
});

readyBtn?.addEventListener('click', () => {
  socket.emit('ready', { username, room });
});
unreadyBtn?.addEventListener('click', () => {
  socket.emit('cancel_ready', { username, room });
});

// ---- start ----
socket.on('start', () => {
  lobby.style.display = 'none';
  board.style.display = 'flex';
});

// ---- gameplay helpers (same as before) ----
const rank = (card) => parseInt(card.slice(0, -1), 10);
const canPlayClientSide = (card, pileIdx) => {
  if (!currentState) return false;
  const center = currentState.center || [];
  const top = center[pileIdx];
  if (!top) return false;
  const r1 = rank(card), r2 = rank(top);
  return Math.abs(r1 - r2) === 1 || Math.abs(r1 - r2) === 12; // wrap around (A<->K)
};

const countValidMoves = (hand) => {
  if (!hand || !hand.length) return { total: 0, left: 0, right: 0 };
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
  updateHint();
};

const markPlayablePiles = () => {
  [pileLeft, pileRight].forEach((p, idx) => {
    p.classList.toggle('playable', selectedCard ? canPlayClientSide(selectedCard, idx) : false);
  });
};

const updateHint = () => {
  if (!currentState) return;
  hintBar.classList.remove('hint-ok', 'hint-warn');

  const hand = currentState.your_hand || [];
  const moves = countValidMoves(hand);

  if (!currentState.active) {
    hintBar.textContent = 'Game not active yet. Waiting to start.';
    return;
  }

  if (moves.total > 0) {
    hintBar.textContent = `You have ${moves.total} valid move${moves.total>1?'s':''} (left: ${moves.left}, right: ${moves.right}). Select a card, then a pile.`;
    hintBar.classList.add('hint-ok');
  } else {
    hintBar.textContent = 'No valid moves detected. You may need to press Draw.';
    hintBar.classList.add('hint-warn');
  }
};

// ---- render/update ----
const render = (state) => {
  currentState = state;

  oppCount.textContent = (state.opponent_count || 0) + ' cards';
  pileLeft.textContent  = state.center?.[0] || '?';
  pileRight.textContent = state.center?.[1] || '?';

  handDiv.innerHTML = '';
  (state.your_hand || []).forEach(card => {
    const c = document.createElement('button');
    c.type = 'button';
    c.className = 'card';
    c.textContent = card;
    c.onclick = () => {
      if (selectedCard === card) { clearSelection(); return; }
      selectedCard = card;
      [...handDiv.querySelectorAll('.card')].forEach(el => el.classList.remove('selected'));
      c.classList.add('selected');
      markPlayablePiles();
      updateHint();
    };
    handDiv.appendChild(c);
  });

  updateHint();
};

socket.on('update_state', (state) => render(state));
socket.on('invalid_play', () => {
  hintBar.textContent = 'That move is invalid.';
  hintBar.classList.add('hint-warn');
  setTimeout(updateHint, 800);
});

[pileLeft, pileRight].forEach((pileEl) => {
  pileEl.addEventListener('click', () => {
    if (!selectedCard) return;
    const pileIndex = parseInt(pileEl.dataset.pile, 10) || 0;

    if (!canPlayClientSide(selectedCard, pileIndex)) {
      pileEl.classList.add('invalid');
      setTimeout(() => pileEl.classList.remove('invalid'), 200);
      return;
    }
    socket.emit('play_card', { username, room, card: selectedCard, pile: pileIndex });
    clearSelection();
  });
});

drawBtn.addEventListener('click', () => {
  socket.emit('draw_request', { room });
});
