class PlayerProfile:
    def __init__(self):
        self.name = ""
        self.deck_list = DeckList()

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