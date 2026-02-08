import random
from pathlib import Path
from typing import List, Optional

from src.board import Board
from src.dictionary import Dictionary
from src.player import Player
from src.tile import BoardTile, TileBag, Tile


class NotAWordException(Exception):
    pass


class Game:
    HAND_SIZE = 7

    def __init__(self, players: Optional[List[Player]] = None):
        if not players:
            players = []
        self.board = Board()
        self.tile_bag = TileBag()
        dict_path = Path(__file__).parent.parent / "dicts" / "sowpods.txt"
        self.dictionary = Dictionary(dict_path)
        self.players: list[Player] = players
        self.current_player: Player = self.players[0] if self.players else None
        self.player_turn: int = 0

        # isinstance() allows subclasses.
        # if len(players) == 0 or not all(isinstance(p, Player) for p in players):
        #     raise ValueError(
        #         "Players must be a non empty list of Player objects.")

    def _set_player_turn(self, set_to):
        self.player_turn = set_to
        self.current_player = self.players[set_to]


    def start(self):
        """Sets up the game, and starts the main game loop"""
        self._set_player_turn(random.randint(0, len(self.players) - 1))
        print("Drawing hands...")
        for _ in self.players:
            assert self.current_player
            self.current_player.hand.extend(self.tile_bag.draw_n(Game.HAND_SIZE))
            self.__increment_turn_counter()

        # INFO: Main game loop is here!
        while not self.is_game_over():
            self.turn_cycle()

    def turn_cycle(self):
        """Main turn cycle of the game"""
        assert self.current_player
        print(f"{self.current_player.name}'s turn")
        self.board.display()
        self.current_player.play_turn(self)

        self.refill_hand(self.current_player)
        self.__increment_turn_counter()

    def refill_hand(self, player: Player):
        """
        Refills a given players hand
        """
        if len(player.hand) <= Game.HAND_SIZE:
            player.hand.extend(self.tile_bag.draw_n(Game.HAND_SIZE - len(player.hand)))
        else:
            raise ValueError(
                f"Cheater! hand too big: {player.hand} > {Game.HAND_SIZE}."
            )

    def is_game_over(self):
        """
        Checks if the game is over
        """
        bag_empty = self.tile_bag.is_empty()
        player_out = any(len(player.hand) == 0 for player in self.players)
        return bag_empty and player_out


    def add_player(self, player: Player):
        """
        Adds player to the game
        """
        self.players.append(player)

    def __increment_turn_counter(self):
        self.player_turn = (self.player_turn + 1) % len(self.players)
        self.current_player = self.players[self.player_turn]

    @staticmethod
    def calculate_word_score(word_tiles: list[BoardTile]):
        total_score, total_mult = 0, 1
        for tile in word_tiles:
            score, mult = tile.calculate_score()
            total_score += score
            total_mult *= mult
        return total_score * total_mult

    def __find_connected(self, row, col, look_vertical: bool):
        tile = self.board.get(row, col)
        j = 0
        while not tile.is_empty():
            j -= 1
            try:
                tile = self.board.get(
                    row + (j if look_vertical else 0),
                    col + (j if not look_vertical else 0),
                )
            except ValueError:
                break
        wordtiles = []
        j += 1  # get back to the word
        tile = self.board.get(
            row + (j if look_vertical else 0),
            col + (j if not look_vertical else 0),
        )
        while not tile.is_empty():
            wordtiles.append(tile)
            j += 1
            try:
                tile = self.board.get(
                    row + (j if look_vertical else 0),
                    col + (j if not look_vertical else 0),
                )
            except ValueError:
                break
        return wordtiles

    def get_connecting_words(
        self, row: int, col: int, word: str, is_vertical: bool
    ) -> list[list[BoardTile]]:
        """
        Gets all words (strings longer than 1 char) connecting to a given word
        if it was placed on the board.
        It does not care if the word is valid.
        """
        words = []
        # First it checks all words in the perpendicular direction for each char
        for i in range(len(word)):
            # goes left until no word
            found = self.__find_connected(
                row + (i if is_vertical else 0),
                col + (i if not is_vertical else 0),
                not is_vertical,
            )
            if found and len(found) > 1:
                words.append(found)

        found = self.__find_connected(row, col, is_vertical)
        if found and len(found) > 1:
            words.append(found)

        return words

    # Stuff for API

    def _check_word_fits(
        self, start_row: int, start_col, word: str, is_vertical: bool
    ) -> int:
        """check if placement is empty or duplicate letter, returning the total overlaps"""
        total_overlaps = 0
        for i, char in enumerate(word):
            if is_vertical:
                board_tile = self.board.get(start_row + i, start_col)
            else:
                board_tile = self.board.get(start_row, start_col + i)

            if not board_tile.is_empty() and board_tile.letter != char:
                raise ValueError(
                    f"{word} has invalid placement at {start_row + i}, {start_col + i}"
                )
            if board_tile.letter == char:
                total_overlaps += 1
        return total_overlaps

    def is_placement_valid(self, start_row: int, start_col: int, word: str, is_vertical: bool, raise_errors=False):
        # raises error if word does not fit / overlaps incorrectly
        try:
            total_overlaps = self._check_word_fits(
                start_row, start_col, word, is_vertical
            )
        except Exception as e:
            if raise_errors:
                raise e

            return False

        # Check Scrabble placement rules
        if self.board.is_empty():
            # First word must cover center square (7, 7)
            center_covered = False
            for i in range(len(word)):
                check_row = start_row + (i if is_vertical else 0)
                check_col = start_col + (i if not is_vertical else 0)
                if check_row == 7 and check_col == 7:
                    center_covered = True
                    break

            if not center_covered:
                if raise_errors:
                    raise ValueError("First word must cover the center square at position (7, 7).")
                return False
        else:
            # Subsequent words must connect to existing tiles
            # Either through overlap or by being adjacent

            if total_overlaps == 0:
                # No overlap, so check if adjacent to any existing tile
                has_adjacent = False
                for i in range(len(word)):
                    check_row = start_row + (i if is_vertical else 0)
                    check_col = start_col + (i if not is_vertical else 0)

                    # Check all 4 directions for adjacent tiles
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        try:
                            adjacent_tile = self.board.get(check_row + dr, check_col + dc)
                            if not adjacent_tile.is_empty():
                                has_adjacent = True
                                break
                        except ValueError:
                            # Out of bounds, skip
                            pass

                    if has_adjacent:
                        break

                if not has_adjacent:
                    if raise_errors:
                        raise ValueError("Word must connect to existing tiles on the board.")
                    return False

        # Validate that the word itself is in the dictionary
        if word.lower() not in self.dictionary:
            if raise_errors:
                raise NotAWordException(f"{word} is not in {self.dictionary}.")
            return False


        # Actually place the letters on the board
        over_written = []
        for i, char in enumerate(word):
            if is_vertical:
                tile = self.board.get(start_row + i, start_col)
            else:
                tile = self.board.get(start_row, start_col + i)

            # Only place if the tile is empty (not an overlap)
            if tile.is_empty():
                self.board.place(
                    start_row + i if is_vertical else start_row,
                    start_col if is_vertical else start_col + i,
                    char
                )
                over_written.append((start_row + i if is_vertical else start_row,
                                     start_col if is_vertical else start_col + i))


        connecting_words = self.get_connecting_words(
            start_row, start_col, word, is_vertical
        )

        for connecting in connecting_words:
            parsed_connecting_word = "".join(char.letter for char in connecting)
            if parsed_connecting_word not in self.dictionary:
                for (row, col) in over_written:
                    self.board.get(row, col).clear()

                if raise_errors:
                    raise NotAWordException(f"{parsed_connecting_word} is not in {self.dictionary}.")
                return False

        return True

    def place_word(self, start_row: int, start_col: int, word: str, is_vertical: bool):
        """
        Places a word on the board.
        Any overlap should be included.

        Ends the current players turn afterwards.
        """

        valid = self.is_placement_valid(start_row, start_col, word, is_vertical, raise_errors=True)

        if not valid:
            return

        total_overlaps = self._check_word_fits(
            start_row, start_col, word, is_vertical
        )

        # Actually place the letters on the board
        for i, char in enumerate(word):
            if is_vertical:
                tile = self.board.get(start_row + i, start_col)
            else:
                tile = self.board.get(start_row, start_col + i)

            # Only place if the tile is empty (not an overlap)
            if tile.is_empty():
                self.board.place(
                    start_row + i if is_vertical else start_row,
                    start_col if is_vertical else start_col + i,
                    char
                )


        # check if bingo
        score = 0
        total_used_letters = len(word) - total_overlaps
        if total_used_letters == 7:  # hand size
            score += 50  # + 50 if bingo

        connecting_words = self.get_connecting_words(
            start_row, start_col, word, is_vertical
        )

        all_used_tiles = []
        for connecting in connecting_words:
            parsed_connecting_word = "".join(char.letter for char in connecting)
            if parsed_connecting_word not in self.dictionary:
                raise NotAWordException(f"{parsed_connecting_word} is not in {self.dictionary}.")

            # score all words
            score += Game.calculate_word_score(connecting)
            for char in connecting:
                # use it up later
                if char not in all_used_tiles:
                    all_used_tiles.append(char)

        hand = self.current_player.hand
        for char in all_used_tiles:
            if char in hand:
                hand.remove(Tile(char.letter))
            char.use_up()

    def discard_letters(self, player: Player, letters: list[str]):
        temp_hand = [tile.letter for tile in player.hand]
        popped = []
        for letter in letters:
            try:
                index = temp_hand.index(letter)
                popped.append(player.hand.pop(index))
                temp_hand.pop(index) # as long as no race conditions this is OK
            except ValueError:
                raise ValueError(
                    f"{letter} not in {[tile.letter for tile in player.hand]}")

        # puts all removed back into tile bag - this is exact same Tile obj
        self.tile_bag.add(popped)

