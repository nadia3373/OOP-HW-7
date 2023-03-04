import abc, random
from tkinter import Tk, Label, Frame, Button, X, BOTH
from typing import List, Tuple


class Board:
    def __init__(self, size: int):
        self.size: int = size
        self.state: List[Tuple[int, int]] = [(i, j) for i in range(size) for j in range(size)]
        self.combos: List[List[Tuple[int, int]]] = self.winning_combos(size)
        self.corners: List[Tuple[int, int]] = [(i, j) for i in (0, size-1) for j in (0, size-1)]
    
    def free(self) -> int:
        return len(self.state)

    def reset(self) -> None:
        self.state: List[Tuple[int, int]] = [(i, j) for i in range(self.size) for j in range(self.size)]
    
    def winning_combos(self, n: int) -> List[List[Tuple[int, int]]]:
        rows = [[(j, i) for i in range(n)] for j in range(n)]
        columns = [[(i, j) for i in range(n)] for j in range(n)]
        d1 = [[row[i] for i, row in enumerate(rows)]]
        d2 = [[col[j] for j, col in enumerate(reversed(columns))]]
        return rows + columns + d1 + d2


class Game:
    def __init__(self, size: int):
        self.board: Board = Board(size)
        self.player1, self.player2 = self.get_players()
        self.current_player: Player = self.player1
        self.status: bool = False
        self.user_interface: UserInterface = UserInterface(self)
        if isinstance(self.current_player, Computer): self.current_player.move(self)
    
    def get_players(self) -> Tuple:
        player1 = Human("X")
        player2 = None
        while player2 is None:
            choice = input("Выберите тип игры (1 – игра с компьютером, 2 – игра между двумя игроками): ")
            choice = int(choice) if choice.isdigit() else None
            player2 = Computer("O") if choice == 1 else Human("O") if choice == 2 else None
            if player2 is None: print("Некорректный выбор!")
        choice = input("Выберите символ для игрока 1 (1 – X, 2 – O): ")
        choice = int(choice) if choice.isdigit() else None
        if choice == 2: (player1.sign, player2.sign) = (player2.sign, player1.sign)
        if player1.sign is None: print("Некорректный выбор!")
        choice = input(f"Кто делает первый ход? 1 – {player1.sign}, 2 – {player2.sign}: ")
        choice = int(choice) if choice.isdigit() else None
        if choice == 2: (player1, player2) = (player2, player1)
        if choice is None: print("Некорректный выбор!")
        return player1, player2
    
    def reset_game(self) -> None:
        self.board.reset()
        self.user_interface.reset()
        self.current_player = self.player1
        self.status = False
        self.player1.moves = []
        self.player2.moves = []
        if isinstance(self.current_player, Computer): self.current_player.move(self)

    def update_status(self) -> None:
        self.status = self.check_win()
        if self.status:
            self.user_interface.disable_buttons()
            self.user_interface.update(f"{self.current_player.sign} победил")
        elif self.check_draw():
            self.user_interface.update("Ничья")
        else:
            self.switch_players()
            if isinstance(self.current_player, Computer): self.current_player.move(self)
            else: self.user_interface.update(f"Ходит {self.current_player.sign}")

    def check_win(self) -> bool:
        return self.current_player.has_won(self.board.combos)

    def check_draw(self) -> bool:
        return True if self.board.free() == 0 else False

    def switch_players(self) -> None:
        self.current_player = self.player2 if self.current_player == self.player1 else self.player1


class Player(metaclass=abc.ABCMeta):
    def __init__(self, sign):
        self.sign = sign
        self.moves = []
        
    def add_move(self, move: Tuple[int]) -> None:
        self.moves.append(move)
        
    def has_won(self, combos: List[List[Tuple[int]]]) -> bool:
        for combo in combos:
            if set(combo).issubset(set(self.moves)):
                return True
        return False
    
    @abc.abstractmethod
    def move(self) -> None:
        pass


