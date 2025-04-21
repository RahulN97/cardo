import logging

import pandas as pd

from agent.character import LlmCharacter
from alpaca.herder import AlpacaHerder
from fox.messenger import ChatResponse, Messenger
from stubs import (
    GetOrdersRequest,
    GetOrdersResponse,
    GetPnlRequest,
    GetPnlResponse,
    NullRequest,
    Request,
    SubmitTradeRequest,
    SubmitTradeResponse,
)


logger: logging.Logger = logging.getLogger(__name__)


class Broker:
    def __init__(
        self,
        name: str,
        messenger: Messenger,
        character: LlmCharacter,
        herder: AlpacaHerder,
        max_lag: int,
    ) -> None:
        self.name: str = name
        self.messenger: Messenger = messenger
        self.character: LlmCharacter = character
        self.herder: AlpacaHerder = herder
        self.max_lag: int = max_lag
        self.last_seen: str = ""
        self.last_sent_ts: pd.Timestamp = pd.Timestamp.now()

    @staticmethod
    def _join_messages(*messages) -> str:
        responses: list[str] = [m for m in messages if m is not None]
        return " ".join(responses) if responses else None

    def _process_request(
        self, request: Request, output_text: str | None
    ) -> ChatResponse | None:
        logger.info(f"Issuing request: {type(request)}")
        match request:
            case NullRequest():
                return ChatResponse(message=output_text) if output_text else None
            case SubmitTradeRequest():
                resp: SubmitTradeResponse = self.herder.submit_trade(request)
            case GetOrdersRequest():
                resp: GetOrdersResponse = self.herder.get_orders(request)
            case GetPnlRequest():
                resp: GetPnlResponse = self.herder.get_pnl(request)
            case _:
                raise NotImplementedError(f"Cannot handle request: {type(request)}")

        return ChatResponse(
            message=self._join_messages(output_text, resp.message),
            img_path=resp.path,
        )

    def start(self) -> None:
        logger.info(f"Starting broker {self.name}")
        self.messenger.wait()
        init_message: str = self.character.get_init_message()
        self.messenger.respond(response=ChatResponse(message=init_message))
        self.last_seen = init_message

    def run(self) -> None:
        while True:
            self.messenger.wait()
            now: pd.Timestamp = pd.Timestamp.now()

            message: str | None = self.messenger.get_latest_message()
            if message is not None and message != self.last_seen:
                logger.info(f"Processing new message: {message}")
                request, output_text = self.character.resolve(message)
                response = self._process_request(request, output_text)
            elif (now - self.last_sent_ts).seconds > self.max_lag:
                response = ChatResponse(message=self.character.get_random_phrase())
            else:
                continue

            if response is not None:
                logger.info("Issuing chat response")
                self.messenger.respond(response)
                self.last_seen = response.message
                self.last_sent_ts = now
            else:
                self.last_seen = message

    def stop(self) -> None:
        logger.info(f"Shutting down broker {self.name}")
        self.messenger.shutdown()
