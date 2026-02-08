from src.game import Game
from src.player import Player
from src.dans_bot import MyBot

bot = Player("Bot 1")
bot2 = Player("Bot 2")
game = Game([bot, bot2])
bot.assign_bot(game, MyBot)
bot2.assign_bot(game, MyBot)

game.start()
