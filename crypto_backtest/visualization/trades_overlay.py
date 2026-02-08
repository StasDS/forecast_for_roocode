"""Trade entry/exit markers overlay for charts."""

import plotly.graph_objects as go
from typing import List
from crypto_backtest.engine.portfolio import Trade


class TradesOverlay:
    """Add trade markers and annotations to existing candlestick charts."""

    @staticmethod
    def add_trades(fig: go.Figure, trades: List[Trade], row: int = 1) -> go.Figure:
        """
        Add trade markers to an existing Plotly figure.

        Parameters
        ----------
        fig : go.Figure
            Existing Plotly figure (typically candlestick chart)
        trades : List[Trade]
            List of completed trades
        row : int
            Which subplot row to add markers to

        Returns
        -------
        go.Figure
            Updated figure with trade markers
        """
        if not trades:
            return fig

        # Separate long and short trades
        long_entries = []
        long_exits = []
        short_entries = []
        short_exits = []

        for trade in trades:
            if trade.direction == "long":
                long_entries.append((trade.entry_time, trade.entry_price, trade.pnl, trade.pnl_pct))
                long_exits.append((trade.exit_time, trade.exit_price, trade.pnl, trade.pnl_pct))
            else:  # short
                short_entries.append((trade.entry_time, trade.entry_price, trade.pnl, trade.pnl_pct))
                short_exits.append((trade.exit_time, trade.exit_price, trade.pnl, trade.pnl_pct))

        # Add long entry markers (green triangle up)
        if long_entries:
            times, prices, pnls, pnl_pcts = zip(*long_entries)
            hover_text = [f"Long Entry<br>Price: ${p:.2f}<br>P&L: ${pnl:.2f} ({pnl_pct:.2f}%)" 
                         for p, pnl, pnl_pct in zip(prices, pnls, pnl_pcts)]
            
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=prices,
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='green',
                        line=dict(color='darkgreen', width=1)
                    ),
                    name='Long Entry',
                    hovertext=hover_text,
                    hoverinfo='text',
                    showlegend=True
                ),
                row=row, col=1
            )

        # Add long exit markers (green triangle down)
        if long_exits:
            times, prices, pnls, pnl_pcts = zip(*long_exits)
            hover_text = [f"Long Exit<br>Price: ${p:.2f}<br>P&L: ${pnl:.2f} ({pnl_pct:.2f}%)" 
                         for p, pnl, pnl_pct in zip(prices, pnls, pnl_pcts)]
            
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=prices,
                    mode='markers',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='lightgreen',
                        line=dict(color='green', width=1)
                    ),
                    name='Long Exit',
                    hovertext=hover_text,
                    hoverinfo='text',
                    showlegend=True
                ),
                row=row, col=1
            )

        # Add short entry markers (red triangle down)
        if short_entries:
            times, prices, pnls, pnl_pcts = zip(*short_entries)
            hover_text = [f"Short Entry<br>Price: ${p:.2f}<br>P&L: ${pnl:.2f} ({pnl_pct:.2f}%)" 
                         for p, pnl, pnl_pct in zip(prices, pnls, pnl_pcts)]
            
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=prices,
                    mode='markers',
                    marker=dict(
                        symbol='triangle-down',
                        size=12,
                        color='red',
                        line=dict(color='darkred', width=1)
                    ),
                    name='Short Entry',
                    hovertext=hover_text,
                    hoverinfo='text',
                    showlegend=True
                ),
                row=row, col=1
            )

        # Add short exit markers (red triangle up)
        if short_exits:
            times, prices, pnls, pnl_pcts = zip(*short_exits)
            hover_text = [f"Short Exit<br>Price: ${p:.2f}<br>P&L: ${pnl:.2f} ({pnl_pct:.2f}%)" 
                         for p, pnl, pnl_pct in zip(prices, pnls, pnl_pcts)]
            
            fig.add_trace(
                go.Scatter(
                    x=times,
                    y=prices,
                    mode='markers',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color='lightcoral',
                        line=dict(color='red', width=1)
                    ),
                    name='Short Exit',
                    hovertext=hover_text,
                    hoverinfo='text',
                    showlegend=True
                ),
                row=row, col=1
            )

        # Optionally add lines connecting entry to exit
        # (Commented out to avoid cluttering the chart)
        # for trade in trades:
        #     color = 'green' if trade.pnl > 0 else 'red'
        #     fig.add_trace(
        #         go.Scatter(
        #             x=[trade.entry_time, trade.exit_time],
        #             y=[trade.entry_price, trade.exit_price],
        #             mode='lines',
        #             line=dict(color=color, width=1, dash='dot'),
        #             showlegend=False,
        #             hoverinfo='skip'
        #         ),
        #         row=row, col=1
        #     )

        return fig
