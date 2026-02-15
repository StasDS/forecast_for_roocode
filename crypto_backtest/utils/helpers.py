"""Utility helper functions."""

from typing import Union


def format_currency(value: float, symbol: str = "$") -> str:
    """
    Format value as currency.

    Parameters
    ----------
    value : float
        Numeric value
    symbol : str
        Currency symbol

    Returns
    -------
    str
        Formatted string
    """
    return f"{symbol}{value:,.2f}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage.

    Parameters
    ----------
    value : float
        Numeric value
    decimals : int
        Number of decimal places

    Returns
    -------
    str
        Formatted string
    """
    return f"{value:.{decimals}f}%"


def timeframe_to_minutes(timeframe: str) -> int:
    """
    Convert timeframe string to minutes.

    Parameters
    ----------
    timeframe : str
        Timeframe (e.g., "1h", "4h", "1d")

    Returns
    -------
    int
        Number of minutes
    """
    timeframe_map = {
        "1m": 1,
        "3m": 3,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "8h": 480,
        "12h": 720,
        "1d": 1440,
        "3d": 4320,
        "1w": 10080,
        "1M": 43200  # approximate
    }

    return timeframe_map.get(timeframe, 60)


def calculate_position_size(
    capital: float,
    risk_per_trade: float,
    entry_price: float,
    stop_loss_price: float
) -> float:
    """
    Calculate position size based on risk management.

    Parameters
    ----------
    capital : float
        Total capital
    risk_per_trade : float
        Risk percentage per trade (e.g., 0.02 for 2%)
    entry_price : float
        Entry price
    stop_loss_price : float
        Stop loss price

    Returns
    -------
    float
        Position size in base currency
    """
    risk_amount = capital * risk_per_trade
    price_risk = abs(entry_price - stop_loss_price)
    
    if price_risk == 0:
        return 0
    
    position_size = risk_amount / price_risk
    
    return position_size
