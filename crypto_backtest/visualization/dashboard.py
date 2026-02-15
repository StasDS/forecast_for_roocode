"""Complete backtest dashboard with charts and metrics."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from crypto_backtest.engine.backtest import BacktestResult
from crypto_backtest.visualization.candlestick import CandlestickChart
from crypto_backtest.visualization.trades_overlay import TradesOverlay
from crypto_backtest.metrics.performance import PerformanceMetrics


class BacktestDashboard:
    """
    Complete backtest visualization dashboard.
    
    Combines candlestick chart with trades, equity curve, 
    drawdown chart, and metrics summary.
    """

    def __init__(self, result: BacktestResult):
        """
        Initialize dashboard with backtest results.

        Parameters
        ----------
        result : BacktestResult
            Completed backtest result
        """
        self.result = result

    def show(self) -> None:
        """
        Display the complete dashboard in Jupyter.
        
        Shows candlestick chart with trades, equity curve, 
        and drawdown chart together.
        """
        # Display metrics table
        print(f"\n{'='*60}")
        print(f"  {self.result.strategy_name} - {self.result.symbol} ({self.result.timeframe})")
        print(f"  Period: {self.result.period[0]} to {self.result.period[1]}")
        print(f"{'='*60}\n")
        
        metrics_table = PerformanceMetrics.summary_table(self.result.metrics)
        print(metrics_table.to_string(index=False))
        print(f"\n{'='*60}\n")

        # Show price chart with trades
        chart = CandlestickChart(
            self.result.signals_df,
            title=f"{self.result.strategy_name} - {self.result.symbol}"
        )
        fig_price = chart.build(show_volume=True)
        
        # Add trades overlay
        if self.result.trades:
            fig_price = TradesOverlay.add_trades(fig_price, self.result.trades)
        
        # Add indicator overlays if available
        if "sma_fast" in self.result.signals_df.columns:
            chart.add_indicator("SMA Fast", self.result.signals_df["sma_fast"], color="blue")
        if "sma_slow" in self.result.signals_df.columns:
            chart.add_indicator("SMA Slow", self.result.signals_df["sma_slow"], color="orange")
        if "bb_upper" in self.result.signals_df.columns:
            chart.add_indicator("BB Upper", self.result.signals_df["bb_upper"], color="gray", line_dash="dash")
            chart.add_indicator("BB Middle", self.result.signals_df["bb_middle"], color="blue")
            chart.add_indicator("BB Lower", self.result.signals_df["bb_lower"], color="gray", line_dash="dash")
        
        fig_price.show()

        # Show equity curve
        fig_equity = self.show_equity()
        fig_equity.show()

        # Show drawdown chart
        fig_dd = self.show_drawdown()
        fig_dd.show()

    def show_equity(self) -> go.Figure:
        """
        Create and return equity curve chart.

        Returns
        -------
        go.Figure
            Equity curve figure
        """
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.result.equity_curve.index,
                y=self.result.equity_curve.values,
                mode='lines',
                name='Equity',
                line=dict(color='blue', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 100, 255, 0.1)'
            )
        )

        # Add initial capital reference line
        fig.add_hline(
            y=self.result.metrics["final_equity"] - self.result.metrics["net_profit"],
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Capital"
        )

        fig.update_layout(
            title="Equity Curve",
            xaxis_title="Date",
            yaxis_title="Equity ($)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def show_drawdown(self) -> go.Figure:
        """
        Create and return drawdown chart.

        Returns
        -------
        go.Figure
            Drawdown chart figure
        """
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=self.result.drawdown_curve.index,
                y=self.result.drawdown_curve.values,
                mode='lines',
                name='Drawdown',
                line=dict(color='red', width=2),
                fill='tozeroy',
                fillcolor='rgba(255, 0, 0, 0.1)'
            )
        )

        fig.update_layout(
            title="Drawdown Chart",
            xaxis_title="Date",
            yaxis_title="Drawdown (%)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )

        return fig

    def show_trades_table(self) -> pd.DataFrame:
        """
        Return a DataFrame of all trades for display.

        Returns
        -------
        pd.DataFrame
            Trades table
        """
        if not self.result.trades:
            return pd.DataFrame()

        trades_data = []
        for i, trade in enumerate(self.result.trades, 1):
            trades_data.append({
                "Trade #": i,
                "Direction": trade.direction.upper(),
                "Entry Time": trade.entry_time.strftime("%Y-%m-%d %H:%M"),
                "Entry Price": f"${trade.entry_price:.2f}",
                "Exit Time": trade.exit_time.strftime("%Y-%m-%d %H:%M"),
                "Exit Price": f"${trade.exit_price:.2f}",
                "P&L": f"${trade.pnl:.2f}",
                "P&L %": f"{trade.pnl_pct:.2f}%",
                "Bars Held": trade.bars_held,
                "Commission": f"${trade.commission:.2f}"
            })

        return pd.DataFrame(trades_data)

    def save_html(self, filepath: str) -> None:
        """
        Save the complete dashboard as an HTML file.

        Parameters
        ----------
        filepath : str
            Output file path
        """
        # Create combined figure with subplots
        fig = make_subplots(
            rows=3, cols=1,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=(
                f"{self.result.strategy_name} - Price & Trades",
                "Equity Curve",
                "Drawdown"
            ),
            shared_xaxes=True,
            vertical_spacing=0.05
        )

        # Add candlestick to row 1
        chart = CandlestickChart(self.result.signals_df)
        price_fig = chart.build(show_volume=False)
        for trace in price_fig.data:
            fig.add_trace(trace, row=1, col=1)

        # Add equity curve to row 2
        fig.add_trace(
            go.Scatter(
                x=self.result.equity_curve.index,
                y=self.result.equity_curve.values,
                mode='lines',
                name='Equity',
                line=dict(color='blue', width=2)
            ),
            row=2, col=1
        )

        # Add drawdown to row 3
        fig.add_trace(
            go.Scatter(
                x=self.result.drawdown_curve.index,
                y=self.result.drawdown_curve.values,
                mode='lines',
                name='Drawdown',
                line=dict(color='red', width=2),
                fill='tozeroy'
            ),
            row=3, col=1
        )

        fig.update_layout(
            height=1000,
            showlegend=True,
            template='plotly_white',
            hovermode='x unified'
        )

        fig.write_html(filepath)
        print(f"Dashboard saved to {filepath}")
