from core.game import Game, GameField, PlayerField, PlayerProfile, DeckList, TokenGroup
import json
import pytest

class TestBoard:

    def test_profile_smoke(self):
        test_profile = PlayerProfile()

    def test_player_field_smoke(self):
        test_player_field = PlayerField()

    def test_board_smoke(self):
        test_field = GameField()
        assert test_field.players == [None, None]
        assert test_field.token_group == TokenGroup()
        assert test_field.turn == 0
        assert test_field.receiving_context == None
    
    @staticmethod
    def setup_profile(name, card_dict):
        p_profile = PlayerProfile()
        p_profile.name = name
        p_profile.deck_list = DeckList(card_dict)
        return p_profile

    def setup_game(self, p1_args, p2_args):
        profiles = [self.setup_profile(*args) for args in (p1_args, p2_args)]
        game = Game()
        game.set_profiles(profiles)
        game.setup_players_from_profiles()
        return game
    
    def test_game_deck_smoke(self):
        p1_dict = [
            "p1",
            {
                "a1": 2,
                "a2": 1 
            }
        ]
        p2_dict = [
            "p2",
            {
                "b1":2,
                "b2":1
            }
        ]
        game = self.setup_game(p1_dict, p2_dict)
        assert len(game.field.players) == 2
        assert game.field.players[0].deck == ["a1", "a1", "a2"]
        assert game.field.players[1].deck == ["b1", "b1", "b2"]
    
    def test_active_draw_smoke(self):
        p1_dict = [
            "p1",
            {
                "1a":2,
                "1b":2
            }
        ]
        p2_dict = [
            "p2",
            {
                "2a":2,
                "2b":2
            }
        ]
        field = self.setup_game(p1_dict, p2_dict).field
        field.start_turn()
        assert len(field.players[0].hand) == 3
        assert field.players[0].hand == ["1a", "1a", "1b"]
        assert field.players[0].deck == ["1b"]

        assert len(field.players[1].hand) == 0
        assert field.players[1].deck == ["2a","2a","2b","2b"]

    def test_start_discard_smoke(self):
        p1_dict = [
            "p1",{}
        ]
        p2_dict = [
            "p2",{}
        ]
        field = self.setup_game(p1_dict, p2_dict).field
        field.players[0].hand = ["d1", "d2", "d3", "d4"]
        field.start_turn()
        assert field.receiving_context == GameField.ReceivingContexts.ACTIVE_PLAYER_START_DISCARD
        field.process_payload(json.dumps({"indices":[0]}))
        assert field.players[0].hand == ["d2", "d3", "d4"]
        assert field.players[0].discard == ["d1"]
    
    def test_active_loss_smoke(self):
        p1_dict = [
            "p1",{}
        ]
        p2_dict = [
            "p2",{}
        ]
        field = self.setup_game(p1_dict, p2_dict).field
        field.start_turn()
        assert field.receiving_context == GameField.ReceivingContexts.ACTIVE_PLAYER_LOST
    
    def test_active_play_card_smoke(self):
        p1_dict = [
            "p1",{
                "play1" : 1,
                "1a" : 2,
                "1b" : 2
            }
        ]

        p2_dict = [
            "p2",{
            }
        ]

        field = self.setup_game(p1_dict, p2_dict).field
        field.start_turn()
        assert field.receiving_context == GameField.ReceivingContexts.ACTIVE_PLAYER_FREE_FIELD
        field.process_payload(json.dumps({
            "start": {
                "id" : 0,
                "section" : "hand",
                "index" : 0
            },
            "end" : {
                "id" : 0,
                "section" : "slot",
                "index" : 1
            },
            "type" : "cast"
        }))
        assert len(field.players[0].hand) == 2
        assert field.players[0].hand == ["1a", "1a"]
        assert field.players[0].slots[1] == "play1"