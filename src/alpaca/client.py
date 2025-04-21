import datetime
import random
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from uuid import uuid4

import pandas as pd
from alpaca_trade_api.entity import Order
from alpaca_trade_api.entity_v2 import BarsV2, QuoteV2
from alpaca_trade_api.rest import REST

from config.environment import Environment


class AlpacaClient(ABC):
    FEED: str = "iex"

    def __init__(self, base_url: str, api_key: str, api_secret: str, **kwargs) -> None:
        self.client: REST = REST(
            key_id=api_key,
            secret_key=api_secret,
            base_url=base_url,
        )

    def get_bars(
        self, symbol: str, timeframe: str, start: str, end: str, limit: int
    ) -> BarsV2:
        return self.client.get_bars(
            symbol=symbol,
            timeframe=timeframe,
            start=start,
            end=end,
            limit=limit,
            feed=self.FEED,
        )

    @abstractmethod
    def get_order(self, id: str) -> Order:
        pass

    @abstractmethod
    def list_orders(self, status: str, nested: bool) -> list[Order]:
        pass

    @abstractmethod
    def cancel_order(self, id: str) -> None:
        pass

    @abstractmethod
    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        client_order_id: str,
    ) -> Order:
        pass


class LiveClient(AlpacaClient):
    def get_order(self, id: str) -> Order:
        return self.client.get_order(order_id=id)

    def list_orders(self, status: str, nested: bool) -> list[Order]:
        return self.client.list_orders(status=status, nested=nested)

    def cancel_order(self, id: str) -> None:
        return self.client.cancel_order(order_id=id)

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        client_order_id: str,
    ) -> Order:
        return self.client.submit_order(
            symbol=symbol,
            qty=qty,
            side=side,
            type=type,
            time_in_force=time_in_force,
            client_order_id=client_order_id,
        )


class TestClient(AlpacaClient):
    DB_PATH_ROOT: Path = Path.cwd().parent / "sqlite"

    CREATE_TABLE: str = """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            client_order_id TEXT,
            symbol TEXT,
            filled_qty REAL,
            filled_avg_price REAL,
            side TEXT,
            type TEXT,
            time_in_force TEXT,
            status TEXT,
            filled_at TEXT
        )
    """
    SUBMIT_RECORD: str = """
        INSERT OR REPLACE INTO orders (
            id,
            client_order_id,
            symbol,
            filled_qty,
            filled_avg_price,
            side,
            type,
            time_in_force,
            status,
            filled_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    GET_ORDER: str = "SELECT * FROM orders WHERE id = ?"
    CANCEL_ORDER: str = "DELETE FROM orders WHERE id = ?"
    LIST_ORDERS: str = "SELECT * FROM orders WHERE status = ?"

    def __init__(
        self, base_url: str, api_key: str, api_secret: str, test_id: str
    ) -> None:
        super().__init__(base_url=base_url, api_key=api_key, api_secret=api_secret)
        if not self.DB_PATH_ROOT.exists():
            self.DB_PATH_ROOT.mkdir(parents=True)
        db_path: Path = self.DB_PATH_ROOT / f"{test_id}.db"
        self.conn: sqlite3.Connection = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        with self.conn:
            self.conn.execute(self.CREATE_TABLE)

    def get_order(self, id: str) -> Order:
        cur: sqlite3.Cursor = self.conn.execute(self.GET_ORDER, (id,))
        row: dict = cur.fetchone()
        if not row:
            raise ValueError(f"Order with ID {id} not found")
        return Order(dict(row))

    def list_orders(self, status: str, nested: bool) -> list[Order]:
        cur: sqlite3.Cursor = self.conn.execute(self.LIST_ORDERS, (status,))
        return [Order(dict(row)) for row in cur.fetchall()]

    def cancel_order(self, id: str) -> None:
        with self.conn:
            self.conn.execute(self.CANCEL_ORDER, (id,))

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str,
        type: str,
        time_in_force: str,
        client_order_id: str,
    ) -> Order:
        order_id: str = str(uuid4())
        now: pd.Timestamp = pd.Timestamp.now(tz=datetime.timezone.utc)
        filled_at: str = now.strftime("%Y%m%d %H:%M:%S")
        status: str = "filled"
        quote: QuoteV2 = self.client.get_latest_quote(symbol=symbol, feed=self.FEED)
        # random price for testing
        price: float = quote.ap * (1 + random.uniform(-0.03, 0.03))

        with self.conn:
            self.conn.execute(
                self.SUBMIT_RECORD,
                (
                    order_id,
                    client_order_id,
                    symbol,
                    qty,
                    price,
                    side,
                    type,
                    time_in_force,
                    status,
                    filled_at,
                ),
            )

        return Order(
            dict(
                id=order_id,
                client_order_id=client_order_id,
                symbol=symbol,
                filled_qty=qty,
                filled_avg_price=price,
                side=side,
                type=type,
                time_in_force=time_in_force,
                status=status,
                filled_at=filled_at,
            )
        )


def get_alpaca_client(
    env: Environment,
    base_url: str,
    api_key: str,
    api_secret: str,
    test_id: str | None,
) -> AlpacaClient:
    client: type[AlpacaClient] = TestClient if env == Environment.TEST else LiveClient
    return client(
        base_url=base_url,
        api_key=api_key,
        api_secret=api_secret,
        test_id=test_id,
    )
