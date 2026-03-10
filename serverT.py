from flask import Flask, request
from flask_socketio import SocketIO, send, emit
import eventlet

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

SIZE = 10
players = {}   # sid -> {name, board, ships_alive, ready}
turn_sid = None   # whose turn it is


# ──────────────────────────────────────────────
#  Helpers
# ──────────────────────────────────────────────

def other_sid(sid):
    """Return the SID of the opponent, or None."""
    sids = list(players.keys())
    if len(sids) != 2:
        return None
    return sids[1] if sids[0] == sid else sids[0]


def parse_board(cell_list):
    """
    cell_list: [[r, c], ...] — coordinates of every ship cell.
    Returns a 10×10 grid of "~" or "S".
    """
    board = [["~"] * SIZE for _ in range(SIZE)]
    for r, c in cell_list:
        board[r][c] = "S"
    return board


def ships_remaining(board):
    """Count living ship cells."""
    return sum(board[r][c] == "S" for r in range(SIZE) for c in range(SIZE))


def check_all_ready():
    if len(players) != 2:
        return False
    return all(p["ready"] for p in players.values())


# ──────────────────────────────────────────────
#  Connection events
# ──────────────────────────────────────────────

@socketio.on("connect")
def handle_connect(auth):
    sid = request.sid
    username = (auth or {}).get("name", "Unknown")

    if len(players) >= 2:
        emit("message", "❌ Гра вже повна. Спробуйте пізніше.")
        return False  # refuse connection

    players[sid] = {
        "name": username,
        "board": None,
        "ships_alive": 0,
        "ready": False,
    }
    print(f"✅ {username} ({sid}) підключився. Гравців: {len(players)}")
    send(f"🔵 {username} приєднався до гри", broadcast=True)

    if len(players) == 2:
        send("⚔️ Обидва гравці підключені! Розставляйте кораблі.", broadcast=True)
        socketio.emit("place_ships")  # tell everyone to show placement screen


@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    if sid not in players:
        return
    name = players.pop(sid)["name"]
    send(f"❌ {name} покинув гру", broadcast=True)
    print(f"❌ {name} ({sid}) відключився")

    # Notify remaining player
    opp = other_sid(sid)
    if opp:
        socketio.emit("message", "😢 Суперник відключився. Гра завершена.", to=opp)


@socketio.on("message")
def handle_message(msg):
    sid = request.sid
    if sid not in players:
        return
    send(msg, broadcast=True)


# ──────────────────────────────────────────────
#  Placement
# ──────────────────────────────────────────────

@socketio.on("player_ready")
def handle_player_ready(data):
    global turn_sid
    sid = request.sid
    if sid not in players:
        return

    board = parse_board(data.get("board", []))
    players[sid]["board"] = board
    players[sid]["ships_alive"] = ships_remaining(board)
    players[sid]["ready"] = True

    name = players[sid]["name"]
    print(f"🟢 {name} готовий! Кораблів: {players[sid]['ships_alive']}")
    send(f"🟢 {name} розставив кораблі та готовий!", broadcast=True)

    if check_all_ready():
        sids = list(players.keys())
        turn_sid = sids[0]   # first connected player goes first

        print(f"🎮 Гра починається! Перший хід: {players[turn_sid]['name']}")
        send("🎮 ГРА ПОЧИНАЄТЬСЯ!", broadcast=True)

        for s in sids:
            first = (s == turn_sid)
            socketio.emit("game_start", {"first_turn": first}, to=s)


# ──────────────────────────────────────────────
#  Shooting
# ──────────────────────────────────────────────

@socketio.on("shoot")
def handle_shoot(data):
    global turn_sid
    sid = request.sid

    if sid not in players:
        return
    if sid != turn_sid:
        emit("message", "⛔ Зараз не ваш хід!")
        return

    opp_sid = other_sid(sid)
    if not opp_sid or players[opp_sid]["board"] is None:
        return

    r, c = data["r"], data["c"]
    opp_board = players[opp_sid]["board"]
    cell = opp_board[r][c]

    if cell in ("X", "O"):
        emit("message", "⛔ Ця клітина вже обстріляна!")
        return

    if cell == "S":
        opp_board[r][c] = "X"
        players[opp_sid]["ships_alive"] -= 1
        alive = players[opp_sid]["ships_alive"]

        # Notify enemy: they were hit
        socketio.emit("enemy_shot", {"r": r, "c": c, "hit": True}, to=opp_sid)

        if alive == 0:
            emit("shot_result", {"r": r, "c": c, "result": "win"})
            socketio.emit("game_over", {"winner": players[sid]["name"]}, broadcast=True)
            send(f"🏆 {players[sid]['name']} переміг!", broadcast=True)
            print(f"🏆 {players[sid]['name']} переміг!")
        else:
            result = "sink" if _is_sunk(opp_board, r, c) else "hit"
            emit("shot_result", {"r": r, "c": c, "result": result})
            # Hit/sink → shooter goes again (turn_sid unchanged)

    else:
        # Miss
        opp_board[r][c] = "O"
        socketio.emit("enemy_shot", {"r": r, "c": c, "hit": False}, to=opp_sid)
        emit("shot_result", {"r": r, "c": c, "result": "miss"})
        turn_sid = opp_sid   # switch turn


def _is_sunk(board, r, c):
    """
    BFS/flood-fill from (r,c) — the cell just hit (now "X").
    A ship is sunk if all connected ship cells (4-directional) are "X" (none remain "S").
    """
    visited = set()
    stack = [(r, c)]
    while stack:
        rr, cc = stack.pop()
        if (rr, cc) in visited:
            continue
        visited.add((rr, cc))
        if board[rr][cc] not in ("X",):
            continue
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = rr+dr, cc+dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE and (nr, nc) not in visited:
                if board[nr][nc] in ("X", "S"):
                    stack.append((nr, nc))
    # If any connected cell is still "S", ship not sunk
    for rr, cc in visited:
        if board[rr][cc] == "S":
            return False
    return True


# ──────────────────────────────────────────────
#  Run
# ──────────────────────────────────────────────
if __name__ == "__main__":
    print("🚀 Сервер запущено на порту 5000")
    socketio.run(app, host="0.0.0.0", port=5000)