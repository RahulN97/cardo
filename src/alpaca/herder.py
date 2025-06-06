import datetime

import pandas as pd
from alpaca_trade_api.entity import Order

from alpaca.exchange import ORDER_TIMEOUT, Exchange
from alpaca.ledger import Ledger
from alpaca.utils import is_mkt_open
from canvas.visualizer import DataVisualizer
from config.environment import Environment
from stubs import (
    GetOrdersRequest,
    GetOrdersResponse,
    GetPnlRequest,
    GetPnlResponse,
    GetPortfolioRequest,
    GetPortfolioResponse,
    MetricWindow,
    OrderMetadata,
    OrderSide,
    OrderStatus,
    OrderType,
    PositionMetadata,
    Request,
    Response,
    SubmitTradeRequest,
    SubmitTradeResponse,
)


class AlpacaHerder:
    def __init__(
        self,
        env: Environment,
        exchange: Exchange,
        ledger: Ledger,
        visualizer: DataVisualizer,
    ) -> None:
        self.env: Environment = env
        self.exchange: Exchange = exchange
        self.ledger: Ledger = ledger
        self.visualizer: DataVisualizer = visualizer

    def dispatch_request(self, request: Request) -> Response:
        match request:
            case SubmitTradeRequest():
                return self.submit_trade(request)
            case GetOrdersRequest():
                return self.get_orders(request)
            case GetPnlRequest():
                return self.get_pnl(request)
            case GetPortfolioRequest():
                return self.get_portfolio(request)
            case _:
                raise NotImplementedError(f"Cannot handle request: {type(request)}")

    def submit_trade(self, request: SubmitTradeRequest) -> SubmitTradeResponse:
        if (fail_resp := self._validate_trade_request(request)) is not None:
            return fail_resp

        order: Order = self.exchange.submit_trade(
            symbol=request.symbol,
            qty=request.qty,
            side=request.side,
            type=request.type,
        )
        status: OrderStatus = OrderStatus.from_str(order.status)
        return SubmitTradeResponse(
            success=status == OrderStatus.FILLED,
            message=self._get_trade_message(status, order),
        )

    def get_orders(self, request: GetOrdersRequest) -> GetOrdersResponse:
        filled_orders: list[Order] = self.exchange.get_filled_orders()
        if request.window is not None and request.window != MetricWindow.TOTAL:
            start: datetime.date = self._window_to_start(request.window)
            filled_orders = [o for o in filled_orders if o.filled_at >= start]
        order_metas: list[OrderMetadata] = [
            OrderMetadata(
                timestamp=o.filled_at,
                asset=o.symbol,
                type=OrderType.from_str(o.type),
                side=OrderSide.from_str(o.side),
                qty=float(o.filled_qty),
                price=float(o.filled_avg_price),
            )
            for o in filled_orders
        ]
        path: str = self.visualizer.generate_orders_table(order_metas)
        return GetOrdersResponse(
            success=True, message="Done fetching filled orders.", path=path
        )

    def get_portfolio(self, request: GetPortfolioRequest) -> GetPortfolioResponse:
        filled_orders: list[Order] = self.exchange.get_filled_orders()
        positions: list[PositionMetadata] = self.ledger.get_positions(filled_orders)
        path: str = self.visualizer.generate_portfolio_table(positions)
        return GetPortfolioResponse(
            success=True, message="Done fetching portfolio positions.", path=path
        )

    def get_pnl(self, request: GetPnlRequest) -> GetPnlResponse:
        filled_orders: list[Order] = self.exchange.get_filled_orders()
        total_pnl: pd.DataFrame = self.ledger.get_total_running_pnl(filled_orders)
        if request.window is not None and request.window != MetricWindow.TOTAL:
            start: datetime.date = self._window_to_start(request.window)
            total_pnl = self._root_pnl(total_pnl, start)
        import pdb

        pdb.set_trace()
        path: str = self.visualizer.generate_pnl_plot(total_pnl, request.window)
        return GetPnlResponse(success=True, message="Done calculating PnL.", path=path)

    def _validate_trade_request(self, request: SubmitTradeRequest) -> None:
        if self.env == Environment.TEST:
            # pass through all requests to test client
            return

        if request.type == OrderType.LIMIT:
            return SubmitTradeResponse(
                success=False,
                message="Failed to route trade: Exchange doesn't support callbacks for fills on limit orders.",
                metadata=None,
            )
        now: datetime.datetime = pd.Timestamp.now(tz=datetime.timezone.utc)
        if not is_mkt_open(now):
            return SubmitTradeResponse(
                success=False,
                message=f"Failed to route trade: Current time {now} is outside of US market hours",
                metadata=None,
            )

    @staticmethod
    def _get_trade_message(status: OrderStatus, order: Order) -> str:
        match status:
            case OrderStatus.FILLED:
                action: str = "Bought" if order.side == "buy" else "Sold"
                return (
                    "Order was successfully filled! "
                    f"{action} {order.filled_qty} shares of {order.symbol} at {float(order.filled_avg_price):.2f}"
                )
            case OrderStatus.CANCELED:
                return f"Order was routed, but wasn't filled before the {ORDER_TIMEOUT} second timeout. Canceled"
            case OrderStatus.REJECTED:
                return (
                    "Order was rejected by exchange - likely due to insufficient funds"
                )
            case _:
                raise ValueError(f"Unexpected order status: {status.name}")

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
        starting_pnl: float = 0.0 if prev.empty else prev.iloc[-1]["total_pnl"]

        df = df[df["timestamp"] >= start]
        df["total_pnl"] = df["total_pnl"] - starting_pnl
        return df
