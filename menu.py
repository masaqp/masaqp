import customtkinter as ctk
from tkinter import messagebox
import socketio
import threading

# ---------- SOCKET ----------
sio = socketio.Client()

# ---------- НАЛАШТУВАННЯ UI ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

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
        sio.connect("http://127.0.0.1:5000",auth={"name":nickname})
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
app.geometry("500x400")
app.protocol("WM_DELETE_WINDOW", close_app)

# ---------- START FRAME ----------
start_frame = ctk.CTkFrame(app, corner_radius=20)
start_frame.pack(pady=40, padx=40, fill="both", expand=True)

ctk.CTkLabel(
    start_frame,
    text="Вхід у гру",
    font=ctk.CTkFont(size=24, weight="bold")
).pack(pady=20)

name_entry = ctk.CTkEntry(
    start_frame,
    placeholder_text="Ваш нікнейм",
    width=220
)
name_entry.pack(pady=10)

ctk.CTkButton(
    start_frame,
    text="ПІДКЛЮЧИТИСЬ",
    width=200,
    height=40,
    command=connect_to_server
).pack(pady=20)

# ---------- CHAT FRAME ----------
chat_frame = ctk.CTkFrame(app, corner_radius=15)

chat_box = ctk.CTkTextbox(chat_frame, state="disabled")
chat_box.pack(padx=10, pady=10, fill="both", expand=True)

bottom_frame = ctk.CTkFrame(chat_frame)
bottom_frame.pack(fill="x", padx=10, pady=10)

message_entry = ctk.CTkEntry(
    bottom_frame,
    placeholder_text="Введіть повідомлення"
)
message_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

ctk.CTkButton(
    bottom_frame,
    text="SEND",
    width=80,
    command=send_message
).pack(side="right")

# ---------- ЗАПУСК ----------
app.mainloop()

