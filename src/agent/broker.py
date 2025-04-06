from agent.request import Request, NoRequest
from exchange.request import ExchangeRequest
from portfolio.request import PortfolioRequest
from parser.message_parser import MessageParser
from interface.messenger import Messenger
from exchange.client import ExchangeClient
from portfolio.ledger import Ledger


class Broker:
    def __init__(
        self,
        name: str,
        messenger: Messenger,
        parser: MessageParser,
        exchange: ExchangeClient,
        ledger: Ledger,
    ) -> None:
        self.name: str = name
        self.messenger: Messenger = messenger
        self.parser: MessageParser = parser
        self.exchange: ExchangeClient = exchange
        self.ledger: Ledger = ledger

    def _process_request(self, request: Request, output_text: str | None) -> str | None:
        match request:
            case NoRequest():
                return output_text
            case ExchangeRequest():
                self.exchange.handle_request(request)
                return output_text
            case PortfolioRequest():
                self.ledger.handle_request(request)
                return output_text
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
