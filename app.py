"""
Wumpus World Knowledge-Based Agent — Flask Backend
Propositional Logic with Resolution Refutation Inference Engine
"""

from flask import Flask, render_template, request, jsonify, session
import random
import json
import uuid

app = Flask(__name__)
app.secret_key = "wumpus-secret-key-2024"

# ─────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE & RESOLUTION ENGINE
# ─────────────────────────────────────────────────────────────────────────────

class Clause:
    """A CNF clause — a frozenset of literal strings like 'P_1_2' or '!P_1_2'."""

    def __init__(self, literals):
        self.literals = frozenset(literals)

    def __eq__(self, other):
        return self.literals == other.literals

    def __hash__(self):
        return hash(self.literals)

    def __repr__(self):
        return "(" + " ∨ ".join(sorted(self.literals)) + ")"

    def is_tautology(self):
        for lit in self.literals:
            if negate(lit) in self.literals:
                return True
        return False

    def is_empty(self):
        return len(self.literals) == 0


def negate(lit: str) -> str:
    return lit[1:] if lit.startswith("!") else "!" + lit


def resolve(c1: Clause, c2: Clause) -> list:
    """
    Resolution Rule: given two clauses, find all resolvents.
    For each literal in c1 whose negation appears in c2, produce a resolvent
    by combining the two clauses and removing the complementary pair.
    """
    resolvents = []
    for lit in c1.literals:
        neg = negate(lit)
        if neg in c2.literals:
            new_lits = (c1.literals - {lit}) | (c2.literals - {neg})
            resolvent = Clause(new_lits)
            if not resolvent.is_tautology():
                resolvents.append(resolvent)
    return resolvents


class KnowledgeBase:
    """
    Propositional Logic Knowledge Base using Resolution Refutation.

    Variables:
        P_r_c  — there IS a pit at (r, c)
        W_r_c  — there IS a wumpus at (r, c)

    Percept encoding (for cell r,c):
        Breeze:  B_r_c  — agent perceives breeze at (r,c)
        Stench:  S_r_c  — agent perceives stench at (r,c)

    Key axioms added via TELL:
        - !B_r_c → ¬P for all adjacent cells
        -  B_r_c → (P_adj1 ∨ P_adj2 ∨ ...)
        - !S_r_c → ¬W for all adjacent cells
        -  S_r_c → (W_adj1 ∨ W_adj2 ∨ ...)
        - Agent is alive at (r,c) → !P_r_c ∧ !W_r_c
    """

    def __init__(self):
        self.clauses: set[Clause] = set()
        self.infer_steps = 0

    def tell(self, clause_lits: list):
        """Add a clause to the KB (ignores duplicates and tautologies)."""
        cl = Clause(clause_lits)
        if not cl.is_tautology():
            self.clauses.add(cl)

    def ask(self, query_lit: str, max_iter: int = 1000) -> bool:
        """
        Resolution Refutation: prove query_lit by refuting its negation.
        Returns True if query_lit is entailed by the KB.
        """
        negated = negate(query_lit)
        working = set(self.clauses)
        working.add(Clause([negated]))

        new_clauses: set[Clause] = set()
        clauses_list = list(working)

        for _ in range(max_iter):
            self.infer_steps += 1
            found_new = False

            for i in range(len(clauses_list)):
                for j in range(i + 1, len(clauses_list)):
                    resolvents = resolve(clauses_list[i], clauses_list[j])
                    for r in resolvents:
                        if r.is_empty():
                            return True          # Contradiction found — query proven
                        if r not in working and r not in new_clauses:
                            new_clauses.add(r)
                            found_new = True

            if not found_new:
                return False                     # No new clauses — not entailed

            for c in new_clauses:
                working.add(c)
            clauses_list = list(working)
            new_clauses.clear()

            if len(clauses_list) > 3000:         # Safety cap
                return False

        return False

    def clause_count(self) -> int:
        return len(self.clauses)

    def clauses_as_strings(self) -> list:
        return [str(c) for c in sorted(self.clauses, key=str)]


