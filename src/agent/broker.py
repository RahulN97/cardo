import logging

from agent.profiles import Profile
from alpaca.herder import AlpacaHerder
from fox.messenger import ChatResponse, Messenger
from resolver.message_resolver import MessageResolver
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
        profile: Profile,
        messenger: Messenger,
        resolver: MessageResolver,
        herder: AlpacaHerder,
    ) -> None:
        self.profile: Profile = profile
        self.messenger: Messenger = messenger
        self.resolver: MessageResolver = resolver
        self.herder: AlpacaHerder = herder

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
                return None
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
        self.messenger.wait()
        self.messenger.respond(
            response=ChatResponse(message=self.profile.dialogue.init_message)
        )

    def run(self) -> None:
        last_seen: str = self.profile.dialogue.init_message

        while True:
            self.messenger.wait()

            message: str | None = self.messenger.get_latest_message()
            if message is None or message == last_seen:
                continue

            logger.info(f"New message: {message}")
            request, output_text = self.resolver.match(message)
            response = self._process_request(request, output_text)

            if response is not None:
                logger.info("Issuing chat response")
                self.messenger.respond(response)
                last_seen = response.message
            else:
                last_seen = message

    def stop(self) -> None:
        self.messenger.respond(
            response=ChatResponse(message=self.profile.dialogue.shutdown_message),
        )
        self.messenger.shutdown()
