import customtkinter as ctk
from tkinter import messagebox
import socketio
import subprocess
import sys

# ---------- SOCKET ----------
sio = socketio.Client()
nickname = ""

# ---------- SOCKET EVENTS ----------
@sio.event
def connect():
    add_message("✅ Підключено до сервера")

@sio.event
def disconnect():
    add_message("❌ Відключено від сервера")

@sio.on("message")
def on_message(data):
    add_message(data)

@sio.on("game_start")
def on_game_start():
    print('Клієнт-стар')
    # start_main_game()

# ---------- ФУНКЦІЇ ----------
def connect_to_server():
    global nickname
    nickname = name_entry.get().strip()

    if nickname == "":
        messagebox.showwarning("Помилка", "Введіть нікнейм!")
        return

    try:
        sio.connect("http://127.0.0.1:5000", auth={"name": nickname})
        start_frame.pack_forget()
        chat_frame.pack(fill="both", expand=True)
    except Exception as e:
        messagebox.showerror("Помилка", f"Не вдалося підключитись\n{e}")

def send_message():
    msg = message_entry.get().strip()
    if msg:
        sio.send(f"{nickname}: {msg}")
        message_entry.delete(0, "end")

def status_active():
    sio.send("/ready")

def add_message(text):
    chat_box.configure(state="normal")
    chat_box.insert("end", text + "\n")
    chat_box.configure(state="disabled")
    chat_box.see("end")

def start_main_game():
    if sio.connected:
        sio.disconnect()

    app.destroy()

    # запуск розстановки кораблів
    

def close_app():
    if sio.connected:
        sio.disconnect()
    app.destroy()

# ---------- UI ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Game Client")
app.geometry("550x450")
app.protocol("WM_DELETE_WINDOW", close_app)

# ---------- START FRAME ----------
start_frame = ctk.CTkFrame(app)
start_frame.pack(pady=50, padx=50, fill="both", expand=True)

ctk.CTkLabel(
    start_frame,
    text="🎮 Вхід у гру",
    font=ctk.CTkFont(size=28, weight="bold")
).pack(pady=20)

name_entry = ctk.CTkEntry(start_frame, placeholder_text="Ваш нікнейм")
name_entry.pack(pady=15)

ctk.CTkButton(
    start_frame,
    text="ПІДКЛЮЧИТИСЬ",
    command=connect_to_server
).pack(pady=25)

# ---------- CHAT FRAME ----------
chat_frame = ctk.CTkFrame(app)

chat_box = ctk.CTkTextbox(chat_frame, state="disabled")
chat_box.pack(padx=10, pady=10, fill="both", expand=True)

bottom_frame = ctk.CTkFrame(chat_frame)
bottom_frame.pack(fill="x", padx=10, pady=10)

message_entry = ctk.CTkEntry(bottom_frame)
message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

ctk.CTkButton(bottom_frame, text="SEND", command=send_message).pack(side="right")
ctk.CTkButton(bottom_frame, text="Готово", command=status_active).pack(side="right", padx=5)

app.mainloop()
