import customtkinter as ctk
from tkinter import messagebox
import socketio
import threading

# ---------- SOCKET ----------
sio = socketio.Client()

# ---------- НАЛАШТУВАННЯ UI ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")  # темніша тема

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

def add_message(text):
    chat_box.configure(state="normal")
    chat_box.insert("end", text + "\n")
    chat_box.configure(state="disabled")
    chat_box.see("end")

def close_app():
    if sio.connected:
        sio.disconnect()
    app.destroy()

# ---------- ВІКНО ----------
app = ctk.CTk()
app.title("Game Client")
app.geometry("550x450")
app.protocol("WM_DELETE_WINDOW", close_app)

# ---------- START FRAME ----------
start_frame = ctk.CTkFrame(app, corner_radius=20, fg_color="#1e1e2f")  # красивий темний фон
start_frame.pack(pady=50, padx=50, fill="both", expand=True)

ctk.CTkLabel(
    start_frame,
    text="🎮 Вхід у гру",
    font=ctk.CTkFont(size=28, weight="bold"),
    text_color="#00bfff"  # блакитний колір заголовка
).pack(pady=20)

name_entry = ctk.CTkEntry(
    start_frame,
    placeholder_text="Ваш нікнейм",
    width=250,
    height=35,
    font=ctk.CTkFont(size=16)
)
name_entry.pack(pady=15)

ctk.CTkButton(
    start_frame,
    text="ПІДКЛЮЧИТИСЬ",
    width=220,
    height=45,
    fg_color="#00bfff",
    hover_color="#3399ff",
    font=ctk.CTkFont(size=16, weight="bold"),
    corner_radius=15,
    command=connect_to_server
).pack(pady=25)

# ---------- CHAT FRAME ----------
chat_frame = ctk.CTkFrame(app, corner_radius=15, fg_color="#1e1e2f")

chat_box = ctk.CTkTextbox(chat_frame, state="disabled", font=ctk.CTkFont(size=14))
chat_box.pack(padx=10, pady=10, fill="both", expand=True)

bottom_frame = ctk.CTkFrame(chat_frame, fg_color="#2e2e3e")
bottom_frame.pack(fill="x", padx=10, pady=10, ipady=5)

message_entry = ctk.CTkEntry(
    bottom_frame,
    placeholder_text="Введіть повідомлення",
    font=ctk.CTkFont(size=14)
)
message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=5)

ctk.CTkButton(
    bottom_frame,
    text="SEND",
    width=90,
    fg_color="#00bfff",
    hover_color="#3399ff",
    font=ctk.CTkFont(size=14, weight="bold"),
    corner_radius=12,
    command=send_message
).pack(side="right", ipady=5)

# ---------- ЗАПУСК ----------
app.mainloop()
