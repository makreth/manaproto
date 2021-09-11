class GameField:
    def __init__(self):
        self.players = []
        self.token_group = TokenGroup()
        self.turn = 0

class PlayerProfile:
    def __init__(self):
        self.name = ""
        self.decklist = DeckList()

class PlayerField:
    def __init__(self):
        self.player_profile = None
        self.token_group = TokenGroup()
        self.play_slots = []
        self.deck = []
        self.hand = []
        self.discard = []

class DeckList:
    def __init__(self):
        self._data = dict()

    def insert_name_count_pair(self, card_name, count):
        self._data[card_name] = count
    
    def get_count_from_name(self, card_name):
        return self._data[card_name]
    
    def get_names(self):
        return list(self._data.keys())
    
class TokenGroup:
    pass