# ─────────────────────────────────────────────────────────────────────────────
# GAME STATE
# ─────────────────────────────────────────────────────────────────────────────

class WumpusGame:
    def __init__(self, rows: int = 4, cols: int = 4, num_pits: int = 3):
        self.rows = rows
        self.cols = cols
        self.num_pits = num_pits
        self.kb = KnowledgeBase()
        self.log: list[dict] = []

        # Hidden ground truth
        self.pit_set: set[tuple] = set()
        self.wumpus: tuple | None = None
        self.gold: tuple | None = None

        # Agent state
        self.agent_r = 0
        self.agent_c = 0
        self.visited: set[tuple] = set()
        self.safe_proven: set[tuple] = set()
        self.inferred_pits: set[tuple] = set()
        self.inferred_wumpus: tuple | None = None
        self.game_over = False
        self.won = False

        self._place_objects()
        self._initialize_start()

    def _key(self, r, c):
        return (r, c)

    def _adjacent(self, r, c) -> list:
        result = []
        if r > 0:           result.append((r - 1, c))
        if r < self.rows-1: result.append((r + 1, c))
        if c > 0:           result.append((r, c - 1))
        if c < self.cols-1: result.append((r, c + 1))
        return result

    def _place_objects(self):
        """Randomly place pits, wumpus, and gold, avoiding start cell neighborhood."""
        forbidden = {(0, 0)}
        for r, c in self._adjacent(0, 0):
            forbidden.add((r, c))

        all_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if (r, c) not in forbidden]
        random.shuffle(all_cells)

        idx = 0
        for _ in range(self.num_pits):
            if idx < len(all_cells):
                self.pit_set.add(all_cells[idx])
                idx += 1

        if idx < len(all_cells):
            self.wumpus = all_cells[idx]; idx += 1
        if idx < len(all_cells):
            self.gold = all_cells[idx]

    def _initialize_start(self):
        """Mark start cell as visited and safe, then perceive."""
        self.visited.add((0, 0))
        self.safe_proven.add((0, 0))
        self.kb.tell(["!P_0_0"])
        self.kb.tell(["!W_0_0"])
        percepts = self._get_percepts(0, 0)
        self._tell_percepts(0, 0, percepts)
        self._run_inference()
        self._add_log(f"Agent starts at (0,0).", "move")

    def _get_percepts(self, r, c) -> dict:
        breeze = any((ar, ac) in self.pit_set for ar, ac in self._adjacent(r, c))
        stench = self.wumpus is not None and self.wumpus in self._adjacent(r, c)
        glitter = self.gold == (r, c)
        return {"breeze": breeze, "stench": stench, "glitter": glitter}

    def _tell_percepts(self, r, c, percepts: dict):
        """
        TELL the KB new propositional clauses based on perceived data at (r,c).

        Biconditional encoding split into CNF:
          B_r_c ↔ ⋁(P_adj)  becomes:
            Forward:  ¬B_r_c → ¬P_adj  for each adj  (¬P_adj as unit clause)
            Backward: B_r_c  → ⋁(P_adj)              (one big disjunction)
        """
        adjs = self._adjacent(r, c)

        # Cell is safe (agent alive here)
        self.kb.tell([f"!P_{r}_{c}"])
        self.kb.tell([f"!W_{r}_{c}"])

        if not percepts["breeze"]:
            for ar, ac in adjs:
                self.kb.tell([f"!P_{ar}_{ac}"])
            self._add_log(f"No breeze @({r},{c}) → ¬Pit for all adjacent cells", "infer")
        else:
            pit_lits = [f"P_{ar}_{ac}" for ar, ac in adjs]
            self.kb.tell(pit_lits)
            self._add_log(f"Breeze @({r},{c}) → {' ∨ '.join(pit_lits)}", "infer")

        if not percepts["stench"]:
            for ar, ac in adjs:
                self.kb.tell([f"!W_{ar}_{ac}"])
            self._add_log(f"No stench @({r},{c}) → ¬Wumpus for all adjacent cells", "infer")
        else:
            w_lits = [f"W_{ar}_{ac}" for ar, ac in adjs]
            self.kb.tell(w_lits)
            self._add_log(f"Stench @({r},{c}) → {' ∨ '.join(w_lits)}", "infer")

        if percepts["glitter"]:
            self._add_log(f"★ GLITTER at ({r},{c}) — GOLD FOUND! You win!", "win")
            self.game_over = True
            self.won = True

        return percepts

    def _run_inference(self):
        """
        ASK the KB about every frontier cell (unvisited cell adjacent to any visited cell).
        Uses Resolution Refutation to prove ¬P and ¬W for safety.
        """
        frontier = set()
        for r, c in self.visited:
            for ar, ac in self._adjacent(r, c):
                if (ar, ac) not in self.visited:
                    frontier.add((ar, ac))

        for r, c in frontier:
            safe_from_pit = self.kb.ask(f"!P_{r}_{c}")
            safe_from_wumpus = self.kb.ask(f"!W_{r}_{c}")
            if safe_from_pit and safe_from_wumpus:
                if (r, c) not in self.safe_proven:
                    self.safe_proven.add((r, c))
                    self._add_log(f"✓ Resolution proves ({r},{c}) is SAFE", "infer")

            if self.kb.ask(f"P_{r}_{c}") and (r, c) not in self.inferred_pits:
                self.inferred_pits.add((r, c))
                self._add_log(f"⚠ Resolution infers PIT at ({r},{c})", "warn")

            if self.inferred_wumpus is None and self.kb.ask(f"W_{r}_{c}"):
                self.inferred_wumpus = (r, c)
                self._add_log(f"⚠ Resolution infers WUMPUS at ({r},{c})", "warn")

    def move(self, r: int, c: int) -> dict:
        """Move agent to (r,c). Returns updated state dict."""
        if self.game_over:
            return self.to_dict()

        self._add_log(f"→ Move to ({r},{c})", "move")

        # Check hazards
        if (r, c) in self.pit_set:
            self._add_log(f"Agent fell into a PIT at ({r},{c})! Game Over.", "dead")
            self.inferred_pits.add((r, c))
            self.game_over = True
            self.won = False
            self.agent_r, self.agent_c = r, c
            return self.to_dict()

        if self.wumpus and (r, c) == self.wumpus:
            self._add_log(f"Agent eaten by the WUMPUS at ({r},{c})! Game Over.", "dead")
            self.inferred_wumpus = (r, c)
            self.game_over = True
            self.won = False
            self.agent_r, self.agent_c = r, c
            return self.to_dict()

        self.agent_r, self.agent_c = r, c
        self.visited.add((r, c))
        self.safe_proven.add((r, c))

        percepts = self._get_percepts(r, c)
        self._tell_percepts(r, c, percepts)
        if not self.game_over:
            self._run_inference()

        return self.to_dict()

    def agent_step(self) -> dict:
        """
        Autonomous agent decision: BFS to nearest proven-safe unvisited cell.
        Falls back to a risky frontier move if no safe path exists.
        """
        if self.game_over:
            return self.to_dict()

        # BFS through visited+safe cells to find nearest unvisited safe cell
        from collections import deque
        queue = deque([(self.agent_r, self.agent_c, [])])
        seen = {(self.agent_r, self.agent_c)}
        target_path = None

        while queue:
            r, c, path = queue.popleft()
            for ar, ac in self._adjacent(r, c):
                if (ar, ac) in seen:
                    continue
                npath = path + [(ar, ac)]
                if (ar, ac) in self.safe_proven and (ar, ac) not in self.visited:
                    target_path = npath
                    break
                if (ar, ac) in self.safe_proven or (ar, ac) in self.visited:
                    seen.add((ar, ac))
                    queue.append((ar, ac, npath))
            if target_path:
                break

        if target_path:
            next_r, next_c = target_path[0]
            return self.move(next_r, next_c)

        # No safe path — take a risk on unvisited adjacent cell
        adjs = self._adjacent(self.agent_r, self.agent_c)
        risky = [(ar, ac) for ar, ac in adjs
                 if (ar, ac) not in self.visited
                 and (ar, ac) not in self.inferred_pits
                 and (ar, ac) != self.inferred_wumpus]

        if risky:
            self._add_log("⚠ No proven-safe path. Taking a calculated risk…", "warn")
            nr, nc = random.choice(risky)
            return self.move(nr, nc)

        self._add_log("Agent is completely stuck — no moves available.", "warn")
        return self.to_dict()

    def _add_log(self, msg: str, kind: str = "info"):
        self.log.append({"msg": msg, "kind": kind})

    def to_dict(self) -> dict:
        """Serialize full game state to JSON-safe dict."""
        # Reveal ground truth when game is over
        reveal_pits = [list(p) for p in self.pit_set] if self.game_over else []
        reveal_wumpus = list(self.wumpus) if self.game_over and self.wumpus else None
        reveal_gold = list(self.gold) if self.gold else None

        return {
            "rows": self.rows,
            "cols": self.cols,
            "agent": [self.agent_r, self.agent_c],
            "visited": [list(c) for c in self.visited],
            "safe_proven": [list(c) for c in self.safe_proven],
            "inferred_pits": [list(c) for c in self.inferred_pits],
            "inferred_wumpus": list(self.inferred_wumpus) if self.inferred_wumpus else None,
            "game_over": self.game_over,
            "won": self.won,
            "reveal_pits": reveal_pits,
            "reveal_wumpus": reveal_wumpus,
            "reveal_gold": reveal_gold,
            "metrics": {
                "infer_steps": self.kb.infer_steps,
                "kb_clauses": self.kb.clause_count(),
                "visited": len(self.visited),
                "safe_proven": len(self.safe_proven),
            },
            "percepts": self._get_percepts(self.agent_r, self.agent_c) if not self.game_over else {},
            "kb_clauses": self.kb.clauses_as_strings()[-30:],  # last 30 for display
            "log": self.log[-50:],  # last 50 entries
        }


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STORE  (in-memory; swap for Redis/DB in production)
# ─────────────────────────────────────────────────────────────────────────────

