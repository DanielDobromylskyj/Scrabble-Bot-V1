import random
from typing import Optional

from colorama import Back, Fore


class Tile:
    """
    Basic scrabble tile, can either be blank or have a letter.
    """

    def __init__(self, letter: str = ""):
        """Initialize a tile with an optional letter (default is blank). Use "?" for blank tiles."""
        self.letter = letter

    def __str__(self):
        return self.letter if self.letter else " "

    def __bool__(self):
        return self.letter not in [" ", "", None]

    def __eq__(self, other):
        if type(other) is str:
            return self.letter == other

        if isinstance(other, Tile):
            return self.letter == other.letter

        raise ValueError("Cant Compare Tile To Something Silly", type(other))


class TileBag:
    """Glorified hashmap of tiles"""

    distribution: dict[str, int] = {
        "?": 2,
        "e": 12,
        "a": 9,
        "i": 9,
        "o": 8,
        "n": 6,
        "r": 6,
        "t": 6,
        "l": 4,
        "s": 4,
        "u": 4,
        "d": 4,
        "g": 3,
        "b": 2,
        "c": 2,
        "m": 2,
        "p": 2,
        "f": 2,
        "h": 2,
        "v": 2,
        "w": 2,
        "y": 2,
        "k": 1,
        "j": 1,
        "x": 1,
        "q": 1,
        "z": 1,
    }

    scores = {
        "?": 0,
        "e": 1,
        "a": 1,
        "i": 1,
        "o": 1,
        "n": 1,
        "r": 1,
        "t": 1,
        "l": 1,
        "s": 1,
        "u": 1,
        "d": 2,
        "g": 2,
        "b": 3,
        "c": 3,
        "m": 3,
        "p": 3,
        "f": 4,
        "h": 4,
        "v": 4,
        "w": 4,
        "y": 4,
        "k": 5,
        "j": 8,
        "x": 8,
        "q": 10,
        "z": 10,
    }

    def __init__(self):
        # Scrabble tile distribution:
        """
        Makes a shuffled list of tiles, also look here for all tile score
        values and distributions.

        From wikipedia:
        2 blank tiles (scoring 0 points)
        1 point: E ×12, A ×9, I ×9, O ×8, N ×6, R ×6, T ×6, L ×4, S ×4, U ×4
        2 points: D ×4, G ×3
        3 points: B ×2, C ×2, M ×2, P ×2
        4 points: F ×2, H ×2, V ×2, W ×2, Y ×2
        5 points: K ×1
        8 points: J ×1, X ×1
        10 points: Q ×1, Z ×1
        """
        self.__tiles = []
        for letter, count in self.distribution.items():
            self.__tiles.extend([Tile(letter) for _ in range(count)])
        random.shuffle(self.__tiles)

    def is_empty(self):
        return len(self.__tiles) == 0

    def add(self, tiles: Tile | list[Tile]):
        """add a list or one tile to the bag, it gets reshuffled"""
        if isinstance(tiles, list):
            self.__tiles.extend(tiles)
        else:
            self.__tiles.append(tiles)
        random.shuffle(self.__tiles)

    def draw(self) -> Optional[Tile]:
        """draw a tile"""
        return self.__tiles.pop() if self.__tiles else None

    def draw_n(self, n: int) -> list[Tile]:
        """draw n tiles"""
        i = 0
        tiles: list[Tile] = []
        while self.__tiles and i < n:
            i += 1
            tiles.append(self.draw())
        return tiles

    def __len__(self) -> int:
        return len(self.__tiles)



class BoardTile(Tile):
    """
    A tile on the Scrabble board that may have special properties.
    """

    def __init__(self, multiplier: int = 1, is_word_multiplier: bool = False):
        super().__init__()
        self.multiplier = multiplier
        self.is_word_multiplier = is_word_multiplier
        self.used_up = False

    def use_up(self):
        """Remove multiplier"""
        self.used_up = True

    def is_empty(self) -> bool:
        return self.letter in [" ", "", None]

    def clear(self):
        self.letter = ""

    def place(self, lettertile: str | Tile):
        if not self.is_empty():
            raise ValueError("Tile already has a letter")

        if isinstance(lettertile, Tile):
            self.letter = lettertile.letter
        elif isinstance(lettertile, str):
            self.letter = lettertile

    def calculate_score(self) -> tuple[int, int]:
        """
        Calculates score for this tile, returns a tuple
        of (score, mult) to be used in running totals
        """
        if self.used_up or self.is_empty():
            return (0, 1)  # Return neutral multiplier of 1, not 0
        # NOTE: self.used_up is set in place_word after everything is done.
        letter_score = TileBag.scores[self.letter]
        if self.is_word_multiplier:
            return (letter_score, self.multiplier)

        letter_score *= self.multiplier
        return (letter_score, 1)

    @classmethod
    def quick_create(cls, creation_str: str):
        """
        Create a BoardTile from a shorthand string.
        Examples:
            "2L" -> double letter score
            "3W" -> triple word score
            "1"  -> normal tile
        """
        if creation_str.endswith("L"):
            multiplier = int(creation_str[:-1])
            return BoardTile(multiplier=multiplier, is_word_multiplier=False)
        if creation_str.endswith("W"):
            multiplier = int(creation_str[:-1])
            return BoardTile(multiplier=multiplier, is_word_multiplier=True)
        return BoardTile()

    def __get_style(self) -> str:
        if not self.is_empty():
            return Back.WHITE + Fore.BLACK
        if self.multiplier == 2 and not self.is_word_multiplier:
            return Back.CYAN
        if self.multiplier == 3 and not self.is_word_multiplier:
            return Back.BLUE
        if self.multiplier == 2 and self.is_word_multiplier:
            return Back.MAGENTA
        if self.multiplier == 3 and self.is_word_multiplier:
            return Back.RED
        return Back.RESET

    def __str__(self):
        return self.__get_style() + super().__str__() + Back.RESET + Fore.RESET
