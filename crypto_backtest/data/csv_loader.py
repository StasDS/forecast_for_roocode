"""CSV and Parquet file data loader."""

import pandas as pd
from typing import Optional
from crypto_backtest.data.base import BaseLoader


class CsvLoader(BaseLoader):
    """
    Load OHLCV data from local CSV or Parquet files.
    
    Supports flexible column mapping and automatic date filtering.
    """

    def __init__(self, filepath: str, column_map: Optional[dict] = None):
        """
        Initialize CSV loader.

        Parameters
        ----------
        filepath : str
            Path to CSV or Parquet file
        column_map : dict, optional
            Mapping of standard names to file column names.
            Default: {"timestamp": "timestamp", "open": "open", 
                     "high": "high", "low": "low", "close": "close", 
                     "volume": "volume"}
        """
        self.filepath = filepath
        self.column_map = column_map or {
            "timestamp": "timestamp",
            "open": "open",
            "high": "high",
            "low": "low",
            "close": "close",
            "volume": "volume"
        }

    def load(
        self,
        symbol: str = None,
        timeframe: str = None,
        start: str = None,
        end: str = None
    ) -> pd.DataFrame:
        """
        Load data from CSV/Parquet file.

        Parameters
        ----------
        symbol : str, optional
            Not used for file-based loading (kept for API compatibility)
        timeframe : str, optional
            Not used for file-based loading (kept for API compatibility)
        start : str, optional
            Start date for filtering (YYYY-MM-DD format)
        end : str, optional
            End date for filtering (YYYY-MM-DD format)

        Returns
        -------
        pd.DataFrame
            OHLCV DataFrame with DatetimeIndex
        """
        # Load file based on extension
        if self.filepath.endswith('.parquet'):
            df = pd.read_parquet(self.filepath)
        else:
            df = pd.read_csv(self.filepath)

        # Rename columns according to mapping
        rename_map = {v: k for k, v in self.column_map.items()}
        df = df.rename(columns=rename_map)

        # Convert timestamp to datetime and set as index
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp")
        elif not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Sort by index
        df = df.sort_index()

        # Filter by date range if specified
        if start:
            df = df[df.index >= pd.to_datetime(start)]
        if end:
            df = df[df.index <= pd.to_datetime(end)]

        # Select only OHLCV columns
        required_cols = ["open", "high", "low", "close", "volume"]
        df = df[required_cols]

        return df
