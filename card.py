import random
from collections import defaultdict

class Card:
	suit_enum = {"C": 1, "S": 2, "D": 4, "H": 8}
	rank_enum = {"9": 1, "X": 2, "J": 3, "Q":4, "K":5, "A":6}
	same_color = {"C": "S", "S": "C", "D": "H", "H": "D"}

	@classmethod
	def suit_to_int(cls, suit):
		return cls.suit_enum[suit]

	@classmethod
	def deck(cls):
		for suit in cls.suit_enum.keys():
			for rank in cls.rank_enum.keys():
				yield cls(suit, rank)
	
	@classmethod
	def suits(cls):
		return cls.suit_enum.keys()
		
	@classmethod
	def trump_cards(cls, suit):
		cards = [Card(suit, "J"), Card(cls.same_color[suit], "J")]
		for rank, _ in sorted(cls.rank_enum.items(), key=lambda x: x[1]):
			if rank != "J":
				cards.append(Card(suit, rank))
		return cards		

	def __init__(self, suit, rank):
		self.suit = suit
		self.rank = rank

	def __str__(self):
		return self.rank + self.suit
		
	def __eq__(self, other):
		return self.suit == other.suit and self.rank == other.rank

	def __ne__(self, other):
		return (not (self == other))
				
	def __lt__(self, other):
		return self.as_tuple() < other.as_tuple()

	def __le__(self, other):
		return self.as_tuple() <= other.as_tuple()

	def __gt__(self, other):
		return self.as_tuple() > other.as_tuple()

	def __ge__(self, other):
		return self.as_tuple() >= other.as_tuple()

	def is_trump(self, trump_suit):
		if trump_suit == self.suit:
			return True
		elif self.rank == "J" and self.same_color[self.suit] == trump_suit:
			return True
		else:
			return False
	
	def power(self, trump_suit):
		power_level = self.rank_enum[self.rank]
		if self.is_trump(trump_suit):
			power_level += 7
			if self.rank == "J":
				power_level += 4
				if self.suit == trump_suit:
					power_level += 1
		return power_level
		
	def as_tuple(self):
		return (self.suit_enum[self.suit], self.rank_enum[self.rank])
	
	
class CardView:
	def __init__(self, card, pos, trump_suit):
		self.raw_suit = card.suit
		self.rank = card.rank
		self.pos = pos
		self.power = card.power(trump_suit)
		if card.is_trump(trump_suit):
			self.suit = trump_suit
		else:
			self.suit = self.raw_suit

	def __eq__(self, other):
		return self.raw_suit == other.raw_suit and self.rank == other.rank

	def __hash__(self):
		return hash(self.raw_suit + self.rank)
		
	def __str__(self):
		return self.rank + self.raw_suit
			
	def is_view_of(self, card):
		return self.raw_suit == card.suit and self.rank == card.rank
		
	def is_trump(self, trump_suit):
		return self.suit == trump_suit


class Hand:
	def __init__(self, cards):
		self.raw_cards = list(sorted(cards))
	
	def __getitem__(self, key):
		return self.raw_cards[key]
	
	def __str__(self):
		return "[" + ", ".join([str(card) for card in self.raw_cards]) + "]"
		
	def __len__(self):
		return len(self.raw_cards)
		
	def __iter__(self):
		return iter(self.raw_cards)

	def view(self, trump_suit):
		return list(sorted((CardView(card, i, trump_suit) for i, card in enumerate(self.raw_cards)), key=lambda x: x.power))

	def pick_up_card(self, up_card):
		worst_card = self.view(up_card.suit)[0]
		self.raw_cards[worst_card.pos] = up_card

	def play(self, pos):
		return self.raw_cards.pop(pos)

	
