import customtkinter as ctk
from tkinter import messagebox
import socketio
import threading

# ---------- SOCKET ----------
sio = socketio.Client()
nickname = ""
game = None

# ---------- GAME SETTINGS ----------
SIZE = 10
# Ordered largest-first so ships_to_place is [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
SHIPS_CONFIG = [(4, 1), (3, 2), (2, 3), (1, 4)]


# ---------- SEA BATTLE CLASS ----------
class SeaBattle:
    def __init__(self, parent):
        self.parent = parent
        self.my_turn = False

        # Internal boards
        self.board_player = [["~"] * SIZE for _ in range(SIZE)]   # my ships
        self.board_enemy  = [["~"] * SIZE for _ in range(SIZE)]   # shots on enemy

        self.phase = "placing"   # placing → waiting → game → over
        self.reset_ships()
        self.placing_orientation = "H"
        self.hover_r = -1
        self.hover_c = -1
        self.preview_coords = []

        # ---- Info label ----
        self.info = ctk.CTkLabel(
            parent,
            text=self._placing_hint(),
            font=ctk.CTkFont(size=14, weight="bold"),
            wraplength=580,
            justify="center",
        )
        self.info.pack(pady=(10, 4))

        # ---- Rotate button ----
        self.rotate_btn = ctk.CTkButton(
            parent,
            text="🔄 Повернути (R)",
            width=160,
            command=self.toggle_orientation,
        )
        self.rotate_btn.pack(pady=(0, 6))

        # ---- Grid frame ----
        self.frame = ctk.CTkFrame(parent)
        self.frame.pack(pady=6)

        # ---- Ready button (hidden until all ships placed) ----
        self.ready_btn = ctk.CTkButton(
            parent,
            text="✅ Готово — надіслати кораблі",
            width=220,
            fg_color="#1a7a1a",
            hover_color="#145214",
            command=self.send_ready,
        )
        # packed later when all ships are placed

        # ---- Result label ----
        self.result = ctk.CTkLabel(parent, text="", font=ctk.CTkFont(size=14))
        self.result.pack(pady=5)

        self.cells_player = [[None] * SIZE for _ in range(SIZE)]
        self.cells_enemy  = [[None] * SIZE for _ in range(SIZE)]

        self._build_grids()

        # ---- Key bindings (bound on root CTk window to avoid customtkinter restriction) ----
        app.bind("<r>", lambda e: self.toggle_orientation())
        app.bind("<R>", lambda e: self.toggle_orientation())
        app.bind("<Up>",    lambda e: self.set_orientation("V"))
        app.bind("<Down>",  lambda e: self.set_orientation("V"))
        app.bind("<Left>",  lambda e: self.set_orientation("H"))
        app.bind("<Right>", lambda e: self.set_orientation("H"))
        app.bind("<w>", lambda e: self.set_orientation("V"))
        app.bind("<s>", lambda e: self.set_orientation("V"))
        app.bind("<a>", lambda e: self.set_orientation("H"))
        app.bind("<d>", lambda e: self.set_orientation("H"))

    # ------------------------------------------------------------------ helpers
    def _placing_hint(self):
        if not self.ships_to_place:
            return "Всі кораблі розставлено! Натисніть «Готово»"
        return (f"Розставте корабель [{self.ships_to_place[0]}] | "
                f"орієнтація: {'→ Горизонтально' if self.placing_orientation == 'H' else '↑ Вертикально'}")

    def reset_ships(self):
        self.ships_to_place = []
        for length, count in SHIPS_CONFIG:
            self.ships_to_place += [length] * count

    # ------------------------------------------------------------------ orientation
    def toggle_orientation(self):
        new = "V" if self.placing_orientation == "H" else "H"
        self.set_orientation(new)

    def set_orientation(self, orient):
        if self.phase != "placing":
            return
        self.placing_orientation = orient
        self.rotate_btn.configure(
            text=f"🔄 {'Горизонтально →' if orient == 'H' else 'Вертикально ↑'}  (R)"
        )
        self.info.configure(text=self._placing_hint())
        if self.hover_r != -1:
            self.update_preview(self.hover_r, self.hover_c)

    # ------------------------------------------------------------------ board building
    def _build_grids(self):
        """Build two side-by-side grids: my board (left) + enemy board (right, locked)."""
        container = ctk.CTkFrame(self.parent, fg_color="transparent")
        container.pack()

        # --- MY board ---
        left = ctk.CTkFrame(container, fg_color="transparent")
        left.pack(side="left", padx=16)
        ctk.CTkLabel(left, text="Мої кораблі", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 4))
        grid_l = ctk.CTkFrame(left)
        grid_l.pack()

        for r in range(SIZE):
            for c in range(SIZE):
                btn = ctk.CTkButton(
                    grid_l, text="", width=36, height=36,
                    fg_color="#2f2f2f", hover_color="#444",
                    command=lambda r=r, c=c: self.cell_click_player(r, c),
                )
                btn.grid(row=r, column=c, padx=1, pady=1)
                self.cells_player[r][c] = btn
                btn.bind("<Enter>", lambda e, r=r, c=c: self.update_preview(r, c))
                btn.bind("<Leave>", lambda e: self.clear_preview())

        # --- ENEMY board ---
        right = ctk.CTkFrame(container, fg_color="transparent")
        right.pack(side="left", padx=16)
        ctk.CTkLabel(right, text="Поле ворога", font=ctk.CTkFont(size=12, weight="bold")).pack(pady=(0, 4))
        grid_r = ctk.CTkFrame(right)
        grid_r.pack()

        for r in range(SIZE):
            for c in range(SIZE):
                btn = ctk.CTkButton(
                    grid_r, text="", width=36, height=36,
                    fg_color="#1a1a2e", hover_color="#16213e",
                    command=lambda r=r, c=c: self.cell_click_enemy(r, c),
                )
                btn.grid(row=r, column=c, padx=1, pady=1)
                self.cells_enemy[r][c] = btn

    # ------------------------------------------------------------------ preview
    def update_preview(self, r, c):
        if self.phase != "placing" or not self.ships_to_place:
            return
        self.clear_preview()
        self.hover_r, self.hover_c = r, c
        length = self.ships_to_place[0]
        coords, valid = [], True
        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            if rr >= SIZE or cc >= SIZE or self.board_player[rr][cc] == "S":
                valid = False
                break
            coords.append((rr, cc))
        color = "#3399ff" if valid else "#ff4d4d"
        for rr, cc in coords:
            self.cells_player[rr][cc].configure(fg_color=color)
            self.preview_coords.append((rr, cc))

    def clear_preview(self):
        for rr, cc in self.preview_coords:
            self.cells_player[rr][cc].configure(
                fg_color="#00bfff" if self.board_player[rr][cc] == "S" else "#2f2f2f"
            )
        self.preview_coords.clear()

    # ------------------------------------------------------------------ placing
    def cell_click_player(self, r, c):
        if self.phase == "placing":
            self.place_ship(r, c)

    def place_ship(self, r, c):
        if not self.ships_to_place:
            return
        length = self.ships_to_place[0]
        # validate
        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            if rr >= SIZE or cc >= SIZE or self.board_player[rr][cc] == "S":
                messagebox.showwarning("Помилка", "Неможливо розмістити корабель тут!")
                return
        # place
        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            self.board_player[rr][cc] = "S"
            self.cells_player[rr][cc].configure(fg_color="#00bfff")

        self.ships_to_place.pop(0)
        self.clear_preview()
        self.hover_r = self.hover_c = -1

        if not self.ships_to_place:
            self.info.configure(text="Всі кораблі розставлено! Натисніть «Готово»")
            self.rotate_btn.pack_forget()
            self.ready_btn.pack(pady=8)
        else:
            self.info.configure(text=self._placing_hint())

    # ------------------------------------------------------------------ ready
    def send_ready(self):
        """Send board to server and wait for game_start."""
        # Serialize board: list of (r,c) ship cells
        ship_cells = [
            [r, c]
            for r in range(SIZE)
            for c in range(SIZE)
            if self.board_player[r][c] == "S"
        ]
        sio.emit("player_ready", {"board": ship_cells})
        self.ready_btn.configure(state="disabled", text="⏳ Очікуємо суперника…")
        self.info.configure(text="Чекаємо на другого гравця…")
        self.phase = "waiting"

    # ------------------------------------------------------------------ shooting
    def cell_click_enemy(self, r, c):
        if self.phase != "game" or not self.my_turn:
            return
        if self.board_enemy[r][c] != "~":
            return
        # Mark locally as pending and send
        self.my_turn = False
        self.result.configure(text="⏳ Очікуємо відповідь…")
        sio.emit("shoot", {"r": r, "c": c})

    def apply_shot_result(self, r, c, result):
        """Called from socket thread — schedule UI update on main thread."""
        self.parent.after(0, lambda: self._apply_shot_result_ui(r, c, result))

    def _apply_shot_result_ui(self, r, c, result):
        if result == "hit":
            self.board_enemy[r][c] = "X"
            self.cells_enemy[r][c].configure(fg_color="#cc2200", text="💥")
            self.result.configure(text="🔥 ПОПАВ! Ваш хід знову.")
            self.my_turn = True
        elif result == "miss":
            self.board_enemy[r][c] = "O"
            self.cells_enemy[r][c].configure(fg_color="#555", text="•")
            self.result.configure(text="❌ ПРОМАХ! Хід суперника.")
        elif result == "sink":
            self.board_enemy[r][c] = "X"
            self.cells_enemy[r][c].configure(fg_color="#ff6600", text="🔥")
            self.result.configure(text="💣 ПОТОПИВ! Ваш хід знову.")
            self.my_turn = True
        elif result == "win":
            self.board_enemy[r][c] = "X"
            self.cells_enemy[r][c].configure(fg_color="#ff6600", text="🔥")
            self.result.configure(text="🏆 ВИ ВИГРАЛИ!")
            self.phase = "over"
            self.info.configure(text="🎉 Перемога!")

    def receive_enemy_shot(self, r, c):
        """Server tells us the enemy shot at (r,c) on our board."""
        self.parent.after(0, lambda: self._receive_enemy_shot_ui(r, c))

    def _receive_enemy_shot_ui(self, r, c, hit: bool):
        if hit:
            self.board_player[r][c] = "X"
            self.cells_player[r][c].configure(fg_color="#cc2200", text="💥")
            self.result.configure(text="💥 Суперник влучив! Його хід знову.")
        else:
            self.board_player[r][c] = "O"
            self.cells_player[r][c].configure(fg_color="#555", text="•")
            # enemy missed → our turn now
            self.my_turn = True
            self.result.configure(text="🎯 Суперник промахнувся! Ваш хід.")

    def start_game(self, first_turn: bool):
        """Switch phase to game and set whose turn it is."""
        self.parent.after(0, lambda: self._start_game_ui(first_turn))

    def _start_game_ui(self, first_turn: bool):
        self.phase = "game"
        self.my_turn = first_turn
        if first_turn:
            self.info.configure(text="🎮 ГРА ПОЧАЛАСЬ! Ваш хід — стріляйте по полю ворога.")
            self.result.configure(text="Ваш хід!")
        else:
            self.info.configure(text="🎮 ГРА ПОЧАЛАСЬ! Хід суперника — очікуйте…")
            self.result.configure(text="Хід суперника…")

    def game_over_lost(self):
        self.parent.after(0, lambda: self._game_over_lost_ui())

    def _game_over_lost_ui(self):
        self.phase = "over"
        self.info.configure(text="💀 Ви програли!")
        self.result.configure(text="Суперник потопив всі ваші кораблі.")


