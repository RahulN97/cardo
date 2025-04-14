import datetime

import pandas as pd
from alpaca_trade_api.entity import Order
from alpaca_trade_api.rest import REST

from stubs import (
    MetricWindow,
    OrderStatus,
    OrderType,
    OrderMetadata,
    GetPnlRequest,
    GetPnlResponse,
    SubmitTradeRequest,
    SubmitTradeResponse,
)
from alpaca.exchange import Exchange
from alpaca.ledger import Ledger
from alpaca.visualize import DataVisualizer
from alpaca.utils import is_mkt_open


MKT_OPEN: datetime.time = datetime.time(9, 30)
MKT_CLOSE: datetime.time = datetime.time(16, 0)

ORDER_STATUS_TO_MESSAGE: dict[OrderStatus, str] = {
    OrderStatus.FILLED: "Order was successfully filled!",
    OrderStatus.CANCELED: "Order was routed, but wasn't filled before timeout. Canceled",
    OrderStatus.REJECTED: "Order was rejected by exchange - likely due to insufficient funds",
}


class AlpacaHerder:
    def __init__(
        self,
        broker_name: str,
        base_url: str,
        api_key: str,
        api_secret: str,
    ) -> None:
        self.broker_name: str = broker_name
        client: REST = REST(key_id=api_key, secret_key=api_secret, base_url=base_url)
        self.exchange: Exchange = Exchange(broker_name=broker_name, client=client)
        self.ledger: Ledger = Ledger(client=client)
        self.visualizer: DataVisualizer = DataVisualizer(broker_name=broker_name)

    def submit_trade(self, request: SubmitTradeRequest) -> SubmitTradeResponse:
        if request.type == OrderType.LIMIT:
            return SubmitTradeResponse(
                success=False,
                message="Exchange doesn't support callbacks for limit orders fills.",
                metadata=None,
            )
        now: datetime.datetime = pd.Timestamp.now(tz=datetime.timezone.utc)
        if not is_mkt_open(now):
            return SubmitTradeResponse(
                success=False,
                message=f"Current time {now} is outside of US market hours",
                metadata=None,
            )
        order_meta: OrderMetadata = self.exchange.submit_trade(
            symbol=request.symbol, qty=request.qty, side=request.side, type=request.type
        )
        return SubmitTradeResponse(
            success=order_meta.status == OrderStatus.FILLED,
            message=ORDER_STATUS_TO_MESSAGE[order_meta.status],
            metadata=order_meta,
        )

    def get_pnl(self, request: GetPnlRequest) -> GetPnlResponse:
        filled_orders: list[Order] = self.exchange.get_filled_orders()
        total_pnl: pd.DataFrame = self.ledger.get_total_running_pnl(filled_orders)
        if request.window not in (MetricWindow.TOTAL, None):
            start: datetime.date = self._window_to_start(request.window)
            total_pnl = self._root_pnl(total_pnl, start)
        path: str = self.visualizer.generate_pnl_plot(total_pnl, request.window)
        return GetPnlResponse(success=True, message="Your PnL's ready!", path=path)

    @staticmethod
    def _window_to_start(window: MetricWindow) -> datetime.date:
        now: datetime.date = datetime.datetime.now().date()
        match window:
            case MetricWindow.DAILY:
                return now
            case MetricWindow.WEEKLY:
                return now - datetime.timedelta(weeks=1)
            case MetricWindow.MONTHLY:
                return now - datetime.timedelta(weeks=4)
            case _:
                raise ValueError(f"Unexpected metric window: {window.name}")

    @staticmethod
    def _root_pnl(df: pd.DataFrame, start: datetime.date) -> pd.DataFrame:
        prev = df[df["timestamp"] < start]
        if prev.empty:
            base = 0.0
        else:
            base = prev.iloc[-1]["total_pnl"]

        df = df[df["timestamp"] >= start]
        df["total_pnl"] = df["total_pnl"] - base
        return df
