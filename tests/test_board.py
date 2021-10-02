from core.game import Game, GameField, PlayerField, PlayerProfile, DeckList, TokenGroup
import pytest

class TestBoard:

    def test_profile_smoke(self):
        test_profile = PlayerProfile()

    def test_player_field_smoke(self):
        test_player_field = PlayerField()

    def test_board_smoke(self):
        test_field = GameField()
        assert test_field.players == []
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