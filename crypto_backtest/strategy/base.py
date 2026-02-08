"""Base abstract class for trading strategies."""

from abc import ABC, abstractmethod
import pandas as pd
from dataclasses import dataclass, field
from typing import Any


@dataclass
class StrategyParams:
    """Container for strategy parameters with defaults."""
    params: dict = field(default_factory=dict)

    def __getattr__(self, name):
        if name in self.__dict__.get('params', {}):
            return self.params[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")


class BaseStrategy(ABC):
    """
    Base class for all trading strategies.

    Subclasses must implement:
    - indicators(df): Add indicator columns to the DataFrame
    - signal(df): Return a Series of signals: 1=buy, -1=sell, 0=hold
    """

    # Default parameters -- override in subclass
    default_params: dict = {}

    def __init__(self, **kwargs):
        """
        Initialize strategy with parameters.

        Parameters are merged with default_params, with kwargs taking precedence.
        """
        merged = {**self.default_params, **kwargs}
        self.params = StrategyParams(params=merged)

    @abstractmethod
    def indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add indicator columns to the OHLCV DataFrame.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with DatetimeIndex

        Returns
        -------
        pd.DataFrame
            DataFrame with additional indicator columns
        """
        pass

    @abstractmethod
    def signal(self, df: pd.DataFrame) -> pd.Series:
        """
        Generate trading signals.

        Parameters
        ----------
        df : pd.DataFrame
            OHLCV DataFrame with indicators

        Returns
        -------
        pd.Series
            Series with values:
                1  = enter long / close short
               -1  = enter short / close long
                0  = hold / no action
        """
        pass

    def name(self) -> str:
        """Return the strategy name."""
        return self.__class__.__name__
