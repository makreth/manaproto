from random import randint
from enum import Enum
import json

from . import exceptions
from .components import TokenGroup, CardSlot
from .profile import PlayerProfile, DeckList
from .validators import validate_discard, validate_payload_dict, validate_card_selector


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
        discarded = []
        invalid = []
        no_mod = False
        for ind in hand_indices:
            try:
                num_ind = int(ind)
                if num_ind < 0:
                    raise IndexError
                _ = self.hand[num_ind]
                if not no_mod:
                    discarded.append(self.hand.pop(num_ind))
            except(ValueError, IndexError):
                no_mod = True
                invalid.append(ind)
        if len(invalid) > 0:
            raise exceptions.DiscardIndicesInvalidException(invalid)
        else:
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

    DEBUG_SYMBOL_NO_EXCEPTION_HANDLING = False

    class ReceivingContexts(Enum):
        ACTIVE_PLAYER_FREE_FIELD = 1
        OPPOSING_PLAYER_RESPONSE = 2
        ACTIVE_PLAYER_RESPONSE = 3
        ACTIVE_PLAYER_START_DISCARD = 4
        OPPOSING_PLAYER_LOST = 98
        ACTIVE_PLAYER_LOST = 99

    KEYS_BY_CONTEXT = {
        ReceivingContexts.ACTIVE_PLAYER_START_DISCARD : {"indices"},
        ReceivingContexts.ACTIVE_PLAYER_FREE_FIELD : {"start", "end", "type"},
        ReceivingContexts.ACTIVE_PLAYER_RESPONSE : {"start", "end", "type"}
    }
    
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
    
    def execute_active_play(self, start=None, end=None, type=None):
        [validate_card_selector(sel) for sel in (start, end)]
        for id_ in (start["id"], end["id"]):
            if id_ != self.turn:
                raise exceptions.PlayerOutOfTurnException(id_)
        self.play_card(start, end, type)
    
    def execute_opp_response(self, start=None, end=None, type=None):
        [validate_card_selector(sel) for sel in (start, end)]
        for id_ in (start["id"], end["id"]):
            if id_ == self.turn:
                raise exceptions.PlayerOutOfTurnException(id_)
        self.play_card(start, end, type)
    
    def execute_start_discard_on_active(self, indices=None):
        acting_player = self.get_active_player()
        try:
            validate_discard(acting_player, indices)
            acting_player.discard_indices(indices)
            self.await_play()
        except exceptions.DiscardTooFewException as e:
            acting_player.discard_indices(indices)
            raise e

    def process_payload(self, string_payload):
        dict_payload = json.loads(string_payload)
        try:
            validate_payload_dict(dict_payload, self.KEYS_BY_CONTEXT[self.receiving_context])
            self.context_processing[self.receiving_context](**dict_payload)
        except exceptions.BaseBoardException as e:
            if self.DEBUG_SYMBOL_NO_EXCEPTION_HANDLING:
                raise e
            else:
                print("BaseBoardException handled.")
    
    def resolve_card_selectors(self, start_selector, end_selector, type):
        target_player = self.players[start_selector.player_id]
        if start_selector.section == "hand":
            card_to_play = target_player.hand.pop(start_selector.index)

        if start_selector.section == "slot":
            target_slot = target_player.slots[start_selector.index]
            card_to_play = target_slot.pop()
        
        dest_slot = target_player.slots[end_selector.index]
        form = CardSlot.convert_cmd_type_to_card_state(type)
        dest_slot.card_name = card_to_play
        dest_slot.form = form
        return dest_slot
    
    def play_card(self, start, end, type):
        start_selector = self.CardSelector(**start)
        end_selector = self.CardSelector(**end)
        dest_slot = self.resolve_card_selectors(start_selector, end_selector, type)
        if type == "cast":
            self.casting_queue.append(dest_slot)
            self.await_opposing_response()
    
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
            self.receiving_context = self.ReceivingContexts.ACTIVE_PLAYER_RESPONSE
    
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