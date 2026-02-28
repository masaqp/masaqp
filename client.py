import customtkinter as ctk
from tkinter import messagebox
import socketio
import random

# ---------- SOCKET ----------
sio = socketio.Client()
nickname = ""

# ---------- GAME SETTINGS ----------
SIZE = 10
SHIPS_CONFIG = {4: 1, 3: 2, 2: 3, 1: 4}

# ---------- SEA BATTLE CLASS ----------
class SeaBattle:
    def __init__(self, parent):
        self.parent = parent

        # Поля для гравця та "супротивника"
        self.board_player = [["~"] * SIZE for _ in range(SIZE)]
        self.board_enemy = [["~"] * SIZE for _ in range(SIZE)]

        self.phase = "placing"
        self.reset_ships()
        self.placing_orientation = "H"
        self.hover_r = -1
        self.hover_c = -1
        self.preview_coords = []

        # Інформаційна панель
        self.info = ctk.CTkLabel(
            parent,
            text=f"Розставте корабель {self.ships_to_place[0]} (H/→ - горизонтально, V/↑ - вертикально)",
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=580,
            justify="center"
        )
        self.info.pack(pady=10)

        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(pady=10)

        self.result = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=14))
        self.result.pack(pady=5)

        self.cells = [[None] * SIZE for _ in range(SIZE)]
        self.draw_board()

        # Прив'язка клавіш для орієнтації кораблів
        parent.bind_all("<w>", lambda e: self.change_orientation("V"))
        parent.bind_all("<s>", lambda e: self.change_orientation("V"))
        parent.bind_all("<Up>", lambda e: self.change_orientation("V"))
        parent.bind_all("<Down>", lambda e: self.change_orientation("V"))
        parent.bind_all("<a>", lambda e: self.change_orientation("H"))
        parent.bind_all("<d>", lambda e: self.change_orientation("H"))
        parent.bind_all("<Left>", lambda e: self.change_orientation("H"))
        parent.bind_all("<Right>", lambda e: self.change_orientation("H"))

    def reset_ships(self):
        self.ships_to_place = []
        for length, count in SHIPS_CONFIG.items():
            self.ships_to_place += [length] * count

    def change_orientation(self, orient):
        self.placing_orientation = orient
        if self.phase == "placing" and self.ships_to_place:
            self.info.configure(
                text=f"Розставте корабель {self.ships_to_place[0]} ({self.placing_orientation})"
            )
        if self.hover_r != -1 and self.hover_c != -1:
            self.update_preview(self.hover_r, self.hover_c)

    def draw_board(self):
        board = self.board_player if self.phase == "placing" else self.board_enemy

        for r in range(SIZE):
            for c in range(SIZE):
                cell = board[r][c]
                color = "#2f2f2f"
                text = ""

                if self.phase == "placing" and cell == "S":
                    color = "#00bfff"
                elif self.phase == "game":
                    if cell == "X":
                        color = "red"
                        text = "X"
                    elif cell == "O":
                        color = "gray"
                        text = "O"

                btn = ctk.CTkButton(
                    self.frame,
                    text=text,
                    width=40,
                    height=40,
                    fg_color=color,
                    command=lambda r=r, c=c: self.cell_click(r, c)
                )
                btn.grid(row=r, column=c, padx=2, pady=2)
                self.cells[r][c] = btn

                if self.phase == "placing":
                    btn.bind("<Enter>", lambda e, r=r, c=c: self.update_preview(r, c))
                    btn.bind("<Leave>", lambda e: self.clear_preview())

    def update_preview(self, r, c):
        self.clear_preview()
        self.hover_r = r
        self.hover_c = c

        if not self.ships_to_place:
            return

        length = self.ships_to_place[0]
        board = self.board_player
        coords = []
        valid = True
        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            if rr >= SIZE or cc >= SIZE or board[rr][cc] == "S":
                valid = False
                break
            coords.append((rr, cc))

        color = "#3399ff" if valid else "#ff4d4d"
        for rr, cc in coords:
            self.cells[rr][cc].configure(fg_color=color)
            self.preview_coords.append((rr, cc))

    def clear_preview(self):
        for rr, cc in self.preview_coords:
            if self.board_player[rr][cc] != "S":
                self.cells[rr][cc].configure(fg_color="#2f2f2f")
        self.preview_coords.clear()

    def can_place_ship(self, r, c, length):
        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            if rr >= SIZE or cc >= SIZE or self.board_player[rr][cc] == "S":
                return False
        return True

    def cell_click(self, r, c):
        if self.phase == "placing":
            self.place_ship(r, c)
        else:
            self.shoot(r, c)

    def place_ship(self, r, c):
        if not self.ships_to_place:
            return

        length = self.ships_to_place[0]
        if not self.can_place_ship(r, c, length):
            messagebox.showwarning("Помилка", "Неможливо розмістити корабель тут!")
            return

        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            self.board_player[rr][cc] = "S"

        self.ships_to_place.pop(0)
        self.clear_preview()
        self.hover_r = -1
        self.hover_c = -1

        if not self.ships_to_place:
            self.phase = "game"
            self.info.configure(text="Гра почалася! Стріляйте по полі супротивника")
            self.board_enemy = [["~"] * SIZE for _ in range(SIZE)]
        else:
            self.info.configure(
                text=f"Розставте корабель {self.ships_to_place[0]} ({self.placing_orientation})"
            )

        self.draw_board()

    def shoot(self, r, c):
        cell = self.board_enemy[r][c]
        if cell in ("X", "O"):
            return

        # випадкова логіка для тренування
        if random.random() < 0.3:  # 30% шанс попадання
            self.board_enemy[r][c] = "X"
            self.result.configure(text="🔥 ПОПАВ!")
        else:
            self.board_enemy[r][c] = "O"
            self.result.configure(text="❌ ПРОМАХ!")

        self.draw_board()


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
    add_message("🎮 Гра починається! Розставте свої кораблі.")
    chat_frame.pack_forget()  # Сховати чат
    start_ship_placement()     # Почати розстановку кораблів


# ---------- FUNCTIONS ----------
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


def start_ship_placement():
    global game
    ship_frame = ctk.CTkFrame(app)
    ship_frame.pack(fill="both", expand=True, pady=10, padx=10)
    game = SeaBattle(ship_frame)


def close_app():
    if sio.connected:
        sio.disconnect()
    app.destroy()


# ---------- UI SETUP ----------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Game Client")
app.geometry("600x700")
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