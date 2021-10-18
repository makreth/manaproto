class BaseBoardException(Exception):
    def __init__(self, message="BaseBoardException raised."):
        super().__init__(message)
    
    def __str__(self):
        return self.message

class MissingPayloadKeys(BaseBoardException):
    def __init__(self, missing_keys):
        super().__init__(self, message=f"Payload rejected: payload is missing the following: {missing_keys}")

class PlayerOutOfTurnException(BaseBoardException):
    def __init__(self):
        super().__init__("Payload rejected: player sending command cannot currently act.")

class DiscardTooManyException(BaseBoardException):
    def __init__(self):
        super().__init__("Payload rejected: too many indices for discard.")

class DiscardTooFewException(BaseBoardException):
    def __init__(self):
        super().__init__("Discard incomplete: too few indices submitted.")

class SlowActiveCardSpeedException(BaseBoardException):
    def __init__(self, card_name):
        super().__init__(f"{card_name} cannot be chain-casted during turn; card must either be set a turn before or spell speed must be Quick.")

class SlowOpposingCardSpeedException(BaseBoardException):
    def __init__(self, card_name):
        super().__init__(f"{card_name} cannot be chain-casted out of turn; card spell speed must be Quick.")

class AttemptedCastOfLockedSetCardException(BaseBoardException):
    def __init__(self, card_name):
        super().__init__(f"{card_name} cannot be casted the turn it was set.")