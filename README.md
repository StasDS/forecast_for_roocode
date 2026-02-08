# Crypto Backtest Module

A lightweight Python module for cryptocurrency trading strategy backtesting and analysis, designed for personal use in Jupyter Notebooks.

## Features

- **Fast Backtesting**: Vectorized calculations for rapid parameter optimization
- **Visual Analysis**: Interactive Plotly charts with trade overlays
- **Dual Modes**: 
  - Fast mode for parameter optimization (metrics only)
  - Full mode for detailed visualization (complete trade log + charts)
- **Flexible Data Loading**: 
  - Binance API (no authentication required)
  - Local CSV/Parquet files
- **TradingView-Style Metrics**: Comprehensive performance analytics
- **Easy Strategy Development**: Simple class-based strategy interface
- **Parameter Optimization**: Grid search optimizer for strategy tuning

## Installation

```bash
pip install -r requirements.txt
```

For development:
```bash
pip install -e ".[dev]"
```

## Quick Start

### Basic Backtest

```python
from crypto_backtest import BinanceLoader, SmaCrossover, BacktestEngine

# Load data
loader = BinanceLoader()
df = loader.load("BTCUSDT", "1h", start="2025-01-01", end="2025-06-01")

# Create strategy
strategy = SmaCrossover(fast_period=10, slow_period=30)

# Run backtest
engine = BacktestEngine(strategy, df, initial_capital=10000)
result = engine.run(mode="fast")

# View metrics
print(result.metrics)
```

### Visual Backtest with Dashboard

```python
# Run in full mode for visualization
result = engine.run(mode="full")

# Display interactive dashboard
from crypto_backtest import BacktestDashboard
dashboard = BacktestDashboard(result)
dashboard.show()
```

### Parameter Optimization

```python
from crypto_backtest import GridOptimizer

optimizer = GridOptimizer(
    strategy_class=SmaCrossover,
    data=df,
    param_grid={
        "fast_period": range(5, 25, 5),
        "slow_period": range(20, 60, 10),
    },
    metric="sharpe_ratio"
)

results = optimizer.run()
best_params = optimizer.get_best_params()
print(f"Best parameters: {best_params}")
```

## Custom Strategy Development

```python
from crypto_backtest import BaseStrategy
import pandas as pd

class MyStrategy(BaseStrategy):
    default_params = {"rsi_period": 14, "overbought": 70, "oversold": 30}

    def indicators(self, df):
        # Calculate RSI
        delta = df["close"].diff()
        gain = delta.where(delta > 0, 0).rolling(self.params.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.params.rsi_period).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100 / (1 + rs))
        return df

    def signal(self, df):
        df = self.indicators(df)
        signals = pd.Series(0, index=df.index)
        
        # Buy when oversold
        signals[df["rsi"] < self.params.oversold] = 1
        
        # Sell when overbought
        signals[df["rsi"] > self.params.overbought] = -1
        
        return signals
```

## Module Structure

```
crypto_backtest/
├── data/               # Data loaders (Binance API, CSV)
├── strategy/           # Strategy base classes and examples
├── engine/             # Backtesting engine and optimizer
├── metrics/            # Performance metrics calculator
├── visualization/      # Interactive charts and dashboards
└── utils/              # Helper functions
```

## Built-in Strategies

- **SmaCrossover**: Simple Moving Average crossover strategy
- **RsiStrategy**: RSI overbought/oversold strategy
- **BollingerStrategy**: Bollinger Bands mean reversion strategy

## Performance Metrics

The module calculates comprehensive TradingView-style metrics:

- Net Profit & Net Profit %
- Gross Profit & Gross Loss
- Profit Factor
- Max Drawdown (absolute & percentage)
- Sharpe Ratio
- Sortino Ratio
- Win Rate
- Long/Short Trade Statistics
- Average Trade P&L
- Consecutive Wins/Losses
- Average Bars in Trade
- Buy & Hold Benchmark
- Total Commissions

## Data Sources

### Binance API
```python
from crypto_backtest import BinanceLoader

loader = BinanceLoader()
df = loader.load("ETHUSDT", "4h", start="2024-01-01", end="2025-01-01")
```

### Local Files
```python
from crypto_backtest import CsvLoader

loader = CsvLoader("my_data.csv")
df = loader.load(start="2024-01-01", end="2025-01-01")
```

## Visualization Features

- Interactive candlestick charts with Plotly
- Trade entry/exit markers
- Indicator overlays (SMA, Bollinger Bands, etc.)
- Equity curve visualization
- Drawdown charts
- Combined dashboard view

## Configuration Options

### BacktestEngine Parameters

- `initial_capital`: Starting capital (default: 10000)
- `commission`: Commission rate per trade (default: 0.001 = 0.1%)
- `position_size`: Fraction of capital per trade (default: 1.0)
- `trade_on`: Execute on "close" or "open" of next bar (default: "close")
- `allow_short`: Allow short positions (default: True)

## Example Notebook

See [`notebooks/example_backtest.ipynb`](notebooks/example_backtest.ipynb) for complete usage examples.

## Requirements

- Python 3.8+
- pandas >= 2.0
- numpy >= 1.24
- plotly >= 5.18
- requests >= 2.31

## Performance

- Fast mode: < 5 seconds for 1 year of daily data
- Supports vectorized operations for rapid parameter scanning
- Can test thousands of parameter combinations efficiently

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

MIT License

## Disclaimer

This software is for educational and research purposes only. It does not constitute financial advice. Trading cryptocurrencies carries risk, and past performance does not guarantee future results. Always do your own research and never risk more than you can afford to lose.
