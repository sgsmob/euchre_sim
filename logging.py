from collections import defaultdict
from card import Card, Hand
import itertools

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
		return "\n".join(str(L) for L in self)
		
	def __iter__(self):
		return iter(self.logs)

	def __len__(self):
		return len(self.logs)
	
	@staticmethod
	def offset(player, dealer):
		'''
		Normalizes the position indicated by player such that the left of the
		dealer is at position 0 and the dealer is at position 3.
		'''
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

	'''
	Analysis functions
	'''

	def distribution_of_points(self):
		counts = defaultdict(int)
		for log in self:
			counts[log.score] += 1
		return counts
		
	def average_points_per_hand(self):
		dist = self.distribution_of_points()
		total_points = 0
		total_hands = 0
		for points, hands in dist.items():
			total_points += points * hands
			total_hands += hands
		return float(total_points) / total_hands
		
	def top_tuples(self, k):
		counter = defaultdict(int)
		score_sum = defaultdict(float)
		for log in self:
			hand = log.power_hand_tuple[log.caller]
			hand_str = " ".join([Card.power_to_str[i] for i in hand])
			counter[hand_str] += 1
			score_sum[hand_str] += log.score
		print len(counter), "unique hands"
		first_k_above_0 = [(None, 1) for _ in range(k)]
		first_k_below_0 = [(None, -1) for _ in range(k)]
		for hand, c in counter.iteritems():
			expected_pts = score_sum[hand] / c
			for i in range(k):
				if expected_pts > 0 and expected_pts < first_k_above_0[i][1]:
					first_k_above_0.insert(i, (hand, expected_pts))
					first_k_above_0.pop()
					break
				elif expected_pts < 0 and expected_pts > first_k_below_0[i][1]:
					first_k_below_0.insert(i, (hand, expected_pts))
					first_k_below_0.pop()
					break
		return itertools.chain(first_k_above_0, first_k_below_0)