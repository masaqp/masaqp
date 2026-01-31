from flask import Flask, request
from flask_socketio import SocketIO, send

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

players={}

@socketio.on("connect")
def handle_connect(auth):
    print(f"✅ Клієнт {request.sid} доєднався!")

    usernema=auth.get("name") 

    players[request.sid] = {
        "name":usernema,
        "status":False
    }

    if (len(players)==2):

        socketio.send ("гра почалась") 
        socketio.send(str(players))
    else:
        socketio.send(str(players))

@socketio.on("disconnect")
def handle_disconnect():
    print(f"❌ Клієнт {request.sid} відключився")


@socketio.on("message")
def handle_message(msg):
    print(f"📩 Отримано нове повідомлення від {request.sid}: {msg}")
    if "Готовність" not in msg:
        send(msg, broadcast=True)  # відправка всім клієнтам
    else:
        # Отримання статусу від гравця
        pass


print("🚀 Сервер почав роботу")
socketio.run(app, host="0.0.0.0", port=5000)