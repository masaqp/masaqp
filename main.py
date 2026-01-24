import customtkinter as ctk
import random

SIZE = 10
SHIPS = 10

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class SeaBattle:
    def __init__(self, root):
        self.root = root
        self.root.title("Морський бій")
        self.root.geometry("520x650")
        self.root.resizable(False, False)

        self.current_player = 1

        self.board1 = self.create_board()
        self.board2 = self.create_board()

        self.place_ships(self.board1)
        self.place_ships(self.board2)

        self.info = ctk.CTkLabel(
            root,
            text="Хід гравця 1 (б’є поле гравця 2)",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.info.pack(pady=10)

        self.result = ctk.CTkLabel(
            root,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.result.pack(pady=5)

        self.frame = ctk.CTkFrame(root, corner_radius=15)
        self.frame.pack(pady=10)

        self.draw_board()

    def create_board(self):
        return [["~"] * SIZE for _ in range(SIZE)]

    def place_ships(self, board):
        ships = 0
        while ships < SHIPS:
            r = random.randint(0, SIZE - 1)
            c = random.randint(0, SIZE - 1)
            if board[r][c] == "~":
                board[r][c] = "S"
                ships += 1

    def draw_board(self):
        for w in self.frame.winfo_children():
            w.destroy()

        target = self.board2 if self.current_player == 1 else self.board1

        for r in range(SIZE):
            for c in range(SIZE):
                text = target[r][c]
                if text == "S":
                    text = "~"

                btn = ctk.CTkButton(
                    self.frame,
                    text=text,
                    width=40,
                    height=40,
                    font=ctk.CTkFont(size=14, weight="bold"),
                    command=lambda r=r, c=c: self.shoot(r, c)
                )
                btn.grid(row=r, column=c, padx=2, pady=2)

    def shoot(self, r, c):
        target = self.board2 if self.current_player == 1 else self.board1

        if target[r][c] in ("X", "O"):
            return

        if target[r][c] == "S":
            target[r][c] = "X"
            self.result.configure(text="🔥 ПОПАВ!")
        else:
            target[r][c] = "O"
            self.result.configure(text="❌ ПРОМАХ!")
            self.switch_player()

        if not any("S" in row for row in target):
            self.info.configure(text=f"🏆 Переміг гравець {self.current_player}!")
            self.result.configure(text="")
            return

        self.draw_board()

    def switch_player(self):
        self.current_player = 2 if self.current_player == 1 else 1
        self.info.configure(
            text=f"Хід гравця {self.current_player} (б’є поле гравця {1 if self.current_player == 2 else 2})"
        )


# ---------- ЗАПУСК ----------
root = ctk.CTk()
game = SeaBattle(root)
root.mainloop()
