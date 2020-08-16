from card import Game
from logging import Logger

if __name__ == "__main__":
	logger = Logger()
	for _ in range(1000):
		game = Game(logger)
		game.play()
		
	# print logger
	print logger.distribution_of_points()
	print logger.average_points_per_hand()