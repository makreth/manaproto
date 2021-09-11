from random import randint
from enum import Enum

class GameField:

    class ReceivingContexts(Enum):
        ACTIVE_PLAYER_START_DISCARD = 1
        ACTIVE_PLAYER_LOST = 99
    
    MAX_HAND_SIZE = 3
    STARTING_DRAW = 3

    def __init__(self):
        self.players = []
        self.token_group = TokenGroup()
        self.turn = 0
        self.receiving_context = None
    
    def start_turn(self):
        acting_player = self.get_active_player()
        player_lost = not(
            acting_player.discard_down_to(GameField.MAX_HAND_SIZE, await_callback = self.await_discard_choices) 
            or 
            acting_player.draw(GameField.STARTING_DRAW)
        )
        if player_lost:
            self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_LOST
        else:
            pass
    
    def await_discard_choices(self):
        self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_START_DISCARD
    
    def get_active_player(self):
        return self.players[self.turn]
    
    def get_inactive_player(self):
        return self.players[abs(self.turn - 1)]
    
    def set_players(self, player_list):
        self.players = player_list
    
    def choose_first_player(self):
        self.turn = randint(0,1)
    
class PlayerProfile:
    def __init__(self):
        self.name = ""
        self.deck_list = DeckList()

class PlayerField:
    def __init__(self):
        self.player_profile = None
        self.token_group = TokenGroup()
        self.play_slots = []
        self.deck = []
        self.hand = []
        self.discard = []
    
    def discard_down_to(self, num_cards, await_callback=None):
        assert await_callback != None, "Callback function must not be None."
        if len(self.hand) > num_cards:
            await_callback()
            return True
        if len(self.hand) == num_cards:
            self.discard_all()
            return True
        else:
            return False
        
    def discard_all(self):
        self.discard += self.hand
        self.hand.clear()
        
    def draw(self, num_cards):
        for _ in range(num_cards):
            try:
                curr_card = self.deck.pop()
            except IndexError:
                return False
            self.hand.append(curr_card)
        return True

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
    def __init__(self, aer=0, gaia=0, hydro=0, ignis=0):
        self.aer = 0
        self.gaia = 0
        self.hydro = 0
        self.ignis = 0
    
    def __iter__(self):
        return (elem for elem in tuple(self.aer, self.gaia, self.hydro, self.ignis))