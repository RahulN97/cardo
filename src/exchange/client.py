from alpaca_trade_api.rest import REST
from alpaca_trade_api.entity import Order

from exchange.request import ExchangeRequest


class ExchangeClient:
    def __init__(
        self, broker_name: str, base_url: str, api_key: str, api_secret: str
    ) -> None:
        self.broker_name: str = broker_name
        self.client = REST(
            key_id=api_key,
            secret_key=api_secret,
            base_url=base_url,
        )

    def handle_request(self, request: ExchangeRequest) -> None:
        order = self._submit_order(
            symbol=request.symbol,
            qty=request.qty,
            side=request.side.to_str(),
            type=request.type.to_str(),
        )
        import pdb

        pdb.set_trace()
        print("a")

    def _submit_order(self, symbol: str, qty: int, side: str, type: str) -> Order:
        return self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force="day",
            client_order_id=f"broker-{self.broker_name}",
        )
