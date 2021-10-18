from .exceptions import DiscardTooFewException, DiscardTooManyException

def validate_discard(player_field, indices):
    leftover = len(player_field.hand) - len(indices)
    if leftover < 3:
        raise DiscardTooManyException()
    if leftover > 3:
        raise DiscardTooFewException()