_games: dict[str, WumpusGame] = {}


def get_game(sid: str) -> WumpusGame | None:
    return _games.get(sid)


# ─────────────────────────────────────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/new_game", methods=["POST"])
def new_game():
    data = request.get_json(force=True)
    rows = max(3, min(8, int(data.get("rows", 4))))
    cols = max(3, min(8, int(data.get("cols", 4))))
    pits = max(1, min(10, int(data.get("pits", 3))))

    sid = str(uuid.uuid4())
    session["sid"] = sid
    game = WumpusGame(rows=rows, cols=cols, num_pits=pits)
    _games[sid] = game

    return jsonify({"sid": sid, "state": game.to_dict()})


@app.route("/api/move", methods=["POST"])
def move():
    data = request.get_json(force=True)
    sid = data.get("sid") or session.get("sid")
    game = get_game(sid)
    if not game:
        return jsonify({"error": "No active game"}), 400

    r = int(data["r"])
    c = int(data["c"])
    state = game.move(r, c)
    return jsonify({"state": state})


@app.route("/api/step", methods=["POST"])
def step():
    data = request.get_json(force=True)
    sid = data.get("sid") or session.get("sid")
    game = get_game(sid)
    if not game:
        return jsonify({"error": "No active game"}), 400

    state = game.agent_step()
    return jsonify({"state": state})


@app.route("/api/state", methods=["GET"])
def state():
    sid = request.args.get("sid") or session.get("sid")
    game = get_game(sid)
    if not game:
        return jsonify({"error": "No active game"}), 400
    return jsonify({"state": game.to_dict()})


# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True, port=5000)