from enum import Enum, auto


class Action(Enum):
    NONE = auto()
    TRADE = auto()
    GET_TRADES = auto()
    GET_PNL = auto()
    GET_DAILY_PNL = auto()
