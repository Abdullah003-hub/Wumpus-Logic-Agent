// ── Game State ───────────────────────────────────────────────────────────
let game = null;
let autoTimer = null;

// Simple game state generator (without full knowledge base reasoning)
function initializeGame(rows, cols, pits) {
  // Place pits, wumpus, and gold randomly
  let cells = [];
  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      cells.push([r, c]);
    }
  }
  
  // Remove safe starting area
  cells = cells.filter(([r, c]) => !(r <= 1 && c <= 1));
  cells.sort(() => Math.random() - 0.5);
  
  const pitSet = new Set();
  const wumpusPos = cells[0];
  const goldPos = cells[1];
  for (let i = 0; i < Math.min(pits, cells.length - 2); i++) {
    pitSet.add(cells[i + 2].join('_'));
  }
  
  return {
    rows, cols, pits,
    agent: [0, 0],
    visited: new Set(['0_0']),
    safe: new Set(['0_0']),
    inferred_pits: new Set(),
    inferred_wumpus: null,
    pit_set: pitSet,
    wumpus: wumpusPos,
    gold: goldPos,
    game_over: false,
    won: false,
    log: [{ msg: 'Game started at (0,0)', kind: 'move' }],
    percepts: { breeze: false, stench: false, glitter: false },
    kb_clauses: []
  };
}

function getPercepts(game, r, c) {
  const breeze = game.pit_set.has(`${r-1}_${c}`) || game.pit_set.has(`${r+1}_${c}`) ||
                 game.pit_set.has(`${r}_${c-1}`) || game.pit_set.has(`${r}_${c+1}`);
  const stench = (game.wumpus && 
                 ((Math.abs(game.wumpus[0] - r) === 1 && game.wumpus[1] === c) ||
                  (Math.abs(game.wumpus[1] - c) === 1 && game.wumpus[0] === r)));
  const glitter = game.gold && game.gold[0] === r && game.gold[1] === c;
  return { breeze, stench, glitter };
}

function moveAgent(game, r, c) {
  if (game.game_over) return;
  
  // Check hazards
  if (game.pit_set.has(`${r}_${c}`)) {
    game.log.push({ msg: `Agent fell into a PIT at (${r},${c})! Game Over.`, kind: 'dead' });
    game.game_over = true;
    game.won = false;
    game.agent = [r, c];
    return;
  }
  
  if (game.wumpus && game.wumpus[0] === r && game.wumpus[1] === c) {
    game.log.push({ msg: `Agent eaten by WUMPUS at (${r},${c})! Game Over.`, kind: 'dead' });
    game.game_over = true;
    game.won = false;
    game.agent = [r, c];
    return;
  }
  
  // Success
  game.agent = [r, c];
  game.visited.add(`${r}_${c}`);
  game.safe.add(`${r}_${c}`);
  game.log.push({ msg: `→ Move to (${r},${c})`, kind: 'move' });
  
  // Get percepts
  const percepts = getPercepts(game, r, c);
  game.percepts = percepts;
  
  if (percepts.glitter) {
    game.log.push({ msg: `★ GLITTER at (${r},${c}) — GOLD FOUND! You win!`, kind: 'win' });
    game.game_over = true;
    game.won = true;
  } else {
    // Simple logic inference
    if (percepts.breeze) {
      game.log.push({ msg: `💨 Breeze detected - pit nearby`, kind: 'infer' });
    } else {
      game.log.push({ msg: `No breeze - adjacent cells are safe`, kind: 'infer' });
    }
    if (percepts.stench) {
      game.log.push({ msg: `💀 Stench detected - wumpus nearby`, kind: 'warn' });
    } else {
      game.log.push({ msg: `No stench - adjacent cells are safe`, kind: 'infer' });
    }
  }
}

function agentStep(game) {
  if (game.game_over) return;
  
  const [ar, ac] = game.agent;
  const adjacent = [];
  
  // Get unvisited adjacent cells
  if (ar > 0 && !game.visited.has(`${ar-1}_${ac}`)) adjacent.push([ar-1, ac]);
  if (ar < game.rows - 1 && !game.visited.has(`${ar+1}_${ac}`)) adjacent.push([ar+1, ac]);
  if (ac > 0 && !game.visited.has(`${ar}_${ac-1}`)) adjacent.push([ar, ac-1]);
  if (ac < game.cols - 1 && !game.visited.has(`${ar}_${ac+1}`)) adjacent.push([ar, ac+1]);
  
  if (adjacent.length > 0) {
    const [nr, nc] = adjacent[Math.floor(Math.random() * adjacent.length)];
    moveAgent(game, nr, nc);
  } else {
    game.log.push({ msg: 'Agent is stuck - no unvisited adjacent cells', kind: 'warn' });
  }
}

// ── UI Update Functions ────────────────────────────────────────────────
function updateUI() {
  if (!game) return;
  
  renderGrid(game);
  updateMetrics(game);
  updatePercepts(game);
  updateKB(game);
  updateLog(game);
  
  if (game.game_over) {
    stopAuto();
    document.getElementById('btn-step').disabled = true;
    document.getElementById('btn-auto').disabled = true;
    showBanner(game.won);
  }
}

