from abc import ABC, abstractmethod
import re

from agent.request import Request
from exchange.request import ExchangeRequest


class Rule(ABC):
    @abstractmethod
    def should_apply_rule(input_message: str) -> bool:
        pass

    @abstractmethod
    def build_request(input_message: str) -> Request:
        pass

    @property
    @abstractmethod
    def output_message(self) -> str:
        pass


class Cardo_TradeVOO(Rule):
    def should_apply_rule(input_message: str):
        return bool(re.fullmatch(r"(?i)cardo+", input_message))

    def build_request(input_message: str) -> ExchangeRequest:
        return ExchangeRequest()

    @property
    def output_message(self) -> str:
        return "Your dinner's ready!"
