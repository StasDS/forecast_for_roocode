"""Plotly candlestick chart builder."""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional


class CandlestickChart:
    """
    Interactive Plotly candlestick chart builder.
    
    Supports overlaying indicators and creating subplots for secondary indicators.
    """

    def __init__(self, df: pd.DataFrame, title: str = "Candlestick Chart"):
        """
        Initialize candlestick chart.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with DatetimeIndex
        title : str
            Chart title
        """
        self.df = df
        self.title = title
        self.fig = None
        self.subplot_count = 2  # Start with 2: candlestick and volume

    def build(self, show_volume: bool = True) -> go.Figure:
        """
        Build the Plotly figure.

        Parameters
        ----------
        show_volume : bool
            Whether to include volume subplot

        Returns
        -------
        go.Figure
            Plotly figure object
        """
        # Create subplots
        if show_volume:
            self.fig = make_subplots(
                rows=2, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.03,
                row_heights=[0.7, 0.3],
                subplot_titles=(self.title, "Volume")
            )
        else:
            self.fig = make_subplots(
                rows=1, cols=1,
                subplot_titles=(self.title,)
            )

        # Add candlestick
        self.fig.add_trace(
            go.Candlestick(
                x=self.df.index,
                open=self.df["open"],
                high=self.df["high"],
                low=self.df["low"],
                close=self.df["close"],
                name="OHLC",
                increasing_line_color='green',
                decreasing_line_color='red'
            ),
            row=1, col=1
        )

        # Add volume bars if requested
        if show_volume:
            colors = ['green' if self.df["close"].iloc[i] >= self.df["open"].iloc[i] 
                     else 'red' for i in range(len(self.df))]
            
            self.fig.add_trace(
                go.Bar(
                    x=self.df.index,
                    y=self.df["volume"],
                    name="Volume",
                    marker_color=colors,
                    showlegend=False
                ),
                row=2, col=1
            )

        # Update layout
        self.fig.update_layout(
            xaxis_rangeslider_visible=False,
            height=600,
            hovermode='x unified',
            template='plotly_white'
        )

        self.fig.update_xaxes(title_text="Date", row=2 if show_volume else 1, col=1)
        self.fig.update_yaxes(title_text="Price", row=1, col=1)
        if show_volume:
            self.fig.update_yaxes(title_text="Volume", row=2, col=1)

        return self.fig

    def add_indicator(
        self,
        name: str,
        series: pd.Series,
        row: int = 1,
        color: str = "blue",
        line_width: int = 2,
        line_dash: Optional[str] = None
    ) -> None:
        """
        Add a line indicator overlay to existing chart.

        Parameters
        ----------
        name : str
            Indicator name for legend
        series : pd.Series
            Indicator values with DatetimeIndex
        row : int
            Which subplot row to add to (default 1 = main chart)
        color : str
            Line color
        line_width : int
            Line width
        line_dash : str, optional
            Line style ('solid', 'dash', 'dot', 'dashdot')
        """
        if self.fig is None:
            self.build()

        self.fig.add_trace(
            go.Scatter(
                x=series.index,
                y=series.values,
                mode='lines',
                name=name,
                line=dict(color=color, width=line_width, dash=line_dash)
            ),
            row=row, col=1
        )

    def add_subplot_indicator(
        self,
        name: str,
        series: pd.Series,
        color: str = "purple",
        chart_type: str = "line"
    ) -> None:
        """
        Add indicator as a new subplot row (e.g., RSI, MACD).

        Parameters
        ----------
        name : str
            Indicator name
        series : pd.Series
            Indicator values
        color : str
            Line/bar color
        chart_type : str
            "line" or "bar"
        """
        # This is a simplified version - would need to rebuild subplots to add new rows
        # For now, just add to the main chart
        self.add_indicator(name, series, row=1, color=color)

    def show(self) -> None:
        """Render the chart in Jupyter notebook."""
        if self.fig is None:
            self.build()
        self.fig.show()

    def save(self, filepath: str) -> None:
        """
        Save chart as HTML file.

        Parameters
        ----------
        filepath : str
            Output file path
        """
        if self.fig is None:
            self.build()
        self.fig.write_html(filepath)
