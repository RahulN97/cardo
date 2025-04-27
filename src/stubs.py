from enum import Enum, auto

import pandas as pd
from pydantic import BaseModel, ConfigDict


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

    @classmethod
    def from_str(cls, s: str) -> "OrderType":
        try:
            return OrderType[s.upper()]
        except KeyError:
            raise ValueError(f"Cannot convert {s} into a valid OrderType")

    def to_str(self) -> str:
        return self.name.lower()


class PositionSide(Enum):
    LONG = auto()
    SHORT = auto()

    @classmethod
    def from_str(cls, s: str) -> "PositionSide":
        try:
            return PositionSide[s.upper()]
        except KeyError:
            raise ValueError(f"Cannot convert {s} into a valid PositionSide")

    def to_str(self) -> str:
        return self.name.lower()


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

    def to_str(self) -> str:
        return self.name.lower()


class OrderMetadata(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    timestamp: pd.Timestamp
    asset: str
    type: OrderType
    side: OrderSide
    qty: float
    price: float


class PositionMetadata(BaseModel):
    asset: str
    qty: float
    side: PositionSide
    avg_entry_price: float
    current_price: float
    cost_basis: float
    market_value: float
    unrealized_pnl: float


class MetricWindow(Enum):
    DAILY = auto()
    WEEKLY = auto()
    MONTHLY = auto()
    TOTAL = auto()


# APIs #


class Request(BaseModel):
    pass


class Response(BaseModel):
    success: bool
    message: str
    path: str | None = None


class NullRequest(Request):
    pass


class SubmitTradeRequest(Request):
    symbol: str
    qty: float
    side: OrderSide
    type: OrderType


class SubmitTradeResponse(Response):
    pass


class GetPnlRequest(Request):
    window: MetricWindow


class GetPnlResponse(Response):
    pass


class GetOrdersRequest(Request):
    window: MetricWindow


class GetOrdersResponse(Response):
    pass


class GetPortfolioRequest(Request):
    pass


class GetPortfolioResponse(Response):
    pass