class Player:
	def __init__(self, pos):
		self.pos = pos
		self.team = pos % 2
		self.hand = None
		
	def __str__(self):
		return "Player {}: {}".format(self.pos, str(self.hand))
		
	def deal(self, hand):
		self.hand = hand
	
	'''
	Determine whether to call trump given the displayed card and the position
	of the dealer.
	
	If `choose_suit` is False, the player chooses any suit not matching `card`
	to be trump or pass if they so choose.  The dealer may not pass.
	
	Returns the suit called or None when passing.
	'''
	def decide_to_call(self, up_card, dealer_pos, choose_suit):
		if choose_suit:
			# Store the estimated number of winners and suit called.
			best = (0, None)
			for suit in Card.suits():
				if suit == up_card.suit:
					continue
				curr = (self.number_of_winners(suit, up_card, dealer_pos), suit)
				if curr > best:
					best = curr
			if best[0] >= 3 or self.pos == dealer_pos:
				return best[1]
		else:
			if self.number_of_winners(up_card.suit, up_card, dealer_pos) >= 3:
				return up_card.suit
		
		return None
			
	def number_of_winners(self, suit, up_card, dealer_pos):
		hand = Hand(self.hand.raw_cards)
		if self.pos == dealer_pos:
			hand.pick_up_card(up_card)
		hand_view = hand.view(suit)

		counters = defaultdict(int)
		suits_seen = set()
		for card in hand_view:
			if card.suit == suit:
				counters["trump"] += 1
			else:
				suits_seen.add(suit)
				if card.rank == "A":
					counters["side_ace"] += 1
		counters["off_suit_trump"] = len(suits_seen)
		# Don't bother doing other computation if we have no trump.
		if counters["trump"] == 0 or counters["off_suit_trump"] == counters["trump"]:
			return counters["side_ace"] + counters["trump"]

		all_trump_cards = Card.trump_cards(suit)
		# Assume that for each suit not in the hand, we can take a trick using a low trump.
		worst_trump_in_hand_idx = len(hand_view) - 1 - (counters["trump"] - counters["off_suit_trump"])
		best_trump_in_hand_idx = len(hand_view) - 1
		next_best_trump_idx = 0
		while next_best_trump_idx < len(all_trump_cards) and worst_trump_in_hand_idx <= best_trump_in_hand_idx:
			next_best_trump = all_trump_cards[next_best_trump_idx]
			if next_best_trump.power(suit) <= hand_view[best_trump_in_hand_idx].power:
				counters["trump_winners"] += 1
				best_trump_in_hand_idx -= 1
				next_best_trump_idx += 2
			else:
				worst_trump_in_hand_idx += 1
				next_best_trump_idx += 1
		return counters["side_ace"] + counters["trump_winners"] + counters["off_suit_trump"]
	

	def pick_up_card(self, up_card):
		self.hand.pick_up_card(up_card)
	
	def play_card(self, game_state):
		pos = self.card_to_play_position(game_state)
		print self, pos
		card = self.hand.play(pos)
		game_state.add_played_card(card)
	
	'''
	Selects the position of the card to play in this turn.
	'''
	def card_to_play_position(self, game_state):
		# Early out when there is no decision to make.
		if len(self.hand) == 1:
			return 0

		is_on_bidding_team = (self.team == game_state.bid.bidding_team())
		trump = game_state.bid.trump_suit
		hand = self.hand.view(trump)

		if game_state.cards_in_play:
			cards_in_led_suit = filter(lambda x: x.suit == game_state.suit_led, hand)
			winning_pos, winning_card = game_state.current_winning_card()
			partner_is_leading = (len(game_state.cards_in_play) % 2 == winning_pos % 2)
			# Don't overplay partner if possible.
			if partner_is_leading:
				if cards_in_led_suit:
					return cards_in_led_suit[0].pos
				else:
					return hand[0].pos					
			else:
				if cards_in_led_suit:
					# Play lowest card that can win in suit.
					for card in cards_in_led_suit:
						if card.power > winning_card.power:
							return card.pos
					# Otherwise, there are no winners and we should throw away our worst card.
					return cards_in_led_suit[0].pos
				else:
					trump_cards = filter(lambda x: x.suit == game_state.bid.trump_suit, hand)
					# Play lowest trump card that can win.
					for card in trump_cards:
						if card.power > winning_card.power:
							return card.pos
					# Otherwise, there are no winners and we should throw away our worst card.
					return hand[0].pos		
		else:
			# Lead highest card when you called.
			if is_on_bidding_team:
				return hand[-1].pos
			# Lead highest non-trump if you didn't call.
			else:
				for card in reversed(hand):
					if not card.is_trump(trump):
						return card.pos
				# Play the worst card if all you have left is trump
				return 0


