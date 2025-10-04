import random

RANKS = list(range(1, 14))
SUITS = ['S', 'H', 'D', 'C']

def rank(card):  # "7H" -> 7
    return int(card[:-1])

class StressGame:
    def __init__(self, room):
        self.room = room
        self.deck = [f"{r}{s}" for s in SUITS for r in RANKS]
        random.shuffle(self.deck)
        self.players = []
        self.hands = {}
        self.center = []
        self.active = False

    def add_player(self, user):
        if user not in self.players and len(self.players) < 2:
            self.players.append(user)
            self.hands[user] = []
        return len(self.players) <= 2

    def deal_if_ready(self):
        if self.active or len(self.players) < 2:
            return
        p1, p2 = self.players[:2]
        for _ in range(26):
            self.hands[p1].append(self.deck.pop())
            self.hands[p2].append(self.deck.pop())
        self.center = [self.deck.pop(), self.deck.pop()]
        self.active = True

    def can_play(self, card, pile_index):
        if not self.center or pile_index not in (0, 1):
            return False
        return abs(rank(card) - rank(self.center[pile_index])) == 1

    def play_card(self, user, card, pile_index):
        hand = self.hands.get(user, [])
        if card not in hand:
            return False
        if self.can_play(card, pile_index):
            hand.remove(card)
            self.center[pile_index] = card
            return True
        return False

    def draw_new_centers(self):
        if len(self.deck) >= 2:
            self.center = [self.deck.pop(), self.deck.pop()]
            return True
        return False

    def winner(self):
        if not self.active:
            return None
        for u, h in self.hands.items():
            if len(h) == 0:
                return u
        return None

    def state_for(self, user):
        return {
            "room": self.room,
            "players": self.players,
            "you": user,
            "your_hand": sorted(self.hands.get(user, []), key=lambda x: (rank(x), x[-1])),
            "opponent_count": sum(len(h) for u, h in self.hands.items() if u != user),
            "center": self.center,
            "deck_count": len(self.deck),
            "active": self.active,
            "winner": self.winner(),
        }
