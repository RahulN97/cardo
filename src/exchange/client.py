import datetime
from uuid import uuid4
import pytz
import time

from alpaca_trade_api.rest import REST
from alpaca_trade_api.entity import Order

from errors import ErroredOrderState
from stubs import (
    OrderType,
    OrderStatus,
    OrderMetadata,
    SubmitTradeRequest,
    SubmitTradeResponse,
)


class ExchangeClient:
    MKT_OPEN: datetime.time = datetime.time(9, 30)
    MKT_CLOSE: datetime.time = datetime.time(16, 0)

    ORDER_TIMEOUT: float = 10.0
    ORDER_POLL_INTERVAL: float = 1.0

    ORDER_STATUS_TO_MESSAGE: dict[str, str] = {
        OrderStatus.FILLED: "Order was successfully filled!",
        OrderStatus.CANCELED: f"Order was routed, but wasn't filled within {ORDER_TIMEOUT} seconds. Canceled",
        OrderStatus.REJECTED: "Order was rejected by exchange - likely due to insufficient funds",
    }

    def __init__(
        self,
        broker_name: str,
        base_url: str,
        api_key: str,
        api_secret: str,
    ) -> None:
        self.broker_name: str = broker_name
        self.client: REST = REST(
            key_id=api_key, secret_key=api_secret, base_url=base_url
        )

    def submit_trade(self, request: SubmitTradeRequest) -> SubmitTradeResponse:
        if request.type == OrderType.LIMIT:
            return SubmitTradeResponse(
                success=False,
                metadata=None,
                message="Exchange doesn't support callbacks for limit orders fills.",
            )
        now: datetime.datetime = datetime.datetime.now(pytz.timezone("US/Eastern"))
        if not self._is_mkt_open(now):
            return SubmitTradeResponse(
                success=False,
                metadata=None,
                message=f"Current time {now} is outside of US market hours",
            )
        order_meta: OrderMetadata = self._try_submit_order(
            symbol=request.symbol,
            qty=request.qty,
            side=request.side.to_str(),
            type=request.type.to_str(),
        )
        return SubmitTradeResponse(
            success=order_meta.status == OrderStatus.FILLED,
            message=self.ORDER_STATUS_TO_MESSAGE[order_meta.status],
            metadata=order_meta,
        )

    def _is_mkt_open(self, now: datetime.datetime) -> bool:
        return now.weekday() < 5 and self.MKT_OPEN <= now.time() <= self.MKT_CLOSE

    def _query_order_periodically(self, order_id: str) -> Order | None:
        time_waited: float = 0.0
        while time_waited < self.ORDER_TIMEOUT:
            order: Order = self.client.get_order(order_id)
            status: str = order.status
            if status in ("filled", "rejected", "canceled"):
                return order

            time_waited += self.ORDER_POLL_INTERVAL
            time.sleep(self.ORDER_POLL_INTERVAL)

    def _try_submit_order(
        self, symbol: str, qty: int, side: str, type: str
    ) -> OrderMetadata:
        client_order_id: str = f"broker-{self.broker_name}-{str(uuid4())}"
        order: Order = self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force="day",
            client_order_id=client_order_id,
        )
        order_id: str = order.id

        if (order := self._query_order_periodically(order_id)) is not None:
            return OrderMetadata(
                id=order.id,
                client_order_id=order.client_order_id,
                fill_price=order.filled_avg_price,
                status=OrderStatus.from_str(order.status),
            )
        return self._try_cancel_order(order_id)

    def _try_cancel_order(self, order_id: str) -> OrderMetadata:
        self.client.cancel_order(order_id)
        if (order := self._query_order_periodically(order_id)) is not None:
            return OrderMetadata(
                id=order.id,
                client_order_id=order.client_order_id,
                fill_price=order.filled_avg_price,
                status=OrderStatus.from_str(order.status),
            )
        raise ErroredOrderState(order_id=order_id, timeout=self.ORDER_TIMEOUT)
