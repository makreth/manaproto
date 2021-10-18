from enum import Enum

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
        SLOW = 5

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
            self._card_name = content_form_tuple
    
    @form.setter
    def form(self, new_state):
        self._form = new_state
    
    def __eq__(self, other):
        return self._card_name == other