function renderGrid(state) {
  const gridEl = document.getElementById('grid');
  gridEl.style.gridTemplateColumns = `repeat(${state.cols}, 88px)`;
  gridEl.innerHTML = '';
  
  const [ar, ac] = state.agent;
  
  // Render from top-left to bottom-right visually
  for (let r = state.rows - 1; r >= 0; r--) {
    for (let c = 0; c < state.cols; c++) {
      const k = `${r}_${c}`;
      const isAgent = r === ar && c === ac;
      const isVisited = state.visited.has(k);
      const isSafe = state.safe.has(k);
      const isPit = state.pit_set.has(k);
      const isWump = state.wumpus && state.wumpus[0] === r && state.wumpus[1] === c;
      const isGold = state.gold && state.gold[0] === r && state.gold[1] === c;
      
      const cell = document.createElement('div');
      cell.className = 'cell';
      cell.innerHTML = `<span class="cell-coord">(${r},${c})</span>`;
      
      let icon = '', label = '';
      
      if (isAgent) {
        cell.classList.add('c-agent');
        icon = '🧭';
        label = 'agent';
      } else if (state.game_over && isGold) {
        cell.classList.add('c-gold');
        icon = '🏆';
        label = 'GOLD';
      } else if (state.game_over && isPit) {
        cell.classList.add('c-pit');
        icon = '🕳';
        label = 'PIT';
      } else if (state.game_over && isWump) {
        cell.classList.add('c-wumpus');
        icon = '👾';
        label = 'WUMPUS';
      } else if (isVisited) {
        cell.classList.add('c-visited');
        icon = '✓';
      } else if (isSafe) {
        cell.classList.add('c-safe');
        label = 'safe';
      } else {
        cell.classList.add('c-fog');
        icon = '?';
      }
      
      if (icon) cell.innerHTML += `<span class="cell-icon">${icon}</span>`;
      if (label) cell.innerHTML += `<span class="cell-label">${label}</span>`;
      
      // Show percepts at current cell
      if (isAgent && !state.game_over && state.percepts) {
        let percSyms = '';
        if (state.percepts.breeze) percSyms += '💨';
        if (state.percepts.stench) percSyms += '💀';
        if (state.percepts.glitter) percSyms += '✨';
        if (percSyms) cell.innerHTML += `<span class="cell-percepts">${percSyms}</span>`;
      }
      
      gridEl.appendChild(cell);
    }
  }
}

function updateMetrics(state) {
  document.getElementById('m-infer').textContent = state.log.length;
  document.getElementById('m-clauses').textContent = state.kb_clauses.length;
  document.getElementById('m-visited').textContent = state.visited.size;
  document.getElementById('m-safe').textContent = state.safe.size;
  document.getElementById('m-pos').textContent = `(${state.agent[0]}, ${state.agent[1]})`;
}

function updatePercepts(state) {
  const el = document.getElementById('percept-display');
  if (state.game_over) {
    el.innerHTML = '<span class="ptag-none">Game over</span>';
    return;
  }
  
  const p = state.percepts || {};
  let html = '';
  if (p.breeze) html += '<span class="ptag ptag-breeze">💨 Breeze</span>';
  if (p.stench) html += '<span class="ptag ptag-stench">💀 Stench</span>';
  if (p.glitter) html += '<span class="ptag ptag-glitter">✨ Glitter</span>';
  if (!html) html = '<span class="ptag-none">None — clear cell</span>';
  el.innerHTML = html;
}

function updateKB(state) {
  const el = document.getElementById('kb-display');
  const clauses = state.kb_clauses;
  if (!clauses.length) {
    el.textContent = 'Building knowledge base...';
    return;
  }
  el.innerHTML = clauses.map(c => `<div>${escapeHtml(c)}</div>`).join('');
  el.scrollTop = el.scrollHeight;
}

function updateLog(state) {
  const el = document.getElementById('log');
  el.innerHTML = state.log.map(e => 
    `<div class="log-entry log-${e.kind}">${escapeHtml(e.msg)}</div>`
  ).join('');
  el.scrollTop = el.scrollHeight;
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;' };
  return text.replace(/[&<>]/g, m => map[m]);
}

function showBanner(won) {
  const banner = document.getElementById('status-banner');
  const overlay = document.getElementById('overlay');
  document.getElementById('banner-title').textContent = won ? '🏆 You Win!' : '☠ Game Over';
  document.getElementById('banner-msg').textContent = won
    ? 'The agent found the gold!'
    : 'The agent encountered a hazard. Better luck next time.';
  banner.className = won ? 'win' : 'lose';
  banner.style.display = 'block';
  overlay.style.display = 'block';
}

function closeBanner() {
  document.getElementById('status-banner').style.display = 'none';
  document.getElementById('overlay').style.display = 'none';
}

// ── Button Handlers ────────────────────────────────────────────────────
function newGame() {
  stopAuto();
  const rows = Math.max(3, Math.min(8, +document.getElementById('inp-rows').value));
  const cols = Math.max(3, Math.min(8, +document.getElementById('inp-cols').value));
  const pits = Math.max(1, Math.min(10, +document.getElementById('inp-pits').value));
  
  game = initializeGame(rows, cols, pits);
  document.getElementById('btn-step').disabled = false;
  document.getElementById('btn-auto').disabled = false;
  closeBanner();
  updateUI();
}

function doStep() {
  if (!game || game.game_over) return;
  agentStep(game);
  updateUI();
}

function toggleAuto() {
  if (autoTimer) {
    stopAuto();
    return;
  }
  document.getElementById('btn-auto').textContent = '⏹ Stop';
  document.getElementById('btn-auto').classList.add('active');
  autoTimer = setInterval(() => {
    if (game?.game_over) {
      stopAuto();
      return;
    }
    doStep();
  }, 550);
}

function stopAuto() {
  if (autoTimer) {
    clearInterval(autoTimer);
    autoTimer = null;
  }
  document.getElementById('btn-auto').textContent = '▶ Auto Run';
  document.getElementById('btn-auto').classList.remove('active');
}

// ── Initialize on page load ────────────────────────────────────────────
window.addEventListener('DOMContentLoaded', () => {
  newGame();
});
