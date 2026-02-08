"""
Hey!

Funny seeing you sneaking around in here.
When creating your bot, keep in mind that when your bot is run,
it will not be with this exact file. It will be on the hosts side.
Any modifications you make here will not work when it comes to a tournament.
If you have found a bug, say, dont fix it yourself.

"""
import time
from copy import deepcopy

from .dictionary import Dictionary


class NotReadyException(Exception):
    pass

class MoveException(Exception):
    pass

class EarlyExitException(Exception):
    pass


class EarlyExitContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            if isinstance(exc_val, EarlyExitException):
                return True  # Suppress Exception, turn has been ended

        return False


class Api:
    def __init__(self):
        self.__player = None
        self.__game = None
        self.__board = None

        self.__task = None
        self.__hooked = False
        self.__hand_is_visible = False

    @staticmethod
    def __get_game_class(): # Cursed. But it stops a circular import error
        from .game import Game
        return Game

    def hook(self, game: "Game", player):
        if self.__hooked or not isinstance(game, Api.__get_game_class()):
            raise RuntimeError("Stop Messing with shit")

        self.__player = player
        self.__game = game
        self.__board = self.__game.board
        self.__hooked = True

        self._init()

        # After starting the bot, we can unhide some info ready for the first round
        self.__hand_is_visible = True

    # Helpers

    @property
    def board_size(self) -> tuple[int, int]:
        if not self.__hooked:
            raise NotReadyException("Cannot access properties of the board. Game has not been started")

        return self.__board.rows, self.__board.cols

    @property
    def board(self) -> list[list]:
        """
        Returns a copy of the board.

        THIS IS NOT THE ACTUAL BOARD CLASS BENEDICT DON'T TRY TO CALL RANDOM METHODS
        """
        if not self.__hooked:
            raise NotReadyException("Cannot access properties of the board. Game has not been started")

        return deepcopy(self.__board.grid)

    def get_tiles_in_hand(self) -> list[str]:
        if not self.__hooked:
            raise NotReadyException("Cannot access properties of the player. Game has not been started")

        if not self.__hand_is_visible:
            raise NotReadyException("Your hand has not yet been delt")

        return [
            tile.letter for tile in self.__player.hand
        ]

    def get_dictionary(self) -> Dictionary:
        if not self.__hooked:
            raise NotReadyException("Cannot access properties of the game. Game has not been started")

        return deepcopy(self.__game.dictionary)

    def check_placement(self, word: str, is_vertical: bool, x: int, y: int) -> bool:
        if not self.__hooked:
            raise NotReadyException("Cannot access properties of the board. Game has not been started")

        return self.__game.is_placement_valid(y, x, word, is_vertical,
                                              raise_errors=False)
    # Actions

    def place_word(self, word: str, is_vertical: bool, x: int, y: int) -> None:
        """ Calling this method ends your turn instantly """
        if type(word) is not str or type(is_vertical) is not bool and type(x) is not int and type(y) is not int:
            raise MoveException(f"Invalid arguments passed to Api.place_word(word: str, is_vertical: bool, x: int, y: int)")

        self.__task = ("place", (y, x, word, is_vertical))
        raise EarlyExitException

    def discard_letters(self, letters: list[str]) -> None:
        """ Calling this method ends your turn instantly """
        if type(letters) is not list or len(letters) <= 0 or len(letters) > 7:
            raise MoveException(f"Invalid arguments passed to Api.discard_letters(letters: list[str]): Min 1, Max 7")

        self.__task = ("discard", (letters,))
        raise EarlyExitException

    def pass_turn(self):
        """ Calling this method ends your turn instantly """
        self.__task = ("pass", ())
        raise EarlyExitException

    def on_turn(self):
        self.__task = None

        start = time.perf_counter()

        with EarlyExitContextManager():
            self._on_turn()

        elapsed = time.perf_counter() - start

        self.__player.time_remaining_s -= elapsed

        if not self.__task:
            print("[WARNING] A action was not performed. The turn has been passed")
            self.__task = ("pass", ())

        task, args = self.__task

        if task == "place":
            self.__game.place_word(*args)

        elif task == "discard":
            self.__game.discard_letters(self.__player, *args)

        elif task == "pass":
            pass

        else:  # This should never get raised. But I know my coding skills.
            raise NotImplementedError(f"A task '{task}' is not implemented or is not intended")


    def _init(self):
        """ This method is called when your bot and the game are initialized. """
        pass

    def _on_turn(self) -> None:
        """ This is ur bit silly """
        raise NotImplementedError

