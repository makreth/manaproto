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

class CardSlot:

    class CardStates(Enum):

        INACTIVE = 0
        DOWN_LOCKED = 1
        DOWN_PLAYABLE = 2
        UP = 3
        TAP = 4

    CMD_ALIASES = {
        "cast" : 2,
        "set" : 1,
        "tap" : 3 
    }

    def __init__(self, id, index):
        self.side_id = id
        self.index = index
        self.card_name = None
        self.form = self.CardStates.INACTIVE
    
    def pop(self):
        res = self.card_name
        self.card_name = None
        self.form = self.CardStates.INACTIVE
        return res
    
    @classmethod
    def convert_cmd_type_to_card_state(cls, cmd_type):
        return cls.CMD_ALIASES[cmd_type]

    @property
    def card_name(self):
        return self._card_name

    @property
    def form(self):
        return self._form
    
    @card_name.setter
    def card_name(self, content_form_tuple):
        if not content_form_tuple:
            self._card_name = None
            self.form = self.CardStates.INACTIVE
        else:
            self._card_name, self.form = content_form_tuple
    
    @form.setter
    def form(self, new_state):
        self._form = new_state
    
    def __eq__(self, other):
        return self._card_name == other

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
    def __init__(self, id):
        self.token_group = TokenGroup()
        self.side_id = id
        self.slots = [CardSlot(id, 0), CardSlot(id, 1), CardSlot(id, 2), CardSlot(id, 3)]
        self.deck = []
        self.hand = []
        self.discard = []
    
    def apply_discard_state(self, num_cards, call_on_discard_choice=None):
        assert call_on_discard_choice != None, "Callback function must not be None."
        if len(self.hand) > num_cards:
            call_on_discard_choice()
            return True
        if len(self.hand) == num_cards:
            self.discard_all()
            return True
        else:
            return False
        
    def discard_indices(self, hand_indices):
        discarded = [self.hand.pop(ind) for ind in hand_indices]
        self.discard += discarded
        
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
    
    class CardSelector:

        POSSIBLE_SECTIONS = ["hand", "slot"]

        def __init__(self, id, section, index):
            self.player_id = id
            self.section = section
            self.index = index

            assert id == 0 or id == 1
            assert section in self.POSSIBLE_SECTIONS

        
    MAX_HAND_SIZE = 3
    STARTING_DRAW = 3
    STARTING_RESERVE = 10

    def __init__(self):
        self.players = [None, None]
        self.token_group = TokenGroup()
        self.turn = 0
        self.reserve = self.STARTING_RESERVE
        self.receiving_context = None
        self.casting_queue = []

        rc = self.ReceivingContexts
        self.context_processing = {
            rc.ACTIVE_PLAYER_START_DISCARD : self.execute_start_discard_on_active,
            rc.ACTIVE_PLAYER_FREE_FIELD : self.execute_active_play,
            rc.OPPOSING_PLAYER_RESPONSE : self.execute_opp_response,
        }

    def process_payload(self, string_payload):
        dict_payload = json.loads(string_payload)
        self.context_processing[self.receiving_context](**dict_payload)
    
    def resolve_card_selectors(self, start_selector, end_selector, type):
        target_player = self.players[start_selector.id]
        if start_selector.section == "hand":
            card_to_play = target_player.hand.pop(start_selector.index)

        if start_selector.section == "slot":
            target_slot = target_player.slots[start_selector.index]
            card_to_play = target_slot.pop()
        
        dest_slot = target_player.slots[end_selector.index]
        form = CardSlot.convert_cmd_type_to_card_state(type)
        dest_slot.card_name = card_to_play, form
        return dest_slot
    
    def play_card(self, start, end, type):
        start_selector = self.CardSelector(**start)
        end_selector = self.CardSelector(**end)
        dest_slot = self.resolve_card_selectors(start_selector, end_selector, type)
        if type == "cast":
            self.casting_queue.append(dest_slot)
            self.await_opposing_response()

    #TODO: more payload validation
    def execute_active_play(self, start=None, end=None, type=None):
        self.play_card(start, end, type)
    
    def execute_opp_response(self, start=None, end=None, type=None):
        self.play_card(start, end, type)
    
    def execute_start_discard_on_active(self, indices=None):
        acting_player = self.get_active_player()
        assert len(indices) <= len(acting_player.hand) - self.MAX_HAND_SIZE
        acting_player.discard_indices(indices)
    
    def start_turn(self):
        acting_player = self.get_active_player()
        player_lost = not(
            acting_player.apply_discard_state(GameField.MAX_HAND_SIZE, call_on_discard_choice = self.await_start_discard_choices) 
            or 
            acting_player.draw(GameField.STARTING_DRAW - len(acting_player.hand))
        )
        if player_lost:
            self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_LOST
        elif self.receiving_context != self.ReceivingContexts.ACTIVE_PLAYER_START_DISCARD:
            self.await_play()
    
    def await_start_discard_choices(self):
        self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_START_DISCARD
    
    def await_play(self):
        self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_FREE_FIELD
    
    def await_opposing_response(self):
        if self.receiving_context == self.ReceivingContexts.ACTIVE_PLAYER_FREE_FIELD or self.receiving_context == self.ReceivingContexts.ACTIVE_PLAYER_RESPONSE:
            self.receiving_context = self.ReceivingContexts.OPPOSING_PLAYER_RESPONSE
        elif self.receiving_context == self.ReceivingContexts.OPPOSING_PLAYER_RESPONSE:
            self.receiving_context == self.receiving_context.ACTIVE_PLAYER_RESPONSE
    
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
        new_player_field = PlayerField(profile_num)
        deck_list = target_profile.deck_list
        for card_name in deck_list.get_names():
            for _ in range(deck_list.get_count_from_name(card_name)):
                new_player_field.deck.append(card_name)
        self.field.players[profile_num] = new_player_field

class PlayerProfile:
    def __init__(self):
        self.name = ""
        self.deck_list = DeckList()

