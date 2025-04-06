from enum import Enum, auto

from agent.request import Request


class OrderSide(Enum):
    BUY = auto()
    SELL = auto()

    def to_str(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, s: str) -> "OrderSide":
        try:
            return OrderSide[s.upper()]
        except KeyError:
            raise ValueError(f"Cannot convert {s} into a valid OrderSide")


class OrderType(Enum):
    MARKET = auto()
    LIMIT = auto()

    def to_str(self) -> str:
        return self.name.lower()

    @classmethod
    def from_str(cls, s: str) -> "OrderType":
        try:
            return OrderType[s.upper()]
        except KeyError:
            raise ValueError(f"Cannot convert {s} into a valid OrderSide")


class ExchangeRequest(Request):
    symbol: str
    qty: int
    side: OrderSide
    type: OrderType
