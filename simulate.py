from card import Game
from logging import Logger

if __name__ == "__main__":
	logger = Logger()
	for _ in range(10000):
		game = Game(logger)
		game.play()
		
	# print logger
	print logger.distribution_of_points()
	print logger.average_points_per_hand()
	for hand_power_tuple, score in logger.top_tuples(10):
		print hand_power_tuple, "\t", score