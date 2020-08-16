import random
from collections import defaultdict

class Card:
	suit_enum = {"C": 1, "S": 2, "D": 4, "H": 8}
	rank_enum = {"9": 0, "X": 1, "J": 2, "Q":3, "K":4, "A":5}
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
			power_level += 6
			if self.rank == "J":
				power_level += 3
				if self.suit == trump_suit:
					power_level += 1
			elif self.rank == "Q" or self.rank == "K" or self.rank == "A":
				power_level -= 1
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
		return list(sorted((CardView(card, i, trump_suit)
			for i, card in enumerate(self.raw_cards)), key=lambda x: x.power))

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
	
	def decide_to_call(self, up_card, dealer_pos, choose_suit):
		'''
		Determine whether to call trump given the displayed card and the
		position of the dealer.
		
		If `choose_suit` is False, the player chooses any suit not matching
		`card` to be trump or pass if they so choose.  The dealer may not
		pass.
		
		Returns the suit called or None when passing.
		'''
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
	
	def play_card(self, hand_state):
		card_pos = self.card_to_play_position(hand_state)
		print self, self.hand[card_pos]
		card = self.hand.play(card_pos)
		hand_state.add_played_card(card)
	
	def card_to_play_position(self, hand_state):
		'''
		Selects the position of the card to play in this turn.
		'''
		# Early out when there is no decision to make.
		if len(self.hand) == 1:
			return 0

		is_on_bidding_team = (self.team == hand_state.bid.bidding_team())
		trick_state = hand_state.trick_state
		trump = trick_state.trump_suit
		hand_view = self.hand.view(trump)
		
		def highest_non_trump_pos():
			'''
			Returns the position of the most powerful trump card in hand_view
			or 0 if all cards are trump.
			'''
			for card in reversed(hand_view):
				if not card.is_trump(trump):
					return card.pos
			return 0

		if trick_state.cards_in_play:
			cards_in_led_suit = filter(lambda x: x.suit == trick_state.suit_led, hand_view)
			winning_pos, winning_card = trick_state.current_winning_card()
			partner_is_leading = (len(trick_state.cards_in_play) % 2 == winning_pos % 2)
			# Don't overplay partner if possible.
			if partner_is_leading:
				if cards_in_led_suit:
					return cards_in_led_suit[0].pos
				else:
					return hand_view[0].pos					
			else:
				if cards_in_led_suit:
					# Play lowest card that can win in suit.
					for card in cards_in_led_suit:
						if card.power > winning_card.power:
							return card.pos
					# Otherwise, there are no winners and we should throw away our worst card.
					return cards_in_led_suit[0].pos
				else:
					trump_cards = filter(lambda x: x.suit == trump, hand_view)
					# Play lowest trump card that can win.
					for card in trump_cards:
						if card.power > winning_card.power:
							return card.pos
					# Otherwise, there are no winners and we should throw away our worst card.
					return hand_view[0].pos		
		else:
			# Lead a high card when you called.
			if is_on_bidding_team:
				best_card = hand_view[-1]
				# Lead the highest trump card if you have it.
				if best_card.is_trump(trump) and max(hand_state.unseen_trump_power) == best_card.power:
					return best_card.pos
				else:
					return highest_non_trump_pos()
			# Lead highest non-trump if you didn't call.
			else:
				return highest_non_trump_pos()


class HandState:
	'''
	Class to keep track of the state of the current hand, such as who dealt
	and which cards have been played.
	'''
	class TrickState:
		'''
		Class to keep track of the state of the current trick, such as who
		lead and who is winning.
		'''
		def __init__(self, leader, trump_suit):
			self.suit_led = None
			self.cards_in_play = []
			self.leader = leader
			self.trump_suit = trump_suit

		def current_winning_card(self):
			valid_cards = filter(lambda x: (x[1].suit == self.trump_suit or x[1].suit == self.suit_led),
				enumerate(self.cards_in_play))
			return max(valid_cards, key=lambda x: x[1].power)

		def add_played_card(self, card):
			if not self.cards_in_play:
				self.suit_led = card.suit
			self.cards_in_play.append(CardView(card, -1, self.trump_suit))

	def __init__(self, bid, dealer_pos):
		self.tricks = [0, 0]
		self.bid = bid
		self.dealer_pos = dealer_pos
		self.unseen_cards = set(str(c) for c in Card.deck())
		self.unseen_trump_power = set(i for i in range(6, 13))
		self.trick_state = self.TrickState((dealer_pos + 1) % 4, self.bid.trump_suit)
			
	def end_trick(self):
		winner_relative_pos, _ = self.trick_state.current_winning_card()
		next_leader = (self.trick_state.leader + winner_relative_pos) % 4
		self.tricks[next_leader % 2] += 1
		self.trick_state = self.TrickState(next_leader, self.bid.trump_suit)
		
	def add_played_card(self, card):
		self.trick_state.add_played_card(card)
		self.unseen_cards.remove(str(card))
		if card.is_trump(self.bid.trump_suit):
			self.unseen_trump_power.remove(card.power(self.bid.trump_suit))


class Bid:
	def __init__(self, player, suit):
		self.player = player
		self.trump_suit = suit
		
	def bidding_team(self):
		return self.player.team

	def score(self, tricks):
		'''Returns change in score the team who scored points this round.'''
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

		hand_state = HandState(bid, self.dealer_pos)
		for _ in range(5):
			self.play_trick(hand_state)
		
		self.update_score(hand_state.tricks, bid)
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
		
	def play_trick(self, hand_state):
		for player in self.turn_order(hand_state.trick_state.leader):
			player.play_card(hand_state)
		hand_state.end_trick()
		
	def update_score(self, tricks, bid):
		team, points_gained = bid.score(tricks)
		self.score[team] += points_gained
		self.logger.log_score(team, points_gained)
		