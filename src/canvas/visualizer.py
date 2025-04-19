import datetime

import pandas as pd
import plotly.graph_objects as go

from agent.profiles import Profile
from stubs import MetricWindow, OrderMetadata


class DataVisualizer:

    def __init__(self, profile: Profile) -> None:
        self.path: str = f"/tmp/{profile.broker_name}-{{file_name}}.png"

    def generate_orders_table(self, orders: list[OrderMetadata]) -> str:
        input_orders: list[dict[str, str | float]] = [
            {
                "timestamp": o.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "asset": o.asset,
                "order type": o.type.to_str(),
                "order side": o.side.to_str(),
                "qty": o.qty,
                "price": f"${o.price:,.2f}",
            }
            for o in orders
        ]
        df = pd.DataFrame(input_orders)

        fig = go.Figure(
            data=[
                go.Table(
                    header=dict(
                        values=list(df.columns), fill_color="lightgray", align="left"
                    ),
                    cells=dict(values=[df[col] for col in df.columns], align="left"),
                )
            ]
        )

        path: str = self.path.format(file_name="orders")
        fig.write_image(path)
        return path

    def generate_pnl_plot(self, df: pd.DataFrame, window: MetricWindow) -> str:
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

    def _resolve_tick_format_and_vals(
        df: pd.DataFrame, window: MetricWindow
    ) -> tuple[str, list[pd.Timestamp]]:
        df["timestamp"] = df["timestamp"].dt.tz_convert("America/New_York")

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
