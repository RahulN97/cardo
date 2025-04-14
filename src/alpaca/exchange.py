from functools import cached_property
from uuid import uuid4
import time

from alpaca_trade_api.rest import REST
from alpaca_trade_api.entity import Order

from errors import ErroredOrderState
from stubs import (
    OrderStatus,
    OrderMetadata,
    OrderSide,
    OrderType,
)


ORDER_TIMEOUT: float = 5.0
ORDER_POLL_INTERVAL: float = 1.0
VALID_ORDER_STATUSES: frozenset[str] = frozenset(("filled", "canceled", "rejected"))


class Exchange:
    def __init__(
        self,
        broker_name: str,
        client: REST,
        poll_interval: float = ORDER_POLL_INTERVAL,
        timeout: float = ORDER_TIMEOUT,
    ) -> None:
        self.broker_name: str = broker_name
        self.client: REST = client
        self.poll_interval: float = poll_interval
        self.timeout: float = timeout

    @cached_property
    def client_id(self) -> str:
        return f"broker-{self.broker_name}"

    def submit_trade(
        self, symbol: str, qty: int, side: OrderSide, type: OrderType
    ) -> OrderMetadata:
        return self._try_submit_order(
            symbol=symbol, qty=qty, side=side.to_str(), type=type.to_str()
        )

    def get_filled_orders(self) -> list[Order]:
        orders = self.client.list_orders(status="filled", nested=True)
        return [o for o in orders if o.client_order_id.startswith(self.client_id)]

    @staticmethod
    def _order_to_order_meta(order: Order) -> OrderMetadata:
        return OrderMetadata(
            id=order.id,
            client_order_id=order.client_order_id,
            fill_price=order.filled_avg_price,
            status=OrderStatus.from_str(order.status),
        )

    def _check_status_periodically(self, order_id: str) -> Order | None:
        time_waited: float = 0.0
        while time_waited < self.timeout:
            order: Order = self.client.get_order(order_id)
            if order.status in VALID_ORDER_STATUSES:
                return order

            time_waited += self.poll_interval
            time.sleep(self.poll_interval)

    def _try_submit_order(
        self, symbol: str, qty: int, side: str, type: str
    ) -> OrderMetadata:
        client_order_id: str = f"{self.client_id}-{str(uuid4())}"
        order: Order = self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force="day",
            client_order_id=client_order_id,
        )
        if order.status in VALID_ORDER_STATUSES:
            return self._order_to_order_meta(order)

        # unexpected order status. Keep querying order to see if status changes
        if (order := self._check_status_periodically(order.id)) is not None:
            return self._order_to_order_meta(order)

        # corrupted order state, cancel it instead
        return self._try_cancel_order(order.id)

    def _try_cancel_order(self, order_id: str) -> OrderMetadata:
        self.client.cancel_order(order_id)
        if (order := self._check_status_periodically(order_id)) is not None:
            return self._order_to_order_meta(order)

        order: Order = self.client.get_order(order_id)
        raise ErroredOrderState(
            order_id=order_id, status=order.status, timeout=ORDER_TIMEOUT
        )
