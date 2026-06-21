import random
import json
import os


class Player:
    def __init__(self, name):
        self._name = name
        self._is_my_turn = False
        self.hp = 10
        self.hand = []
        self.deck = []
        self.mana_deck = 10
        self.mana_pool = 0
        self.mana_max = 0
        self.defense_active = 0
        self.is_first_turn = True  # <--- NOVA FLAG PARA O BALANCEAMENTO

        self._load_deck()

    def _load_deck(self):
        path = os.path.join("data", "cards.json")
        with open(path, "r", encoding="utf-8") as f:
            all_cards = json.load(f)

        self.deck = random.sample(all_cards, 20)
        random.shuffle(self.deck)

        for _ in range(3):
            self.draw_card()

    @property
    def name(self):
        return self._name

    @property
    def is_my_turn(self):
        return self._is_my_turn

    def set_turn(self, state):
        self._is_my_turn = state

    def draw_card(self):
        if self.deck:
            self.hand.append(self.deck.pop(0))
            return True
        return False

    def draw_mana(self):
        if self.mana_deck > 0:
            self.mana_deck -= 1
            self.mana_max += 1
            self.mana_pool = self.mana_max
            return True
        return False