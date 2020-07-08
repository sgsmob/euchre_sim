from card import Game
from logging import Logger

if __name__ == "__main__":
	logger = Logger()
	for _ in range(1):
		game = Game(logger)
		game.play()
		
	print logger