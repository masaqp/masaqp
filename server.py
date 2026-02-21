from flask import Flask, request
from flask_socketio import SocketIO, send
import eventlet

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

players = {}

def check_start():
    if len(players) != 2:
        return False
    for player in players.values():
        print(player)
        if not player["status"]:
            return False
    return True


@socketio.on("connect")
def handle_connect(auth):
    print(f"✅ Клієнт {request.sid} доєднався!")

    username = auth.get("name") if auth else "Unknown"

    players[request.sid] = {
        "name": username,
        "status": False
    }

    send(f"🔵 {username} приєднався до гри", broadcast=True)


@socketio.on("disconnect")
def handle_disconnect():
    if request.sid in players:
        name = players[request.sid]["name"]
        del players[request.sid]
        send(f"❌ {name} покинув гру", broadcast=True)

    print(f"❌ Клієнт {request.sid} відключився")


@socketio.on("message")
def handle_message(msg):
    print(f"📩 {request.sid}: {msg}")

    if request.sid not in players:
        return

    # READY
    if msg == "/ready":
        players[request.sid]["status"] = True
        name = players[request.sid]["name"]

        send(f"🟢 {name} готовий!", broadcast=True)

        if check_start():
            send("🎮 ГРА ПОЧИНАЄТЬСЯ!", broadcast=True)
            socketio.emit("game_start")
        return

    # звичайний чат
    send(msg, broadcast=True)


if __name__ == "__main__":
    print("🚀 Сервер запущено")
    socketio.run(app, host="0.0.0.0", port=5000)
