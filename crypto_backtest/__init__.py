"""
Crypto Backtest Module

A Python module for cryptocurrency trading strategy backtesting and analysis.
"""

from crypto_backtest.data.binance_loader import BinanceLoader
from crypto_backtest.data.csv_loader import CsvLoader
from crypto_backtest.strategy.base import BaseStrategy, StrategyParams
from crypto_backtest.strategy.examples import SmaCrossover, RsiStrategy, BollingerStrategy
from crypto_backtest.engine.backtest import BacktestEngine, BacktestResult
from crypto_backtest.engine.optimizer import GridOptimizer
from crypto_backtest.engine.portfolio import Trade, Portfolio
from crypto_backtest.metrics.performance import PerformanceMetrics
from crypto_backtest.visualization.candlestick import CandlestickChart
from crypto_backtest.visualization.trades_overlay import TradesOverlay
from crypto_backtest.visualization.dashboard import BacktestDashboard

__version__ = "0.1.0"

__all__ = [
    "BinanceLoader",
    "CsvLoader",
    "BaseStrategy",
    "StrategyParams",
    "SmaCrossover",
    "RsiStrategy",
    "BollingerStrategy",
    "BacktestEngine",
    "BacktestResult",
    "GridOptimizer",
    "Trade",
    "Portfolio",
    "PerformanceMetrics",
    "CandlestickChart",
    "TradesOverlay",
    "BacktestDashboard",
]
