import datetime
from collections import defaultdict, deque

import pandas as pd
from alpaca_trade_api.entity import Order
from alpaca_trade_api.entity_v2 import BarsV2

from alpaca.client import AlpacaClient
from alpaca.utils import MKT_CLOSE, MKT_OPEN, is_mkt_open
from stubs import OrderSide


class Ledger:
    def __init__(self, client: AlpacaClient) -> None:
        self.client: AlpacaClient = client

    def get_total_running_pnl(self, filled_orders: list[Order]) -> pd.DataFrame:
        if not filled_orders:
            return pd.DataFrame(
                columns=["timestamp", "realized_pnl", "unrealized_pnl", "total_pnl"]
            )

        mkt_price: dict[str, dict[pd.Timestamp, float]] = self._get_bars(filled_orders)

        start = end = pd.Timestamp.now(tz=datetime.timezone.utc)
        ts_to_orders: dict[pd.Timestamp, list[Order]] = defaultdict(list)
        for o in filled_orders:
            fill_time: pd.Timestamp = pd.Timestamp(o.filled_at)
            start = min(fill_time, start)
            ts_to_orders[fill_time].append(o)

        position_lots: dict[str, deque[tuple[int, float]]] = defaultdict(deque)
        net_positions: dict[str, int] = defaultdict(int)
        realized_pnl: float = 0.0

        pnl_snapshots = []
        timeline: list[pd.Timestamp] = [
            ts
            for ts in pd.date_range(
                start=start, end=end, freq="1min", tz=datetime.timezone.utc
            )
            if is_mkt_open(ts)
        ]
        for timestamp in timeline:
            for order in ts_to_orders[timestamp]:
                symbol = order.symbol
                qty: int = int(order.filled_qty)
                price: float = float(order.filled_avg_price)
                side: OrderSide = OrderSide.from_str(order.side)

                if side == OrderSide.BUY:
                    position_lots[symbol].append((qty, price))
                    net_positions[symbol] += qty
                elif side == OrderSide.SELL:
                    qty_to_sell: int = qty
                    while qty_to_sell > 0 and position_lots[symbol]:
                        lot_qty, lot_price = position_lots[symbol].popleft()
                        matched_qty = min(qty_to_sell, lot_qty)
                        pnl = matched_qty * (price - lot_price)
                        realized_pnl += pnl
                        qty_to_sell -= matched_qty
                        if lot_qty > matched_qty:
                            position_lots[symbol].appendleft(
                                (lot_qty - matched_qty, lot_price)
                            )
                    net_positions[symbol] -= qty

            unrealized_pnl: float = 0.0
            for symbol, lots in position_lots.items():
                market_price = mkt_price[symbol][timestamp]
                for qty, entry_price in lots:
                    unrealized_pnl += qty * (market_price - entry_price)

            total_pnl = realized_pnl + unrealized_pnl
            pnl_snapshots.append(
                {
                    "timestamp": timestamp,
                    "realized_pnl": realized_pnl,
                    "unrealized_pnl": unrealized_pnl,
                    "total_pnl": total_pnl,
                }
            )

        return pd.DataFrame(pnl_snapshots)

    def _get_bars(self, orders: list[Order]) -> dict[str, dict[pd.Timestamp, float]]:
        sym_to_start: dict[str, pd.Timestamp] = {}
        for o in orders:
            filled_at: pd.Timestamp = pd.Timestamp(
                o.filled_at, tz=datetime.timezone.utc
            )
            if (o.symbol not in sym_to_start) or filled_at < sym_to_start[o.symbol]:
                sym_to_start[o.symbol] = filled_at

        return {
            sym: self._get_bars_for_symbol(symbol=sym, start=start)
            for sym, start in sym_to_start.items()
        }

    def _get_bars_for_symbol(
        self, symbol: str, start: pd.Timestamp
    ) -> dict[pd.Timestamp, float]:
        bars_data: list[pd.DataFrame] = []

        cur_start: pd.Timestamp = start
        end: pd.Timestamp = pd.Timestamp.now(tz="America/New_York")
        while cur_start < end:
            # Format RFC3339
            start_ts: str = (
                cur_start.astimezone(datetime.timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )
            end_ts: str = (
                end.astimezone(datetime.timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z")
            )

            bars: BarsV2 = self.client.get_bars(
                symbol=symbol,
                timeframe="1Min",
                start=start_ts,
                end=end_ts,
                limit=1000,
            )

            df: pd.DataFrame = bars.df
            if df.empty:
                break

            df = df.sort_index()
            bars_data.append(df)

            last_ts = df.index[-1]
            cur_start = last_ts + pd.Timedelta(minutes=1)

        if not bars_data:
            return {}

        bars_df = pd.concat(bars_data)
        return self._map_ts_to_price(bars_df)

    @staticmethod
    def _map_ts_to_price(bars_df: pd.DataFrame) -> dict[pd.Timestamp, float]:
        bars_df = bars_df.sort_index()
        full_index = []

        for day in bars_df.index.normalize().unique():
            day_start = pd.Timestamp.combine(day, MKT_OPEN).tz_localize("UTC")
            day_end = pd.Timestamp.combine(day, MKT_CLOSE).tz_localize("UTC")
            full_index.extend(pd.date_range(day_start, day_end, freq="1min"))

        full_index = pd.DatetimeIndex(full_index)
        bars_df = bars_df.reindex(full_index)
        bars_df["close"] = bars_df["close"].ffill()

        return bars_df["close"].to_dict()