class Human(Player):
    def move(self, game: 'Game', row: int, column: int) -> None:
        button: Button = game.user_interface.buttons[row * game.board.size + column]
        if button["state"] != "disabled":
            button["state"] = "disabled"
            button["text"] = self.sign
            self.moves.append((row, column))
            game.board.state.remove((row, column))
            game.update_status()


class Computer(Player): 
    def calculate_move(self, game: 'Game') -> Tuple[int, int]:
        other_player = game.player1 if game.player1 != self else game.player2
        move = None
        if game.board.size % 2 != 0:
            center = (game.board.size // 2, game.board.size // 2)
        if center in game.board.state:
            move = center
        if move is None:
            for i in game.board.combos:
                if len(set(i).intersection(set(self.moves))) == 2:
                    if tuple(set(i).difference(set(self.moves)))[0] in game.board.state:
                        move = tuple(set(i).difference(set(self.moves)))[0]
                        break
        if move is None:
            for i in game.board.combos:
                if len(set(i).intersection(set(other_player.moves))) == 2:
                    if tuple(set(i).difference(set(other_player.moves)))[0] in game.board.state:
                        move = tuple(set(i).difference(set(other_player.moves)))[0]
                        break
        if move is None:
            free_corners = [i for i in game.board.corners if i in game.board.state]
            if len(free_corners) > 0:
                move = free_corners[random.randint(0, len(free_corners) - 1)]
        if move is None:
            free_cells = [i for i in game.board.state]
            move = free_cells[random.randint(0, len(free_cells) - 1)]
        return move
    
    def move(self, game: 'Game', row: int=None, column: int=None) -> None:
        move = self.calculate_move(game)
        button = game.user_interface.buttons[move[0] * game.board.size + move[1]]
        button["state"] = "disabled"
        button["text"] = self.sign
        game.board.state.remove(move)
        self.add_move((move[0], move[1]))
        game.update_status()


class UserInterface():
    def __init__(self, game: Game):
        self.game = game
        self.window: Tk = Tk()
        self.configure_window()
        self.new_game_button: Button = Button(self.window, text="Новая игра", font=('Arial', 15), command=self.game.reset_game)
        self.new_game_button.pack(fill=X)
        self.frame: Frame = Frame(self.window, bg="gray20")
        self.frame.pack(expand=1, fill=BOTH)
        self.buttons: List[Button] = self.get_buttons(self.game.board.size)
        self.window.bind("<Configure>", self.resize_buttons_font)
        self.status_label: Label = Label(self.window, text=f"Ходит {self.game.current_player.sign}", font=('Arial', 15), bg='green', fg='snow')
        self.status_label.pack(fill=X)
    
    def configure_window(self) -> Tk:
        self.window.aspect(1, 1, 1, 1)
        self.window.minsize(300, 300)
        self.window.title("Крестики-нолики")
        self.window.update_idletasks()

    def disable_buttons(self) -> None:
        [button.config(state='disabled') for button in self.buttons if button["state"] != "disabled"]
    
    def get_buttons(self, size: int) -> List[Button]:
        buttons: List[Button] = []
        for i in range(size):
            self.frame.columnconfigure(i, weight=1)
            self.frame.rowconfigure(i, weight=1)
            for j in range(size):
                button: Button = Button(
                    self.frame,
                    font=('Arial', 36),
                    highlightthickness=0,
                    relief="flat",
                    state="active",
                    text='',
                    fg="white",
                    bg="blue",
                    command=lambda row=i, col=j: self.game.current_player.move(self.game, row, col)
                )
                button.grid(row=i, column=j, sticky="news", padx=1, pady=1)
                buttons.append(button)
        return buttons

    def resize_buttons_font(self, event) -> None:
        font_size = int(event.height / 4)
        for button in self.buttons:
            button.config(font=('Arial', font_size))
    
    def reset(self):
        for button in self.buttons:
            button["state"] = "active"
            button["text"] = ""
        self.status_label["text"] = f"Ходит {self.game.current_player.sign}"
    
    def update(self, text: str):
        self.status_label["text"] = text
