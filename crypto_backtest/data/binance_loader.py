"""Binance API data loader for historical OHLCV data."""

import pandas as pd
import requests
from datetime import datetime
from typing import Optional
import time
from crypto_backtest.data.base import BaseLoader


class BinanceLoader(BaseLoader):
    """
    Load OHLCV data from Binance public API.
    
    Uses the public REST API endpoint - no authentication required.
    Handles pagination automatically for large date ranges.
    """

    BASE_URL = "https://api.binance.com"
    INTERVALS = {
        "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m", "30m": "30m",
        "1h": "1h", "2h": "2h", "4h": "4h", "6h": "6h", "8h": "8h", "12h": "12h",
        "1d": "1d", "3d": "3d", "1w": "1w", "1M": "1M"
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize Binance loader.

        Parameters
        ----------
        cache_dir : str, optional
            Directory to cache downloaded data (for faster subsequent loads)
        """
        self.cache_dir = cache_dir

    def load(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str
    ) -> pd.DataFrame:
        """
        Load OHLCV data from Binance.

        Parameters
        ----------
        symbol : str
            Trading pair (e.g., "BTCUSDT")
        timeframe : str
            Candle interval (e.g., "1h", "4h", "1d")
        start : str
            Start date in YYYY-MM-DD format
        end : str
            End date in YYYY-MM-DD format

        Returns
        -------
        pd.DataFrame
            OHLCV DataFrame with DatetimeIndex
        """
        # Validate timeframe
        if timeframe not in self.INTERVALS:
            raise ValueError(f"Invalid timeframe: {timeframe}. "
                           f"Choose from: {list(self.INTERVALS.keys())}")

        # Convert dates to timestamps
        start_ms = int(pd.Timestamp(start).timestamp() * 1000)
        end_ms = int(pd.Timestamp(end).timestamp() * 1000)

        # Fetch data with pagination
        all_klines = []
        current_start = start_ms

        print(f"Fetching {symbol} {timeframe} data from {start} to {end}...")

        while current_start < end_ms:
            klines = self._fetch_klines(
                symbol=symbol,
                interval=self.INTERVALS[timeframe],
                start_ms=current_start,
                end_ms=end_ms,
                limit=1000
            )

            if not klines:
                break

            all_klines.extend(klines)

            # Update start time to the last candle's close time + 1ms
            current_start = klines[-1][6] + 1

            # Rate limiting - be nice to the API
            time.sleep(0.1)

            # Progress indicator
            progress_date = pd.Timestamp(klines[-1][0], unit='ms')
            print(f"  Loaded up to {progress_date.strftime('%Y-%m-%d %H:%M')}", end='\r')

        print(f"\nTotal candles fetched: {len(all_klines)}")

        # Convert to DataFrame
        df = self._to_dataframe(all_klines)

        # Save to cache if enabled
        if self.cache_dir:
            self.save_cache(df, symbol, timeframe, start, end)

        return df

    def _fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_ms: int,
        end_ms: int,
        limit: int = 1000
    ) -> list:
        """
        Fetch klines (candlesticks) from Binance API.

        Parameters
        ----------
        symbol : str
            Trading pair
        interval : str
            Candle interval
        start_ms : int
            Start timestamp in milliseconds
        end_ms : int
            End timestamp in milliseconds
        limit : int
            Max number of candles per request (max 1000)

        Returns
        -------
        list
            Raw kline data from API
        """
        endpoint = f"{self.BASE_URL}/api/v3/klines"

        params = {
            "symbol": symbol,
            "interval": interval,
            "startTime": start_ms,
            "endTime": end_ms,
            "limit": limit
        }

        try:
            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"\nError fetching data from Binance: {e}")
            return []

    def _to_dataframe(self, raw_klines: list) -> pd.DataFrame:
        """
        Convert raw kline data to OHLCV DataFrame.

        Parameters
        ----------
        raw_klines : list
            Raw kline data from Binance API

        Returns
        -------
        pd.DataFrame
            OHLCV DataFrame with DatetimeIndex
        """
        if not raw_klines:
            return pd.DataFrame()

        # Binance kline structure:
        # [
        #   [open_time, open, high, low, close, volume, close_time, 
        #    quote_volume, trades, taker_buy_base, taker_buy_quote, ignore]
        # ]

        df = pd.DataFrame(raw_klines, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", 
            "taker_buy_base", "taker_buy_quote", "ignore"
        ])

        # Convert to proper types
        df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
        df["open"] = pd.to_numeric(df["open"])
        df["high"] = pd.to_numeric(df["high"])
        df["low"] = pd.to_numeric(df["low"])
        df["close"] = pd.to_numeric(df["close"])
        df["volume"] = pd.to_numeric(df["volume"])

        # Set timestamp as index
        df = df.set_index("open_time")

        # Keep only OHLCV columns
        df = df[["open", "high", "low", "close", "volume"]]

        return df

    def save_cache(
        self,
        df: pd.DataFrame,
        symbol: str,
        timeframe: str,
        start: str,
        end: str
    ) -> None:
        """
        Save DataFrame to cache file.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame
        symbol : str
            Trading pair
        timeframe : str
            Timeframe
        start : str
            Start date
        end : str
            End date
        """
        if not self.cache_dir:
            return

        import os
        os.makedirs(self.cache_dir, exist_ok=True)

        filename = f"{symbol}_{timeframe}_{start}_{end}.csv"
        filepath = os.path.join(self.cache_dir, filename)

        df.to_csv(filepath)
        print(f"Cached data to {filepath}")

    @staticmethod
    def list_top_symbols(limit: int = 20) -> list:
        """
        Get list of top trading pairs by volume.

        Parameters
        ----------
        limit : int
            Number of symbols to return

        Returns
        -------
        list
            List of symbol names
        """
        endpoint = "https://api.binance.com/api/v3/ticker/24hr"

        try:
            response = requests.get(endpoint, timeout=30)
            response.raise_for_status()
            tickers = response.json()

            # Filter USDT pairs and sort by quote volume
            usdt_pairs = [
                t for t in tickers 
                if t["symbol"].endswith("USDT") and float(t["quoteVolume"]) > 0
            ]

            sorted_pairs = sorted(
                usdt_pairs,
                key=lambda x: float(x["quoteVolume"]),
                reverse=True
            )

            return [p["symbol"] for p in sorted_pairs[:limit]]

        except requests.exceptions.RequestException as e:
            print(f"Error fetching symbols: {e}")
            return []
