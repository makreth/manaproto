from random import randint
from enum import Enum
import json

class TokenGroup:
    def __init__(self, aer=0, gaia=0, hydro=0, ignis=0):
        self.aer = 0
        self.gaia = 0
        self.hydro = 0
        self.ignis = 0
    
    def __eq__(self, other):
        return (self.aer, self.gaia, self.hydro, self.ignis) == (other.aer, other.gaia, other.hydro, other.ignis)
    
    def __iter__(self):
        return (elem for elem in tuple(self.aer, self.gaia, self.hydro, self.ignis))

class DeckList:
    def __init__(self, init_data = None):
        if init_data:
            self._data = init_data
        else:
            self._data = dict()

    def insert_name_count_pair(self, card_name, count):
        self._data[card_name] = count
    
    def get_count_from_name(self, card_name):
        return self._data[card_name]
    
    def get_names(self):
        return list(self._data.keys())

class PlayerField:
    def __init__(self):
        self.token_group = TokenGroup()
        self.play_slots = []
        self.deck = []
        self.hand = []
        self.discard = []
    
    def discard_down_to(self, num_cards, call_on_discard_choice=None):
        assert call_on_discard_choice != None, "Callback function must not be None."
        if len(self.hand) > num_cards:
            call_on_discard_choice()
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
                curr_card = self.deck.pop(0)
            except IndexError:
                return False
            self.hand.append(curr_card)
        return True

class GameField:
    class ReceivingContexts(Enum):
        ACTIVE_PLAYER_FREE_FIELD = 1
        OPPOSING_PLAYER_RESPONSE = 2
        ACTIVE_PLAYER_RESPONSE = 3
        ACTIVE_PLAYER_START_DISCARD = 4
        OPPOSING_PLAYER_LOST = 98
        ACTIVE_PLAYER_LOST = 99
    
    MAX_HAND_SIZE = 3
    STARTING_DRAW = 3

    def __init__(self):
        self.players = [None, None]
        self.token_group = TokenGroup()
        self.turn = 0
        self.receiving_context = None

        rc = self.ReceivingContexts
        self.context_processing = {
            rc.ACTIVE_PLAYER_START_DISCARD : self.execute_start_discard_on_active
        }

    def process_payload(self, string_payload):
        dict_payload = json.loads(string_payload)
        self.context_processing[self.receiving_context](dict_payload)

    def execute_start_discard_on_active(self, payload):
        hand_indices = payload["indices"]
        acting_player = self.get_active_player()
        discarded = [acting_player.hand.pop(ind) for ind in hand_indices]
        acting_player.discard += discarded
    
    def start_turn(self):
        acting_player = self.get_active_player()
        player_lost = not(
            acting_player.discard_down_to(GameField.MAX_HAND_SIZE, call_on_discard_choice = self.await_discard_choices) 
            or 
            acting_player.draw(GameField.STARTING_DRAW)
        )
        if player_lost:
            self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_LOST
        elif self.receiving_context != self.ReceivingContexts.ACTIVE_PLAYER_START_DISCARD:
            self.await_play()
    
    def await_discard_choices(self):
        self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_START_DISCARD
    
    def await_play(self):
        self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_FREE_FIELD
    
    def get_active_player(self):
        return self.players[self.turn]
    
    def get_inactive_player(self):
        return self.players[abs(self.turn - 1)]
    
    def choose_first_player(self):
        self.turn = randint(0,1)

class Game:

    def __init__(self):
        self.profiles = []
        self.field = GameField()
    
    def set_profiles(self, profile_list):
        self.profiles = profile_list
    
    def setup_players_from_profiles(self):
        self.setup_player(0)
        self.setup_player(1)

    def setup_player(self, profile_num):
        target_profile = self.profiles[profile_num]
        new_player_field = PlayerField()
        deck_list = target_profile.deck_list
        for card_name in deck_list.get_names():
            for _ in range(deck_list.get_count_from_name(card_name)):
                new_player_field.deck.append(card_name)
        self.field.players[profile_num] = new_player_field

class PlayerProfile:
    def __init__(self):
        self.name = ""
        self.deck_list = DeckList()

