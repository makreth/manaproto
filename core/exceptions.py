class BaseBoardException(Exception):
    def __init__(self, message="BaseBoardException raised."):
        super().__init__(message)
    
    def __str__(self):
        return self.message

class PlayerOutOfTurnException(Exception):
    def __init__(self):
        super().__init__("Payload rejected: player sending command cannot currently act.")

class DiscardTooManyException(Exception):
    def __init__(self):
        super().__init__("Payload rejected: too many indices for discard.")

class DiscardTooFewException(Exception):
    def __init__(self):
        super().__init__("Discard incomplete: too few indices submitted.")

class SlowActiveCardSpeedException(Exception):
    def __init__(self, card_name):
        super().__init__(f"{card_name} cannot be chain-casted during turn; card must either be set a turn before or spell speed must be Quick.")

class SlowOpposingCardSpeedException(Exception):
    def __init__(self, card_name):
        super().__init__(f"{card_name} cannot be chain-casted out of turn; card spell speed must be Quick.")

class AttemptedCastOfLockedSetCardException(Exception):
    def __init__(self, card_name):
        super().__init__(f"{card_name} cannot be casted the turn it was set.")