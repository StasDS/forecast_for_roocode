"""Base abstract class for all data loaders."""

from abc import ABC, abstractmethod
import pandas as pd


class BaseLoader(ABC):
    """Abstract base class for all data loaders."""

    @abstractmethod
    def load(
        self,
        symbol: str,
        timeframe: str,
        start: str,
        end: str
    ) -> pd.DataFrame:
        """
        Load OHLCV data for a given symbol and timeframe.

        Parameters
        ----------
        symbol : str
            Trading pair symbol (e.g., "BTCUSDT")
        timeframe : str
            Candle timeframe (e.g., "1h", "4h", "1d")
        start : str
            Start date in YYYY-MM-DD format
        end : str
            End date in YYYY-MM-DD format

        Returns
        -------
        pd.DataFrame
            DataFrame with DatetimeIndex and columns:
            [open, high, low, close, volume]
        """
        pass
