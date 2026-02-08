from typing import Optional

from src.api import Api
from src.tile import Tile, TileBag


class Player:
    def __init__(self, name):
        """main player object, also where bots are assigned"""
        self.name = name
        self.score = 0
        self.hand: list[Tile] = []
        self.time_remaining_s: float = 3 * 60
        self.api: Optional[Api] = None

    def assign_bot(self, game, bot_class):  # how does this work
        self.api = bot_class()
        self.api.hook(game, self)

    def play_human_turn(self, game) -> None:
        """
        Human can:
        exchange
        pass
        place
        """
        print("Your hand: " + " ".join(
            list(
                # f"{c}({TileBag.scores.get(c.letter.lower())})"
                str(c) for c in self.hand
            )
        ))
        choice = int(
            input(
                "What would you like to do?"
                "\n1) Exchange tiles"
                "\n2) Pass your turn"
                "\n3) Place tiles"
                "\n>> "
            )
        )
        match choice:
            case 1:
                letters: list = input(
                    "Choose the letters you would like to "
                    "exchange, e.g. 'a b c d e' to exchange [a], "
                    "[b], [c], [d], [e] from your hand.").split(" ")
                return game.discard_letters(self, letters)
            case 2:
                return None
            case 3:
                word = input("What word would you like to play? Remember to "
                             "include any overlap.")
                start_row = int(input(
                    "Choose the start row (start from 0):"
                ))
                start_col = int(input(
                    "Choose the start column (start from 0):"
                ))
                is_vertical = True if (input("Is your word vertical ("
                                             "y/n)").lower() == "y") else False
                hand_str = [char.letter for char in self.hand]
                for char in word:
                    if char not in hand_str:
                        print("Invalid word, please try again!")
                        return self.play_human_turn(game)
                    hand_str.remove(char)

                return game.place_word(start_col, start_row, word, is_vertical)
            case _:
                print(f"Input {choice} unrecognised, please try again.")
                return self.play_human_turn(game)

    def play_turn(self, game):
        if self.api:
            return self.api.on_turn()
        return self.play_human_turn(game)
