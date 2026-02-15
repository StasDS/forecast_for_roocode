"""Portfolio and trade tracking data structures."""

from dataclasses import dataclass, field
from typing import Optional, List
import pandas as pd


@dataclass
class Trade:
    """Represents a completed trade."""
    
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    direction: str  # "long" or "short"
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float  # realized P&L in absolute terms
    pnl_pct: float  # P&L as percentage
    bars_held: int  # number of candles in trade
    commission: float  # total commission for the trade
    
    def __repr__(self):
        return (f"Trade(direction={self.direction}, entry={self.entry_time.strftime('%Y-%m-%d %H:%M')}, "
                f"exit={self.exit_time.strftime('%Y-%m-%d %H:%M')}, pnl={self.pnl:.2f}, pnl_pct={self.pnl_pct:.2%})")


@dataclass
class Portfolio:
    """Tracks portfolio state during backtesting."""
    
    initial_capital: float
    current_capital: float
    position: float = 0.0  # current position size (0 = flat)
    direction: Optional[str] = None  # "long", "short", or None
    equity_curve: List[tuple] = field(default_factory=list)  # (timestamp, equity) pairs
    trades: List[Trade] = field(default_factory=list)  # completed trades
    open_trade: Optional[dict] = None  # currently open trade info
    
    def get_equity(self, current_price: float) -> float:
        """
        Calculate current equity including unrealized P&L.
        
        Parameters
        ----------
        current_price : float
            Current market price
            
        Returns
        -------
        float
            Total equity value
        """
        if self.position == 0:
            return self.current_capital
        
        # Calculate unrealized P&L
        if self.direction == "long":
            unrealized_pnl = (current_price - self.open_trade["entry_price"]) * self.position
        elif self.direction == "short":
            unrealized_pnl = (self.open_trade["entry_price"] - current_price) * self.position
        else:
            unrealized_pnl = 0
        
        return self.current_capital + unrealized_pnl
    
    def reset(self):
        """Reset portfolio to initial state."""
        self.current_capital = self.initial_capital
        self.position = 0.0
        self.direction = None
        self.equity_curve = []
        self.trades = []
        self.open_trade = None