class GameState:
	def __init__(self, bid, dealer_pos):
		self.tricks = [0, 0]
		self.bid = bid
		self.dealer_pos = dealer_pos
		self.leader = (dealer_pos + 1) % 4
		self.cards_in_play = []
		self.unseen_cards = set(str(c) for c in Card.deck())
		self.suit_led = None
	
	def current_winning_card(self):
		valid_cards = filter(lambda x: (x[1].suit == self.bid.trump_suit or x[1].suit == self.suit_led),
			enumerate(self.cards_in_play))
		return max(valid_cards, key=lambda x: x[1].power)
			
	def end_trick(self):
		winner_relative_pos, _ = self.current_winning_card()
		self.leader = (self.leader + winner_relative_pos) % 4
		self.tricks[self.leader % 2] += 1
		self.cards_in_play = []
		self.suit_led = None
		
	def add_played_card(self, card):
		if not self.cards_in_play:
			self.suit_led = card.suit
		self.cards_in_play.append(CardView(card, -1, self.bid.trump_suit))
		print card
		self.unseen_cards.remove(str(card))


class Bid:
	def __init__(self, player, suit):
		self.player = player
		self.trump_suit = suit
		
	def bidding_team(self):
		return self.player.team

	# Returns change in score the team who scored points this round.
	def score(self, tricks):
		print tricks
		bidding_tricks = tricks[self.player.team]
		if (bidding_tricks < 3):
			return ((self.bidding_team() + 1) % 2, 2)
		elif (bidding_tricks == 5):
			return self.bidding_team(), 2
		else:
			return self.bidding_team(), 1


class Game:
	def __init__(self, logger):
		self.logger = logger
		self.players = [Player(i) for i in range(4)]
		self.dealer_pos = 0
		self.deck = list(Card.deck())
		self.score = [0, 0]
		print [str(x) for x in sorted(self.deck)]
		
	def deal(self):
		shuffled_deck = [x for x in random.sample(self.deck, len(self.deck))]
		print [str(x) for x in shuffled_deck]
		for i, player in enumerate(self.players):
			cards = shuffled_deck[i * 5 : (i + 1) * 5]
			player.deal(Hand(cards))
			self.logger.log_hand(player)

		up_card = shuffled_deck[-1]
		self.logger.log_up_card(up_card)
		return up_card
		
	def turn_order(self, start_pos):
		for i in range(4):
			yield self.players[(start_pos + i) % 4]

	def play_hand(self):
		self.logger.init_log(self.dealer_pos)
		up_card = self.deal()
		bid = self.select_bid(up_card)

		game_state = GameState(bid, self.dealer_pos)
		for _ in range(5):
			self.play_trick(game_state)
		
		self.update_score(game_state.tricks, bid)
		self.logger.commit_log()
		
	def play(self):
		while (not self.has_winner()):
			self.play_hand()
			self.dealer_pos = (self.dealer_pos + 1) % 4
		return self.score
		
	def has_winner(self):
		return self.score[0] >= 10 or self.score[1] >= 10
		
	def select_bid(self, up_card):
		left_of_dealer = (self.dealer_pos + 1) % 4
		# Call up card
		for player in self.turn_order(left_of_dealer):
			if player.decide_to_call(up_card=up_card, dealer_pos=self.dealer_pos, choose_suit=False) is not None:
				self.players[self.dealer_pos].pick_up_card(up_card)
				self.logger.log_bid(player, up_card.suit)
				return Bid(player, up_card.suit)

		# Call without up card
		for player in self.turn_order(left_of_dealer):
			trump_suit = player.decide_to_call(up_card=up_card, dealer_pos=self.dealer_pos, choose_suit=True)
			if trump_suit is not None:
				self.logger.log_bid(player, trump_suit)
				return Bid(player, trump_suit)
				
		raise ValueError("Dealer needed to call trump on hand " + self.players[self.dealer_pos].hand)
		
	def play_trick(self, game_state):
		for player in self.turn_order(game_state.leader):
			player.play_card(game_state)
		game_state.end_trick()
		
	def update_score(self, tricks, bid):
		team, points_gained = bid.score(tricks)
		self.score[team] += points_gained
		self.logger.log_score(team, points_gained)
		