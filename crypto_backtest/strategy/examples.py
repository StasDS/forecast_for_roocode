"""Example trading strategies for demonstration and testing."""

import pandas as pd
import numpy as np
from crypto_backtest.strategy.base import BaseStrategy


class SmaCrossover(BaseStrategy):
    """
    Simple Moving Average Crossover Strategy.
    
    Generates buy signal when fast SMA crosses above slow SMA.
    Generates sell signal when fast SMA crosses below slow SMA.
    """

    default_params = {"fast_period": 10, "slow_period": 30}

    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add fast and slow SMAs to the DataFrame."""
        df = df.copy()
        df["sma_fast"] = df["close"].rolling(window=self.params.fast_period).mean()
        df["sma_slow"] = df["close"].rolling(window=self.params.slow_period).mean()
        return df

    def signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on SMA crossover.
        
        Returns 1 when fast > slow (bullish), -1 when fast < slow (bearish).
        """
        df = self.indicators(df)
        
        # Create position series: 1 when fast > slow, 0 otherwise
        position = (df["sma_fast"] > df["sma_slow"]).astype(int)
        
        # Generate signals from position changes
        # diff() gives: 1 for long entry, -1 for long exit
        signals = position.diff()
        
        # Replace -1 with -1 (exit long = enter short in our system)
        # Keep 1 for long entry
        signals = signals.fillna(0)
        
        return signals


class RsiStrategy(BaseStrategy):
    """
    RSI (Relative Strength Index) Strategy.
    
    Buys when RSI crosses below oversold threshold.
    Sells when RSI crosses above overbought threshold.
    """

    default_params = {"rsi_period": 14, "oversold": 30, "overbought": 70}

    def _calculate_rsi(self, series: pd.Series, period: int) -> pd.Series:
        """Calculate RSI indicator."""
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        
        avg_gain = gain.rolling(window=period).mean()
        avg_loss = loss.rolling(window=period).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi

    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add RSI to the DataFrame."""
        df = df.copy()
        df["rsi"] = self._calculate_rsi(df["close"], self.params.rsi_period)
        return df

    def signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on RSI levels.
        
        Returns 1 when RSI < oversold, -1 when RSI > overbought.
        """
        df = self.indicators(df)
        
        signals = pd.Series(0, index=df.index)
        
        # Buy signal when RSI crosses below oversold
        oversold_cross = (df["rsi"] < self.params.oversold) & (df["rsi"].shift(1) >= self.params.oversold)
        signals[oversold_cross] = 1
        
        # Sell signal when RSI crosses above overbought
        overbought_cross = (df["rsi"] > self.params.overbought) & (df["rsi"].shift(1) <= self.params.overbought)
        signals[overbought_cross] = -1
        
        return signals


class BollingerStrategy(BaseStrategy):
    """
    Bollinger Bands Strategy.
    
    Buys when price touches lower band.
    Sells when price touches upper band.
    """

    default_params = {"period": 20, "num_std": 2.0}

    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add Bollinger Bands to the DataFrame."""
        df = df.copy()
        
        # Calculate middle band (SMA)
        df["bb_middle"] = df["close"].rolling(window=self.params.period).mean()
        
        # Calculate standard deviation
        rolling_std = df["close"].rolling(window=self.params.period).std()
        
        # Calculate upper and lower bands
        df["bb_upper"] = df["bb_middle"] + (rolling_std * self.params.num_std)
        df["bb_lower"] = df["bb_middle"] - (rolling_std * self.params.num_std)
        
        return df

    def signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate signals based on Bollinger Bands.
        
        Returns 1 when price <= lower band, -1 when price >= upper band.
        """
        df = self.indicators(df)
        
        signals = pd.Series(0, index=df.index)
        
        # Buy signal when price touches or crosses below lower band
        lower_touch = df["close"] <= df["bb_lower"]
        signals[lower_touch] = 1
        
        # Sell signal when price touches or crosses above upper band
        upper_touch = df["close"] >= df["bb_upper"]
        signals[upper_touch] = -1
        
        return signals
