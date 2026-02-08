from src.api import Api
import random
import time

tile_scores = { "?": 0, "e": 1, "a": 1, "i": 1, "o": 1, "n": 1, "r": 1, "t": 1, "l": 1, "s": 1, "u": 1, "d": 2, "g": 2,
    "b": 3, "c": 3, "m": 3, "p": 3, "f": 4, "h": 4, "v": 4, "w": 4, "y": 4, "k": 5, "j": 8, "x": 8, "q": 10, "z": 10}


"""
def create_bucketed_dictionary(dictionary: set) -> dict:
    bucket = {}

    for word in dictionary:
        sub_bucket = bucket
        for char in list(word):
            if char not in sub_bucket:
                sub_bucket[char] = {}

            sub_bucket = sub_bucket[char]

    return bucket
"""

def create_bucketed_dictionary(dictionary: set) -> dict:
    bucket = {}

    for word in dictionary:
        first_char = word[0]

        if first_char not in bucket:
            bucket[first_char] = []

        bucket[first_char].append(word)

    return bucket

class MyBot(Api):
    def __init__(self):
        super().__init__()

        self.dictionary_buckets = {}
        self.first_turn = True

    def _init(self):
        self.dictionary_buckets = create_bucketed_dictionary(self.get_dictionary().words)

    @staticmethod
    def can_make_word(hand: list[str], word: str) -> bool:
        for char in set(word):
            if char not in hand:
                return False

            if hand.count(char) < word.count(char):
                return False

        return True


    def get_possible_words(self, hand: list[str]):
        return [ word for char in set(hand) if char in self.dictionary_buckets for word in self.dictionary_buckets[char] if self.can_make_word(hand, word) ]

    @staticmethod
    def score_word(word: str):
        bonus = 50 if len(word) > 6 else 0
        return sum([tile_scores[char] for char in word]) + bonus

    def score_words(self, words: list[str]):
        words.sort(key=self.score_word, reverse=True)

    @staticmethod
    def get_viable_locations(board):
        return [
            (x, y)
            for y in range(1, len(board) - 1)
            for x in range(1, len(board[y]) - 1)
            if (
                       (v_count := int(bool(board[y][x + 1])) + int(bool(board[y][x - 1]))) == -1 or
                       (h_count := int(bool(board[y + 1][x])) + int(bool(board[y - 1][x]))) == -1
               ) or (not board[y][x])
            if (v_count > 0 and h_count == 0) or (h_count > 0 and v_count == 0)
        ]

    def _on_turn(self) -> None:
        board = self.board
        hand = self.get_tiles_in_hand()

        possible_words = self.get_possible_words(hand)
        self.score_words(possible_words)

        viable_locations = self.get_viable_locations(board)

        if not viable_locations and self.first_turn:
            viable_locations = [(x, y) for x in range(1, 10) for y in range(1, 10)]

        self.first_turn = False
        for playable in possible_words:
            for x, y in viable_locations:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if self.check_placement(playable, True, x + dx, y + dy):
                        self.place_word(playable, True, x + dx, y + dy)

                    if self.check_placement(playable, False, x + dx, y + dy):
                        self.place_word(playable, False, x + dx, y + dy)

        # No Moves? No Problem!
        self.discard_letters(hand)