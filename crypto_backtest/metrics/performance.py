"""TradingView-style performance metrics calculator."""

import pandas as pd
import numpy as np
from typing import List, Dict
from crypto_backtest.engine.portfolio import Trade


class PerformanceMetrics:
    """Calculate comprehensive performance metrics from backtest results."""

    @staticmethod
    def calculate(
        trades: List[Trade],
        equity_curve: pd.Series,
        initial_capital: float,
        buy_hold_return: float
    ) -> Dict:
        """
        Calculate all performance metrics.

        Parameters
        ----------
        trades : List[Trade]
            List of completed trades
        equity_curve : pd.Series
            Equity values over time
        initial_capital : float
            Starting capital
        buy_hold_return : float
            Buy and hold benchmark return percentage

        Returns
        -------
        dict
            Dictionary containing all performance metrics
        """
        if len(trades) == 0:
            return PerformanceMetrics._empty_metrics(initial_capital, buy_hold_return)

        # Basic P&L metrics
        total_pnl = sum(t.pnl for t in trades)
        net_profit_pct = (total_pnl / initial_capital) * 100

        winning_trades = [t for t in trades if t.pnl > 0]
        losing_trades = [t for t in trades if t.pnl < 0]

        gross_profit = sum(t.pnl for t in winning_trades) if winning_trades else 0
        gross_loss = sum(t.pnl for t in losing_trades) if losing_trades else 0

        # Trade statistics
        total_trades = len(trades)
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0

        avg_trade = total_pnl / total_trades if total_trades > 0 else 0
        avg_winning_trade = gross_profit / len(winning_trades) if winning_trades else 0
        avg_losing_trade = gross_loss / len(losing_trades) if losing_trades else 0

        # Long vs Short trades
        long_trades = [t for t in trades if t.direction == "long"]
        short_trades = [t for t in trades if t.direction == "short"]

        long_won = len([t for t in long_trades if t.pnl > 0])
        short_won = len([t for t in short_trades if t.pnl > 0])

        long_win_rate = (long_won / len(long_trades)) * 100 if long_trades else 0
        short_win_rate = (short_won / len(short_trades)) * 100 if short_trades else 0

        # Profit factor
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else float('inf')

        # Drawdown metrics
        max_drawdown, max_drawdown_pct = PerformanceMetrics._calculate_max_drawdown(equity_curve)

        # Risk-adjusted metrics
        sharpe_ratio = PerformanceMetrics._calculate_sharpe_ratio(equity_curve, initial_capital)
        sortino_ratio = PerformanceMetrics._calculate_sortino_ratio(equity_curve, initial_capital)

        # Consecutive wins/losses
        max_consecutive_wins = PerformanceMetrics._max_consecutive(trades, "win")
        max_consecutive_losses = PerformanceMetrics._max_consecutive(trades, "loss")

        # Trade duration
        avg_bars_in_trade = np.mean([t.bars_held for t in trades]) if trades else 0

        # Commission
        total_commission = sum(t.commission for t in trades)

        # Final equity
        final_equity = equity_curve.iloc[-1] if len(equity_curve) > 0 else initial_capital

        return {
            "net_profit": total_pnl,
            "net_profit_pct": net_profit_pct,
            "gross_profit": gross_profit,
            "gross_loss": gross_loss,
            "profit_factor": profit_factor,
            "max_drawdown": max_drawdown,
            "max_drawdown_pct": max_drawdown_pct,
            "sharpe_ratio": sharpe_ratio,
            "sortino_ratio": sortino_ratio,
            "total_trades": total_trades,
            "win_rate": win_rate,
            "long_trades": len(long_trades),
            "long_win_rate": long_win_rate,
            "short_trades": len(short_trades),
            "short_win_rate": short_win_rate,
            "avg_trade": avg_trade,
            "avg_winning_trade": avg_winning_trade,
            "avg_losing_trade": avg_losing_trade,
            "max_consecutive_wins": max_consecutive_wins,
            "max_consecutive_losses": max_consecutive_losses,
            "avg_bars_in_trade": avg_bars_in_trade,
            "buy_hold_return": buy_hold_return,
            "total_commission": total_commission,
            "final_equity": final_equity,
        }

    @staticmethod
    def _empty_metrics(initial_capital: float, buy_hold_return: float) -> Dict:
        """Return empty metrics when no trades were made."""
        return {
            "net_profit": 0,
            "net_profit_pct": 0,
            "gross_profit": 0,
            "gross_loss": 0,
            "profit_factor": 0,
            "max_drawdown": 0,
            "max_drawdown_pct": 0,
            "sharpe_ratio": 0,
            "sortino_ratio": 0,
            "total_trades": 0,
            "win_rate": 0,
            "long_trades": 0,
            "long_win_rate": 0,
            "short_trades": 0,
            "short_win_rate": 0,
            "avg_trade": 0,
            "avg_winning_trade": 0,
            "avg_losing_trade": 0,
            "max_consecutive_wins": 0,
            "max_consecutive_losses": 0,
            "avg_bars_in_trade": 0,
            "buy_hold_return": buy_hold_return,
            "total_commission": 0,
            "final_equity": initial_capital,
        }

    @staticmethod
    def _calculate_max_drawdown(equity_curve: pd.Series) -> tuple:
        """
        Calculate maximum drawdown.

        Returns
        -------
        tuple
            (max_drawdown_absolute, max_drawdown_percentage)
        """
        if len(equity_curve) == 0:
            return 0, 0

        running_max = equity_curve.expanding().max()
        drawdown = equity_curve - running_max
        max_dd = drawdown.min()

        max_dd_pct = (drawdown / running_max * 100).min()

        return max_dd, max_dd_pct

    @staticmethod
    def _calculate_sharpe_ratio(equity_curve: pd.Series, initial_capital: float, 
                                risk_free_rate: float = 0.0, periods_per_year: int = 252) -> float:
        """
        Calculate annualized Sharpe ratio.

        Parameters
        ----------
        equity_curve : pd.Series
            Equity values over time
        initial_capital : float
            Starting capital
        risk_free_rate : float
            Annual risk-free rate (default 0)
        periods_per_year : int
            Number of periods per year for annualization (default 252 for daily)

        Returns
        -------
        float
            Sharpe ratio
        """
        if len(equity_curve) < 2:
            return 0

        returns = equity_curve.pct_change().dropna()

        if len(returns) == 0 or returns.std() == 0:
            return 0

        excess_returns = returns - (risk_free_rate / periods_per_year)
        sharpe = excess_returns.mean() / returns.std()
        
        # Annualize
        sharpe_annualized = sharpe * np.sqrt(periods_per_year)

        return sharpe_annualized

    @staticmethod
    def _calculate_sortino_ratio(equity_curve: pd.Series, initial_capital: float,
                                 target_return: float = 0.0, periods_per_year: int = 252) -> float:
        """
        Calculate annualized Sortino ratio (downside deviation only).

        Parameters
        ----------
        equity_curve : pd.Series
            Equity values over time
        initial_capital : float
            Starting capital
        target_return : float
            Target return threshold
        periods_per_year : int
            Number of periods per year for annualization

        Returns
        -------
        float
            Sortino ratio
        """
        if len(equity_curve) < 2:
            return 0

        returns = equity_curve.pct_change().dropna()

        if len(returns) == 0:
            return 0

        downside_returns = returns[returns < target_return]

        if len(downside_returns) == 0:
            return float('inf') if returns.mean() > 0 else 0

        downside_std = downside_returns.std()

        if downside_std == 0:
            return 0

        sortino = (returns.mean() - target_return) / downside_std
        
        # Annualize
        sortino_annualized = sortino * np.sqrt(periods_per_year)

        return sortino_annualized

    @staticmethod
    def _max_consecutive(trades: List[Trade], trade_type: str) -> int:
        """
        Calculate maximum consecutive wins or losses.

        Parameters
        ----------
        trades : List[Trade]
            List of trades
        trade_type : str
            "win" or "loss"

        Returns
        -------
        int
            Maximum consecutive count
        """
        if len(trades) == 0:
            return 0

        max_consecutive = 0
        current_consecutive = 0

        for trade in trades:
            is_win = trade.pnl > 0

            if (trade_type == "win" and is_win) or (trade_type == "loss" and not is_win):
                current_consecutive += 1
                max_consecutive = max(max_consecutive, current_consecutive)
            else:
                current_consecutive = 0

        return max_consecutive

    @staticmethod
    def summary_table(metrics: dict) -> pd.DataFrame:
        """
        Format metrics as a display-friendly DataFrame.

        Parameters
        ----------
        metrics : dict
            Metrics dictionary from calculate()

        Returns
        -------
        pd.DataFrame
            Formatted metrics table
        """
        data = {
            "Metric": [
                "Net Profit",
                "Net Profit %",
                "Gross Profit",
                "Gross Loss",
                "Profit Factor",
                "Max Drawdown",
                "Max Drawdown %",
                "Sharpe Ratio",
                "Sortino Ratio",
                "Total Trades",
                "Win Rate",
                "Long Trades (Won %)",
                "Short Trades (Won %)",
                "Avg Trade",
                "Avg Winning Trade",
                "Avg Losing Trade",
                "Max Consecutive Wins",
                "Max Consecutive Losses",
                "Avg Bars in Trade",
                "Buy & Hold Return",
                "Total Commission",
                "Final Equity"
            ],
            "Value": [
                f"${metrics['net_profit']:.2f}",
                f"{metrics['net_profit_pct']:.2f}%",
                f"${metrics['gross_profit']:.2f}",
                f"${metrics['gross_loss']:.2f}",
                f"{metrics['profit_factor']:.2f}",
                f"${metrics['max_drawdown']:.2f}",
                f"{metrics['max_drawdown_pct']:.2f}%",
                f"{metrics['sharpe_ratio']:.2f}",
                f"{metrics['sortino_ratio']:.2f}",
                f"{metrics['total_trades']}",
                f"{metrics['win_rate']:.2f}%",
                f"{metrics['long_trades']} ({metrics['long_win_rate']:.1f}%)",
                f"{metrics['short_trades']} ({metrics['short_win_rate']:.1f}%)",
                f"${metrics['avg_trade']:.2f}",
                f"${metrics['avg_winning_trade']:.2f}",
                f"${metrics['avg_losing_trade']:.2f}",
                f"{metrics['max_consecutive_wins']}",
                f"{metrics['max_consecutive_losses']}",
                f"{metrics['avg_bars_in_trade']:.1f}",
                f"{metrics['buy_hold_return']:.2f}%",
                f"${metrics['total_commission']:.2f}",
                f"${metrics['final_equity']:.2f}"
            ]
        }

        return pd.DataFrame(data)

    @staticmethod
    def comparison_table(results: List) -> pd.DataFrame:
        """
        Compare multiple backtest results side by side.

        Parameters
        ----------
        results : List[BacktestResult]
            List of backtest results to compare

        Returns
        -------
        pd.DataFrame
            Comparison table
        """
        comparison_data = {}

        for i, result in enumerate(results):
            metrics = result.metrics
            strategy_name = result.strategy_name or f"Strategy {i+1}"

            comparison_data[strategy_name] = {
                "Net Profit %": f"{metrics['net_profit_pct']:.2f}%",
                "Total Trades": metrics['total_trades'],
                "Win Rate": f"{metrics['win_rate']:.2f}%",
                "Profit Factor": f"{metrics['profit_factor']:.2f}",
                "Max Drawdown %": f"{metrics['max_drawdown_pct']:.2f}%",
                "Sharpe Ratio": f"{metrics['sharpe_ratio']:.2f}",
                "Final Equity": f"${metrics['final_equity']:.2f}"
            }

        return pd.DataFrame(comparison_data).T