# ---------- SOCKET EVENTS ----------
@sio.event
def connect():
    app.after(0, lambda: add_message("✅ Підключено до сервера"))

@sio.event
def disconnect():
    app.after(0, lambda: add_message("❌ Відключено від сервера"))

@sio.on("message")
def on_message(data):
    app.after(0, lambda: add_message(data))

@sio.on("game_start")
def on_game_start(data):
    first = data.get("first_turn", False)
    app.after(0, lambda: _handle_game_start(first))

def _handle_game_start(first_turn):
    add_message("🎮 Гра починається!")
    if game:
        game._start_game_ui(first_turn)

@sio.on("place_ships")
def on_place_ships():
    app.after(0, lambda: _show_placement_screen())

def _show_placement_screen():
    global game
    add_message("🎮 Розставте свої кораблі!")
    chat_frame.pack_forget()
    start_ship_placement()

@sio.on("shot_result")
def on_shot_result(data):
    if game:
        r, c, result = data["r"], data["c"], data["result"]
        app.after(0, lambda: game._apply_shot_result_ui(r, c, result))

@sio.on("enemy_shot")
def on_enemy_shot(data):
    if game:
        r, c, hit = data["r"], data["c"], data["hit"]
        app.after(0, lambda: game._receive_enemy_shot_ui(r, c, hit))

@sio.on("game_over")
def on_game_over(data):
    if game:
        if data.get("winner") != nickname:
            app.after(0, lambda: game._game_over_lost_ui())


# ---------- FUNCTIONS ----------
def connect_to_server():
    global nickname
    nickname = name_entry.get().strip()
    if not nickname:
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
app.title("Морський Бій")
app.geometry("860x740")
app.protocol("WM_DELETE_WINDOW", close_app)

# ---------- START FRAME ----------
start_frame = ctk.CTkFrame(app)
start_frame.pack(pady=50, padx=50, fill="both", expand=True)

ctk.CTkLabel(
    start_frame, text="🎮 Морський Бій",
    font=ctk.CTkFont(size=28, weight="bold")
).pack(pady=20)

name_entry = ctk.CTkEntry(start_frame, placeholder_text="Ваш нікнейм")
name_entry.pack(pady=15)

ctk.CTkButton(
    start_frame, text="ПІДКЛЮЧИТИСЬ",
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

app.mainloop()