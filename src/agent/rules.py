import re
from abc import ABC, abstractmethod

from stubs import OrderSide, OrderType, Request, SubmitTradeRequest


class Rule(ABC):
    @staticmethod
    @abstractmethod
    def should_apply_rule(input_message: str) -> bool:
        """
        Determines whether or not input message matches this rule
        """
        pass

    @staticmethod
    @abstractmethod
    def build_request(input_message: str) -> Request:
        """
        Transforms input message into an actionable request for the herder
        """
        pass

    @property
    @abstractmethod
    def output_message(self) -> str | None:
        """
        Optional static message this rule always returns
        """
        pass


class Cardo_TradeVOO(Rule):
    @staticmethod
    def should_apply_rule(input_message: str):
        return bool(re.fullmatch(r"(?i)cardo+", input_message))

    @staticmethod
    def build_request(input_message: str) -> SubmitTradeRequest:
        return SubmitTradeRequest(
            symbol="VOO",
            qty=1,
            side=OrderSide.BUY,
            type=OrderType.MARKET,
        )

    @property
    def output_message(self) -> str:
        return "Your dinner's ready!"
