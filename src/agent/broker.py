from stubs import (
    Request,
    NoRequest,
    SubmitTradeRequest,
    SubmitTradeResponse,
)
from parser.message_parser import MessageParser
from interface.messenger import Messenger
from exchange.client import ExchangeClient


class Broker:
    def __init__(
        self,
        name: str,
        messenger: Messenger,
        parser: MessageParser,
        exchange: ExchangeClient,
    ) -> None:
        self.name: str = name
        self.messenger: Messenger = messenger
        self.parser: MessageParser = parser
        self.exchange: ExchangeClient = exchange

    @staticmethod
    def _join_messages(*messages) -> str:
        return " ".join([m for m in messages if m is not None])

    def _process_request(self, request: Request, output_text: str | None) -> str | None:
        match request:
            case NoRequest():
                return output_text
            case SubmitTradeRequest():
                trade_resp: SubmitTradeResponse = self.exchange.submit_trade(request)
                # port_resp: DisplayPortfolioResponse = self.ledger.handle_request(
                #     request=SaveOrderRequest()
                # )
                return self._join_messages(output_text, trade_resp.message)
            case _:
                raise NotImplementedError(f"Cannot handle request: {type(request)}")

    def run(self) -> None:
        last_message: str = ""

        while True:
            self.messenger.wait()

            message: str | None = self.messenger.get_latest_message()
            if message is None or message == last_message:
                continue

            print(f"New message: {message}")
            request, output_text = self.parser.resolve(message)
            reply = self._process_request(request, output_text)

            if reply is not None:
                self.messenger.reply(reply)
                last_message = reply
            else:
                last_message = message

    def stop(self) -> None:
        self.messenger.shutdown()
