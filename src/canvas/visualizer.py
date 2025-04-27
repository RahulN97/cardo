import datetime

import pandas as pd
import plotly.graph_objects as go

from stubs import MetricWindow, OrderMetadata, PositionMetadata


class DataVisualizer:

    def __init__(self, name: str) -> None:
        self.path: str = f"/tmp/{name}-{{file_name}}.png"

    def generate_orders_table(self, orders: list[OrderMetadata]) -> str:
        input_orders: list[dict[str, str | float]] = [
            {
                "Timestamp": o.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Asset": o.asset,
                "Order Type": o.type.to_str(),
                "Order Side": o.side.to_str(),
                "Qty": o.qty,
                "Price": f"${o.price:,.2f}",
            }
            for o in orders
        ]
        df = pd.DataFrame(input_orders)
        df["Timestamp"] = df["Timestamp"].dt.tz_convert("America/New_York")

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(df.columns), fill_color="lightgray", align="left"
                    ),
                    cells=dict(values=[df[col] for col in df.columns], align="left"),
                )
            ],
        )
        fig.update_layout(
            title=dict(
                text="Orders",
                x=0.5,
                xanchor="center",
                font=dict(size=20),
            ),
            margin=dict(l=20, r=20, t=60, b=20),
        )

        path: str = self.path.format(file_name="orders")
        fig.write_image(path)
        return path

    def generate_portfolio_table(self, positions: list[PositionMetadata]) -> str:
        input_positions: list[dict[str, str | float]] = [
            {
                "Asset": p.asset,
                "Qty": p.qty,
                "Side": p.side.to_str(),
                "Avg Entry Price": f"${p.avg_entry_price:,.2f}",
                "Current Price": f"${p.current_price:,.2f}",
                "Cost Basis": f"${p.cost_basis:,.2f}",
                "Market Value": f"${p.market_value:,.2f}",
                "Unrealized PnL": f"${p.unrealized_pnl:,.2f}",
            }
            for p in positions
        ]
        df = pd.DataFrame(input_positions)

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(df.columns),
                        fill_color="black",
                        align="center",
                        font_color="white",
                    ),
                    cells=dict(
                        values=[df[col] for col in df.columns],
                        fill_color="lightblue",
                        align="left",
                        font_color="black",
                    ),
                )
            ]
        )
        fig.update_layout(
            title=dict(
                text="Portfolio Positions",
                x=0.5,
                xanchor="center",
                font=dict(size=20),
            ),
            autosize=False,
            width=800,  # Make table wider
            height=400,  # Optional: increase if you have many rows
            margin=dict(l=20, r=20, t=60, b=20),
        )

        path: str = self.path.format(file_name="portfolio")
        fig.write_image(path)
        return path

    def generate_pnl_plot(self, df: pd.DataFrame, window: MetricWindow) -> str:
        df["timestamp"] = df["timestamp"].dt.tz_convert("America/New_York")

        fig: go.Figure = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["total_pnl"],
                mode="lines",
                name="Total PnL",
                line=dict(width=2),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["realized_pnl"],
                mode="lines",
                name="Realized PnL",
                line=dict(dash="dash"),
            )
        )

        fig.add_trace(
            go.Scatter(
                x=df["timestamp"],
                y=df["unrealized_pnl"],
                mode="lines",
                name="Unrealized PnL",
                line=dict(dash="dot"),
            )
        )

        tickformat, tickvals = self._resolve_tick_format_and_vals(df, window)

        fig.update_layout(
            title="PnL Over Time",
            xaxis_title="Timestamp",
            yaxis_title="PnL ($)",
            template="plotly_dark",
            height=500,
            margin=dict(l=40, r=40, t=40, b=80),
            legend=dict(x=0.01, y=0.99),
            xaxis=dict(
                type="date",
                tickformat=tickformat,
                tickangle=45,
                ticklabelmode="period",
                tickvals=tickvals,
                rangebreaks=[
                    dict(bounds=["sat", "mon"]),
                    dict(bounds=[16, 9.5], pattern="hour"),
                ],
            ),
        )

        path: str = self.path.format(file_name="pnl")
        fig.write_image(path, width=1200, height=600)
        return path

    @staticmethod
    def _resolve_tick_format_and_vals(
        df: pd.DataFrame, window: MetricWindow
    ) -> tuple[str, list[pd.Timestamp]]:
        tickformat: str = "%m-%d %H:%M"
        dates: list[datetime.date] = df["timestamp"].dt.date.unique()

        if window == MetricWindow.DAILY:
            times = pd.date_range("09:30", "16:00", freq="15min").time
            tickformat = "%H:%M"
        elif window == MetricWindow.WEEKLY:
            times = pd.date_range("09:30", "16:00", freq="65min").time
        elif window == MetricWindow.MONTHLY:
            times = [datetime.time(9, 30), datetime.time(12, 45)]
        elif window == MetricWindow.TOTAL:
            times = [datetime.time(9, 30)]
            tickformat = "%m-%d"
        else:
            raise ValueError(f"Cannot resolve plot tickvals for window {window.name}")

        tickvals: list[pd.Timestamp] = []
        for d in dates:
            for t in times:
                dt = pd.Timestamp.combine(d, t).tz_localize("America/New_York")
                if df["timestamp"].min() <= dt <= df["timestamp"].max():
                    tickvals.append(dt)

        return tickformat, tickvals
