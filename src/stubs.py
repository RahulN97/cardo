from enum import Enum, auto
from pydantic import BaseModel


# Structs #


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
            raise ValueError(f"Cannot convert {s} into a valid OrderType")


class OrderStatus(Enum):
    FILLED = auto()
    REJECTED = auto()
    CANCELED = auto()

    @classmethod
    def from_str(cls, s: str) -> "OrderStatus":
        try:
            return OrderStatus[s.upper()]
        except KeyError:
            raise ValueError(f"Cannot convert {s} into a valid OrderStatus")


class OrderMetadata(BaseModel):
    id: str
    client_order_id: str
    fill_price: float | None
    status: OrderStatus


# APIs #


class Request(BaseModel):
    pass


class NoRequest(Request):
    pass


class Response(BaseModel):
    success: bool


class SubmitTradeRequest(Request):
    symbol: str
    qty: int
    side: OrderSide
    type: OrderType


class SubmitTradeResponse(Response):
    message: str
    metadata: OrderMetadata | None


class DisplayPortfolioRequest(Request):
    pass


class DisplayPortfolioResponse(Response):
    pass
