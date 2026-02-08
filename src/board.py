"""
Main board file
"""

from pathlib import Path
from colorama import init

from src.tile import BoardTile

init()  # sets up colorama


class Board:
    """
    Basic Scrabble board.
    """

    def __init__(self, rows=15, cols=15):
        self.rows = rows
        self.cols = cols
        self.grid: list[list[BoardTile]] = self._create_empty_board()

    def is_empty(self):
        return not any(any(row) for row in self.grid)

    def _create_empty_board(self):
        board_file = Path(__file__).parent / "blankboard.txt"
        with open(board_file, "rt") as f:
            temp = [line.strip().split() for line in f.readlines()]
        board = []
        for row in temp:
            new = []
            for col in row:
                tile = BoardTile.quick_create(col)
                new.append(tile)
            board.append(new)
        return board

    def display(self):
        """displays board with colours"""
        for i, row in enumerate(self.grid):
            print("|".join(str(tile) for tile in row))
            if i < self.rows - 1:
                print("-" * (self.cols * 2 - 1))

    def get(self, row, col):
        """gets given tile"""
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return self.grid[row][col]
        raise ValueError("Position out of bounds")

    def place(self, row, col, letter: str):
        """places a letter at given tile"""
        self.get(row, col).place(letter)


if __name__ == "__main__":
    board = Board()
    board.place(7, 7, "l")
    board.place(7, 8, "e")
    board.display()
