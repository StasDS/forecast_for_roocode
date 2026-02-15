"""Core backtesting engine."""

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Optional, List
from crypto_backtest.strategy.base import BaseStrategy
from crypto_backtest.engine.portfolio import Portfolio, Trade


@dataclass
class BacktestResult:
    """Results container for a completed backtest."""
    
    metrics: dict  # TradingView-style performance metrics
    trades: List[Trade]  # completed trades (empty in fast mode)
    equity_curve: pd.Series  # equity over time
    drawdown_curve: pd.Series  # drawdown over time
    signals_df: pd.DataFrame  # OHLCV + indicators + signals
    strategy_name: str
    symbol: str
    timeframe: str
    period: tuple  # (start, end)


class BacktestEngine:
    """
    Core backtesting engine supporting two modes:
    - fast: vectorized calculation for optimization (metrics only)
    - full: candle-by-candle for visualization (metrics + detailed trades)
    """

    def __init__(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        initial_capital: float = 10000.0,
        commission: float = 0.001,  # 0.1% per trade (Binance spot default)
        position_size: float = 1.0,  # fraction of capital per trade
        trade_on: str = "close",  # execute on "close" or "open" of next bar
        allow_short: bool = True,
        symbol: str = "UNKNOWN",
        timeframe: str = "1h"
    ):
        """
        Initialize backtesting engine.

        Parameters
        ----------
        strategy : BaseStrategy
            Trading strategy instance
        data : pd.DataFrame
            OHLCV data with DatetimeIndex
        initial_capital : float
            Starting capital amount
        commission : float
            Commission rate per trade (e.g., 0.001 = 0.1%)
        position_size : float
            Fraction of capital to use per trade (0-1)
        trade_on : str
            "close" to execute on current bar close, "open" for next bar open
        allow_short : bool
            Allow short positions
        symbol : str
            Trading pair symbol
        timeframe : str
            Candle timeframe
        """
        self.strategy = strategy
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.position_size = position_size
        self.trade_on = trade_on
        self.allow_short = allow_short
        self.symbol = symbol
        self.timeframe = timeframe

    def run(self, mode: str = "fast") -> BacktestResult:
        """
        Run backtest.

        Parameters
        ----------
        mode : str
            "fast": returns metrics only (no trade log detail)
            "full": returns metrics + detailed trade log + equity curve

        Returns
        -------
        BacktestResult
            Complete backtest results
        """
        # Generate signals
        df = self.strategy.indicators(self.data)
        signals = self.strategy.signal(df)
        df["signal"] = signals

        if mode == "fast":
            return self._run_fast(df, signals)
        elif mode == "full":
            return self._run_full(df, signals)
        else:
            raise ValueError(f"Invalid mode: {mode}. Choose 'fast' or 'full'.")

    def _run_fast(self, df: pd.DataFrame, signals: pd.Series) -> BacktestResult:
        """
        Fast vectorized backtest for parameter optimization.
        
        Returns metrics only, no detailed trade log.
        """
        # Use vectorized calculation
        portfolio = self._vectorized_backtest(df, signals)
        
        # Calculate metrics
        from crypto_backtest.metrics.performance import PerformanceMetrics
        
        # Calculate buy and hold return
        buy_hold_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
        
        metrics = PerformanceMetrics.calculate(
            trades=portfolio.trades,
            equity_curve=pd.Series([eq for _, eq in portfolio.equity_curve], 
                                   index=[ts for ts, _ in portfolio.equity_curve]),
            initial_capital=self.initial_capital,
            buy_hold_return=buy_hold_return
        )
        
        equity_series = pd.Series([eq for _, eq in portfolio.equity_curve], 
                                  index=[ts for ts, _ in portfolio.equity_curve])
        
        drawdown_curve = self._calculate_drawdown(equity_series)
        
        return BacktestResult(
            metrics=metrics,
            trades=[],  # Empty in fast mode
            equity_curve=equity_series,
            drawdown_curve=drawdown_curve,
            signals_df=df,
            strategy_name=self.strategy.name(),
            symbol=self.symbol,
            timeframe=self.timeframe,
            period=(str(df.index[0]), str(df.index[-1]))
        )

    def _run_full(self, df: pd.DataFrame, signals: pd.Series) -> BacktestResult:
        """
        Full candle-by-candle backtest with detailed trade logging.
        """
        portfolio = Portfolio(
            initial_capital=self.initial_capital,
            current_capital=self.initial_capital
        )
        
        # Iterate through each candle
        for i in range(len(df)):
            timestamp = df.index[i]
            row = df.iloc[i]
            signal = signals.iloc[i]
            
            current_price = row["close"] if self.trade_on == "close" else row["open"]
            
            # Record equity at this point
            equity = portfolio.get_equity(current_price)
            portfolio.equity_curve.append((timestamp, equity))
            
            # Process signal
            if signal != 0 and not pd.isna(signal):
                self._process_signal(portfolio, signal, timestamp, current_price, i)
        
        # Close any open position at the end
        if portfolio.position != 0:
            last_price = df.iloc[-1]["close"]
            self._close_position(portfolio, df.index[-1], last_price, len(df) - 1)
        
        # Calculate metrics
        from crypto_backtest.metrics.performance import PerformanceMetrics
        
        buy_hold_return = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
        
        equity_series = pd.Series([eq for _, eq in portfolio.equity_curve], 
                                  index=[ts for ts, _ in portfolio.equity_curve])
        
        metrics = PerformanceMetrics.calculate(
            trades=portfolio.trades,
            equity_curve=equity_series,
            initial_capital=self.initial_capital,
            buy_hold_return=buy_hold_return
        )
        
        drawdown_curve = self._calculate_drawdown(equity_series)
        
        return BacktestResult(
            metrics=metrics,
            trades=portfolio.trades,
            equity_curve=equity_series,
            drawdown_curve=drawdown_curve,
            signals_df=df,
            strategy_name=self.strategy.name(),
            symbol=self.symbol,
            timeframe=self.timeframe,
            period=(str(df.index[0]), str(df.index[-1]))
        )

    def _process_signal(self, portfolio: Portfolio, signal: int, 
                       timestamp: pd.Timestamp, price: float, bar_index: int):
        """Process a trading signal."""
        
        # Close existing position if any
        if portfolio.position != 0:
            self._close_position(portfolio, timestamp, price, bar_index)
        
        # Open new position based on signal
        if signal == 1:  # Long signal
            self._open_position(portfolio, "long", timestamp, price, bar_index)
        elif signal == -1 and self.allow_short:  # Short signal
            self._open_position(portfolio, "short", timestamp, price, bar_index)

    def _open_position(self, portfolio: Portfolio, direction: str, 
                      timestamp: pd.Timestamp, price: float, bar_index: int):
        """Open a new position."""
        
        # Calculate position size
        capital_to_use = portfolio.current_capital * self.position_size
        commission_cost = capital_to_use * self.commission
        net_capital = capital_to_use - commission_cost
        
        position_size = net_capital / price
        
        portfolio.position = position_size
        portfolio.direction = direction
        portfolio.open_trade = {
            "entry_time": timestamp,
            "entry_price": price,
            "entry_bar": bar_index,
            "direction": direction,
            "quantity": position_size,
            "commission": commission_cost
        }

    def _close_position(self, portfolio: Portfolio, timestamp: pd.Timestamp, 
                       price: float, bar_index: int):
        """Close the current position and record the trade."""
        
        if portfolio.open_trade is None:
            return
        
        open_trade = portfolio.open_trade
        
        # Calculate P&L
        if open_trade["direction"] == "long":
            pnl = (price - open_trade["entry_price"]) * portfolio.position
        else:  # short
            pnl = (open_trade["entry_price"] - price) * portfolio.position
        
        # Subtract exit commission
        exit_commission = portfolio.position * price * self.commission
        total_commission = open_trade["commission"] + exit_commission
        pnl -= exit_commission
        
        # Update capital
        portfolio.current_capital += pnl
        
        # Calculate percentage P&L
        invested = open_trade["entry_price"] * portfolio.position + open_trade["commission"]
        pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
        
        # Record trade
        trade = Trade(
            entry_time=open_trade["entry_time"],
            exit_time=timestamp,
            direction=open_trade["direction"],
            entry_price=open_trade["entry_price"],
            exit_price=price,
            quantity=portfolio.position,
            pnl=pnl,
            pnl_pct=pnl_pct,
            bars_held=bar_index - open_trade["entry_bar"],
            commission=total_commission
        )
        
        portfolio.trades.append(trade)
        
        # Reset position
        portfolio.position = 0
        portfolio.direction = None
        portfolio.open_trade = None

    def _vectorized_backtest(self, df: pd.DataFrame, signals: pd.Series) -> Portfolio:
        """
        Vectorized backtest for speed (used in fast mode).
        
        This is a simplified version that doesn't track individual trades
        but provides quick performance metrics.
        """
        portfolio = Portfolio(
            initial_capital=self.initial_capital,
            current_capital=self.initial_capital
        )
        
        # Create position series from signals
        positions = signals.copy()
        positions = positions.fillna(0)
        
        # Forward fill positions (hold until next signal)
        # Convert signals to positions: 1 = long, -1 = short, 0 = flat
        position_series = pd.Series(0, index=df.index)
        
        current_pos = 0
        for i in range(len(signals)):
            if signals.iloc[i] == 1:
                current_pos = 1
            elif signals.iloc[i] == -1:
                current_pos = -1 if self.allow_short else 0
            position_series.iloc[i] = current_pos
        
        # Calculate returns
        price_changes = df["close"].pct_change()
        
        # Strategy returns (with position)
        strategy_returns = position_series.shift(1) * price_changes
        
        # Count trades (position changes)
        position_changes = position_series.diff().abs()
        num_trades = int(position_changes.sum() / 2) if (position_changes.sum() / 2) > 0 else 0
        
        # Apply commissions on each trade
        total_commission = num_trades * 2 * self.commission  # entry + exit
        
        # Calculate equity curve
        equity = self.initial_capital * (1 + strategy_returns.fillna(0)).cumprod()
        equity = equity * (1 - total_commission) if num_trades > 0 else equity
        
        # Store equity curve
        for timestamp, eq_value in equity.items():
            portfolio.equity_curve.append((timestamp, eq_value))
        
        portfolio.current_capital = equity.iloc[-1]
        
        # Generate approximate trades for metrics (simplified)
        self._generate_trades_from_positions(portfolio, df, position_series)
        
        return portfolio

    def _generate_trades_from_positions(self, portfolio: Portfolio, 
                                       df: pd.DataFrame, positions: pd.Series):
        """Generate trade objects from position series for metrics calculation."""
        
        position_changes = positions.diff()
        
        open_trade = None
        
        for i in range(1, len(positions)):
            if position_changes.iloc[i] != 0:
                # Position changed
                current_pos = positions.iloc[i]
                prev_pos = positions.iloc[i-1]
                
                timestamp = df.index[i]
                price = df["close"].iloc[i]
                
                # Close existing trade if any
                if open_trade is not None:
                    exit_price = price
                    if open_trade["direction"] == "long":
                        pnl = (exit_price - open_trade["entry_price"]) * open_trade["quantity"]
                    else:
                        pnl = (open_trade["entry_price"] - exit_price) * open_trade["quantity"]
                    
                    commission = open_trade["quantity"] * (open_trade["entry_price"] + exit_price) * self.commission
                    pnl -= commission
                    
                    invested = open_trade["entry_price"] * open_trade["quantity"]
                    pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
                    
                    trade = Trade(
                        entry_time=open_trade["entry_time"],
                        exit_time=timestamp,
                        direction=open_trade["direction"],
                        entry_price=open_trade["entry_price"],
                        exit_price=exit_price,
                        quantity=open_trade["quantity"],
                        pnl=pnl,
                        pnl_pct=pnl_pct,
                        bars_held=i - open_trade["entry_bar"],
                        commission=commission
                    )
                    portfolio.trades.append(trade)
                    open_trade = None
                
                # Open new trade if position is not flat
                if current_pos != 0:
                    direction = "long" if current_pos > 0 else "short"
                    capital_to_use = self.initial_capital * self.position_size
                    quantity = capital_to_use / price
                    
                    open_trade = {
                        "entry_time": timestamp,
                        "entry_price": price,
                        "entry_bar": i,
                        "direction": direction,
                        "quantity": quantity
                    }
        
        # Close final trade if still open
        if open_trade is not None:
            exit_price = df["close"].iloc[-1]
            timestamp = df.index[-1]
            
            if open_trade["direction"] == "long":
                pnl = (exit_price - open_trade["entry_price"]) * open_trade["quantity"]
            else:
                pnl = (open_trade["entry_price"] - exit_price) * open_trade["quantity"]
            
            commission = open_trade["quantity"] * (open_trade["entry_price"] + exit_price) * self.commission
            pnl -= commission
            
            invested = open_trade["entry_price"] * open_trade["quantity"]
            pnl_pct = (pnl / invested) * 100 if invested > 0 else 0
            
            trade = Trade(
                entry_time=open_trade["entry_time"],
                exit_time=timestamp,
                direction=open_trade["direction"],
                entry_price=open_trade["entry_price"],
                exit_price=exit_price,
                quantity=open_trade["quantity"],
                pnl=pnl,
                pnl_pct=pnl_pct,
                bars_held=len(df) - 1 - open_trade["entry_bar"],
                commission=commission
            )
            portfolio.trades.append(trade)

    def _calculate_drawdown(self, equity_curve: pd.Series) -> pd.Series:
        """Calculate drawdown series from equity curve."""
        
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max * 100
        
        return drawdown
