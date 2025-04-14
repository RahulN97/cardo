from stubs import (
    Request,
    NullRequest,
    GetPnlRequest,
    GetPnlResponse,
    SubmitTradeRequest,
    SubmitTradeResponse,
)
from parser.message_parser import MessageParser
from fox.messenger import ChatResponse, Messenger
from alpaca.herder import AlpacaHerder


class Broker:
    def __init__(
        self,
        name: str,
        messenger: Messenger,
        parser: MessageParser,
        herder: AlpacaHerder,
    ) -> None:
        self.name: str = name
        self.messenger: Messenger = messenger
        self.parser: MessageParser = parser
        self.herder: AlpacaHerder = herder

    @staticmethod
    def _join_messages(*messages) -> str:
        responses: list[str] = [m for m in messages if m is not None]
        return " ".join(responses) if responses else None

    def _process_request(
        self, request: Request, output_text: str | None
    ) -> ChatResponse | None:
        match request:
            case NullRequest():
                return None
            case SubmitTradeRequest():
                resp: SubmitTradeResponse = self.herder.submit_trade(request)
            case GetPnlRequest():
                resp: GetPnlResponse = self.herder.get_pnl(request)
            case _:
                raise NotImplementedError(f"Cannot handle request: {type(request)}")

        return ChatResponse(
            message=self._join_messages(output_text, resp.message),
            img_path=resp.path,
        )

    def run(self) -> None:
        last_message: str = ""

        while True:
            self.messenger.wait()

            message: str | None = self.messenger.get_latest_message()
            if message is None or message == last_message:
                continue

            print(f"New message: {message}")
            request, output_text = self.parser.resolve(message)
            response = self._process_request(request, output_text)

            if response is not None:
                self.messenger.respond(response)
                last_message = response.message
            else:
                last_message = message

    def stop(self) -> None:
        self.messenger.shutdown()
