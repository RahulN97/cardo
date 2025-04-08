from abc import ABC, abstractmethod
import re

from stubs import Request, OrderSide, OrderType, SubmitTradeRequest


class Rule(ABC):
    @staticmethod
    @abstractmethod
    def should_apply_rule(input_message: str) -> bool:
        pass

    @staticmethod
    @abstractmethod
    def build_request(input_message: str) -> Request:
        pass

    @property
    @abstractmethod
    def output_message(self) -> str:
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
