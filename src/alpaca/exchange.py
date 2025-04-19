import time
from uuid import uuid4

from alpaca_trade_api.entity import Order
from alpaca_trade_api.rest import REST

from errors import ErroredOrderState
from stubs import OrderSide, OrderType


ORDER_TIMEOUT: float = 5.0
ORDER_POLL_INTERVAL: float = 1.0
VALID_ORDER_STATUSES: frozenset[str] = frozenset(("filled", "canceled", "rejected"))


class Exchange:
    def __init__(
        self,
        client: REST,
        id: str,
        poll_interval: float = ORDER_POLL_INTERVAL,
        timeout: float = ORDER_TIMEOUT,
    ) -> None:
        self.client: REST = client
        self.client_id: str = f"broker-{id}"
        self.poll_interval: float = poll_interval
        self.timeout: float = timeout

    def submit_trade(
        self, symbol: str, qty: int, side: OrderSide, type: OrderType
    ) -> Order:
        return self._try_submit_order(
            symbol=symbol, qty=qty, side=side.to_str(), type=type.to_str()
        )

    def get_filled_orders(self) -> list[Order]:
        orders = self.client.list_orders(status="filled", nested=True)
        return [o for o in orders if o.client_order_id.startswith(self.client_id)]

    def _check_status_periodically(self, order_id: str) -> Order | None:
        time_waited: float = 0.0
        while time_waited < self.timeout:
            order: Order = self.client.get_order(order_id)
            if order.status in VALID_ORDER_STATUSES:
                return order

            time_waited += self.poll_interval
            time.sleep(self.poll_interval)

    def _try_submit_order(self, symbol: str, qty: int, side: str, type: str) -> Order:
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
            return order

        order_id: str = order.id
        # unexpected order status. Keep querying order to see if status changes
        if (order := self._check_status_periodically(order_id)) is not None:
            return order

        # corrupted order state, cancel it instead
        return self._try_cancel_order(order.id)

    def _try_cancel_order(self, order_id: str) -> Order:
        self.client.cancel_order(order_id)
        if (order := self._check_status_periodically(order_id)) is not None:
            return order

        order: Order = self.client.get_order(order_id)
        raise ErroredOrderState(
            order_id=order_id, status=order.status, timeout=ORDER_TIMEOUT
        )
