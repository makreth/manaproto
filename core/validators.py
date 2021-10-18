from .exceptions import DiscardTooFewException, DiscardTooManyException

def validate_discard(player_field, indices):
    leftover = len(player_field.hand) - len(indices)
    if leftover < 3:
        raise DiscardTooManyException()
    if leftover > 3:
        raise DiscardTooFewException()

from .exceptions import MissingPayloadKeys

def validate_payload_dict(payload_dict, key_set):
    missing = [k for k in payload_dict.keys() if k not in key_set]
    if len(missing) > 0:
        raise MissingPayloadKeys(missing)

selector_keys = {"id", "section", "index"}
def validate_selector(selector_dict):
    validate_payload_dict(selector_dict, selector_keys)
