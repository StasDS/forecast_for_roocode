Product Requirements Document (PRD)
1. Overview
Create a Python module for personal use designed for local backtesting and analysis of various cryptocurrency trading strategies in Jupyter notebooks.

2. Core Objectives
Enable rapid backtesting of cryptocurrency trading strategies using candle data tables

Support user-defined time periods for analysis

Generate standardized strategy performance metrics similar to TradingView's market simulator

Provide both visual and non-visual backtesting modes

3. Functional Requirements
3.1 Backtesting Engine
FR1: Calculate backtest results from cryptocurrency candle data tables

FR2: Support user-specified time periods for analysis

FR3: Output standardized strategy performance metrics (Sharpe ratio, win rate, max drawdown, etc.)

FR4: Implement two operational modes:

FR4.1: Non-visual mode for parameter optimization and batch processing

FR4.2: Visual mode with graphical representation of results

3.2 Visualization Components
FR5: Generate standard candlestick charts from DataFrame data

FR6: Visualize backtest trades directly on price charts

FR7: Provide interactive chart capabilities for:

Zooming and panning through historical data

Hover tooltips displaying trade details

Custom indicator overlay options

3.3 Data Integration
FR8: Accept pandas DataFrames with OHLCV (Open, High, Low, Close, Volume) data

FR9: Support multiple timeframes (1m, 5m, 1h, 4h, 1d, etc.)

FR10: Compatible with common cryptocurrency data formats (CSV, JSON, parquet)

4. Technical Specifications
4.1 Architecture
TS1: Pure Python implementation with minimal dependencies

TS2: Jupyter notebook compatible with seamless integration

TS3: Modular design allowing strategy customization

TS4: Use vectorized operations for performance optimization

4.2 Performance Requirements
PR1: Fast backtest calculations (optimized for speed over precision in batch mode)

PR2: Memory-efficient handling of large historical datasets

PR3: Support for parallel processing in parameter search mode

4.3 Output Requirements
OR1: Generate comprehensive performance reports including:

Equity curve

Trade listing with entry/exit points

Risk metrics

Period returns

OR2: Export results to CSV/JSON formats

OR3: Save visualizations as HTML/interactive plots

5. User Experience
5.1 Interface Requirements
IR1: Simple function-based API for quick implementation

IR2: Clear documentation with usage examples

IR3: Intuitive parameter configuration

IR4: Real-time progress indicators for long-running backtests

5.2 Integration Requirements
IR5: Compatible with popular data analysis libraries (pandas, numpy)

IR6: Support for common technical indicators (TA-Lib compatible)

IR7: Easy integration with existing Jupyter workflows

6. Success Metrics
Backtest execution time under 5 seconds for 1-year daily data

Support for at least 10 simultaneous technical indicators

Accurate reproduction of TradingView-like performance metrics

Interactive visualization load time under 3 seconds

7. Dependencies & Constraints
Python 3.8+ environment

Jupyter notebook/lab installation

Standard scientific stack (pandas, numpy, matplotlib)

Optional: Plotly for interactive visualizations