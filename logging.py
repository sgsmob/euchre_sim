from card import Hand

class Logger:
	class Log:
		def __init__(self, curr_data):
			def hand_power_tuple(hand):
				return tuple(reversed(sorted(card.power for card in hand.view(curr_data["suit"]))))
				
			self.power_hand_tuple = [hand_power_tuple(h) for h in curr_data["hands"]]
			self.hand_str = ", ".join(str(h) for h in curr_data["hands"])
			self.caller = curr_data["caller"]
			self.up_card = curr_data["up_card"]
			self.score = curr_data["score"]
			self.called_suit = curr_data["suit"]
			caller_made = ((curr_data["winning_team"] % 2) == (curr_data["caller"] % 2))
			if not caller_made:
				self.score = self.score * -1
				
		def __str__(self):
			return "{} : {} {} ({}) -> {}".format(self.hand_str, self.caller, self.called_suit, self.up_card, self.score)

	def __init__(self):
		self.logs = []
		self.curr_data = None
		
	def __str__(self):
		return "\n".join(str(L) for L in self.logs)
	
	'''
	Normalizes the position indicated by player such that the left of the
	dealer is at position 0 and the dealer is at position 3.
	'''
	@staticmethod
	def offset(player, dealer):
		return (player - dealer + 3) % 4
	
	def init_log(self, dealer_pos):
		self.curr_data = {}
		self.curr_data["dealer_pos"] = dealer_pos
		self.curr_data["hands"] = [None, None, None, None]

	def log_hand(self, player):
		self.curr_data["hands"][self.offset(player.pos, self.curr_data["dealer_pos"])] = Hand([x for x in player.hand])
		
	def log_up_card(self, up_card):
		self.curr_data["up_card"] = up_card
		
	def log_bid(self, player, suit):
		self.curr_data["suit"] = suit
		self.curr_data["caller"] = self.offset(player.pos, self.curr_data["dealer_pos"])
	
	def log_score(self, team, points_gained):
		self.curr_data["winning_team"] = self.offset(team, self.curr_data["dealer_pos"])
		self.curr_data["score"] = points_gained
	
	def commit_log(self):
		self.logs.append(Logger.Log(self.curr_data))
		self.curr_data = {}