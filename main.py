import customtkinter as ctk
import tkinter.messagebox as mb
import random

SIZE = 10
SHIPS_CONFIG = {4: 1, 3: 2, 2: 3, 1: 4}  # довжина: кількість

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SeaBattle:
    def __init__(self, root):
        self.root = root
        self.root.title("Морський бій")
        self.root.geometry("600x750")
        self.root.resizable(False, False)

        self.board_player = [["~"] * SIZE for _ in range(SIZE)]
        self.board_ai = [["~"] * SIZE for _ in range(SIZE)]

        # список кораблів, які треба розставити
        self.ships_to_place = []
        for length, count in SHIPS_CONFIG.items():
            self.ships_to_place += [length] * count

        self.placing_orientation = "H"  # орієнтація H/V
        self.phase = "placing"  # placing / game

        self.info = ctk.CTkLabel(
            root, text=f"Розставте корабель довжиною {self.ships_to_place[0]}",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.info.pack(pady=10)

        self.frame = ctk.CTkFrame(root, corner_radius=15)
        self.frame.pack(pady=10)

        self.orient_btn = ctk.CTkButton(root, text="Повернути (H/V)", command=self.toggle_orientation)
        self.orient_btn.pack(pady=5)

        self.start_btn = ctk.CTkButton(root, text="Почати гру", command=self.start_game, state="disabled")
        self.start_btn.pack(pady=5)

        self.result = ctk.CTkLabel(root, text="", font=ctk.CTkFont(size=14))
        self.result.pack(pady=5)

        self.draw_board()

    def toggle_orientation(self):
        self.placing_orientation = "V" if self.placing_orientation == "H" else "H"

    def draw_board(self):
        for w in self.frame.winfo_children():
            w.destroy()

        target_board = self.board_player if self.phase == "placing" else self.board_ai

        for r in range(SIZE):
            for c in range(SIZE):
                cell = target_board[r][c]
                color = None
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
                    font=ctk.CTkFont(size=14, weight="bold"),
                    command=lambda r=r, c=c: self.cell_click(r, c)
                )
                btn.grid(row=r, column=c, padx=2, pady=2)

    def cell_click(self, r, c):
        if self.phase == "placing":
            self.place_ship(r, c)
        elif self.phase == "game":
            self.player_shoot(r, c)

    def can_place_ship(self, r, c, length, orientation):
        """Перевіряємо, чи можна розмістити корабель"""
        coords = []
        for i in range(length):
            rr = r + i if orientation == "V" else r
            cc = c + i if orientation == "H" else c
            if rr >= SIZE or cc >= SIZE or self.board_player[rr][cc] == "S":
                return False
            coords.append((rr, cc))
        return True

    def place_ship(self, r, c):
        if not self.ships_to_place:
            return
        length = self.ships_to_place[0]

        if not self.can_place_ship(r, c, length, self.placing_orientation):
            mb.showwarning("Помилка", "Неможливо розмістити корабель тут!")
            return

        for i in range(length):
            rr = r + i if self.placing_orientation == "V" else r
            cc = c + i if self.placing_orientation == "H" else c
            self.board_player[rr][cc] = "S"

        self.ships_to_place.pop(0)
        if self.ships_to_place:
            self.info.configure(text=f"Розставте корабель довжиною {self.ships_to_place[0]}")
        else:
            self.info.configure(text="Всі кораблі розставлено!")
            self.start_btn.configure(state="normal")

        self.draw_board()

    def start_game(self):
        self.phase = "game"
        self.info.configure(text="Гра почалася! Ваш хід")
        self.start_btn.configure(state="disabled")
        self.orient_btn.configure(state="disabled")
        self.result.configure(text="")

        # Розставляємо AI кораблі випадково
        for length, count in SHIPS_CONFIG.items():
            for _ in range(count):
                placed = False
                while not placed:
                    r = random.randint(0, SIZE-1)
                    c = random.randint(0, SIZE-1)
                    orient = random.choice(["H","V"])
                    coords = []
                    for i in range(length):
                        rr = r + i if orient=="V" else r
                        cc = c + i if orient=="H" else c
                        if rr >= SIZE or cc >= SIZE or self.board_ai[rr][cc]=="S":
                            break
                        coords.append((rr, cc))
                    else:
                        for rr, cc in coords:
                            self.board_ai[rr][cc] = "S"
                        placed = True
        self.draw_board()

    def player_shoot(self, r, c):
        cell = self.board_ai[r][c]
        if cell in ("X","O"):
            return

        if cell == "S":
            self.board_ai[r][c] = "X"
            self.result.configure(text="🔥 ПОПАВ!")
        else:
            self.board_ai[r][c] = "O"
            self.result.configure(text="❌ ПРОМАХ!")

        self.draw_board()
        if not any("S" in row for row in self.board_ai):
            self.info.configure(text="🏆 Ви перемогли!")
            self.result.configure(text="")
            return

        # Хід AI
        self.ai_shoot()

    def ai_shoot(self):
        while True:
            r = random.randint(0, SIZE-1)
            c = random.randint(0, SIZE-1)
            cell = self.board_player[r][c]
            if cell not in ("X","O"):
                if cell == "S":
                    self.board_player[r][c] = "X"
                    self.result.configure(text="💥 AI ПОПАВ!")
                else:
                    self.board_player[r][c] = "O"
                    self.result.configure(text="AI ПРОМАХ!")
                break
        self.draw_board()
        if not any("S" in row for row in self.board_player):
            self.info.configure(text="💀 AI переміг!")
            self.result.configure(text="")


# ---------- ЗАПУСК ----------
root = ctk.CTk()
game = SeaBattle(root)
root.mainloop()
