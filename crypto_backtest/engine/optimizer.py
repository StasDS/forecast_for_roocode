"""Grid search parameter optimizer for strategy tuning."""

import pandas as pd
import itertools
from typing import Dict, List, Type
from crypto_backtest.strategy.base import BaseStrategy
from crypto_backtest.engine.backtest import BacktestEngine


class GridOptimizer:
    """
    Grid search optimizer for strategy parameters.
    
    Runs backtests for all parameter combinations and ranks by target metric.
    Uses fast mode for speed.
    """

    def __init__(
        self,
        strategy_class: Type[BaseStrategy],
        data: pd.DataFrame,
        param_grid: Dict[str, List],
        metric: str = "net_profit_pct",
        **engine_kwargs
    ):
        """
        Initialize grid optimizer.

        Parameters
        ----------
        strategy_class : Type[BaseStrategy]
            Strategy class (not instance) to optimize
        data : pd.DataFrame
            OHLCV data for backtesting
        param_grid : dict
            Dictionary of parameter names to lists of values to test
            Example: {"fast_period": [5, 10, 20], "slow_period": [30, 50]}
        metric : str
            Target metric to optimize (e.g., "net_profit_pct", "sharpe_ratio")
        **engine_kwargs
            Additional arguments passed to BacktestEngine
        """
        self.strategy_class = strategy_class
        self.data = data
        self.param_grid = param_grid
        self.metric = metric
        self.engine_kwargs = engine_kwargs
        self.results = None

    def run(self) -> pd.DataFrame:
        """
        Run grid search optimization.

        Returns
        -------
        pd.DataFrame
            Results DataFrame with all parameter combinations and metrics,
            sorted by target metric (descending).
        """
        # Generate all parameter combinations
        param_names = list(self.param_grid.keys())
        param_values = list(self.param_grid.values())
        combinations = list(itertools.product(*param_values))

        total_combos = len(combinations)
        print(f"Testing {total_combos} parameter combinations...")

        results_list = []

        for i, combo in enumerate(combinations, 1):
            # Create parameter dict for this combination
            params = dict(zip(param_names, combo))

            # Create strategy instance with these parameters
            strategy = self.strategy_class(**params)

            # Run backtest in fast mode
            try:
                engine = BacktestEngine(strategy, self.data, **self.engine_kwargs)
                result = engine.run(mode="fast")

                # Store parameters and metrics
                result_dict = {**params, **result.metrics}
                results_list.append(result_dict)

                # Progress indicator
                if i % max(1, total_combos // 20) == 0:
                    print(f"  Progress: {i}/{total_combos} ({i/total_combos*100:.1f}%)")

            except Exception as e:
                print(f"  Error with params {params}: {e}")
                continue

        print(f"Optimization complete. Tested {len(results_list)} combinations.")

        # Create results DataFrame
        self.results = pd.DataFrame(results_list)

        # Sort by target metric (descending for profit metrics, could be adjusted)
        if self.metric in self.results.columns:
            self.results = self.results.sort_values(by=self.metric, ascending=False)

        return self.results

    def best(self, n: int = 1) -> pd.DataFrame:
        """
        Get the best n parameter combinations.

        Parameters
        ----------
        n : int
            Number of top results to return

        Returns
        -------
        pd.DataFrame
            Top n results sorted by target metric
        """
        if self.results is None:
            raise ValueError("Must run optimization first using run()")

        return self.results.head(n)

    def get_best_params(self) -> dict:
        """
        Get the best parameter combination.

        Returns
        -------
        dict
            Best parameters
        """
        if self.results is None:
            raise ValueError("Must run optimization first using run()")

        best_row = self.results.iloc[0]
        param_names = list(self.param_grid.keys())
        
        return {name: best_row[name] for name in param_names}

    def get_best_metrics(self) -> dict:
        """
        Get metrics for the best parameter combination.

        Returns
        -------
        dict
            Metrics dictionary
        """
        if self.results is None:
            raise ValueError("Must run optimization first using run()")

        best_row = self.results.iloc[0]
        
        # Extract only metric columns (not parameters)
        param_names = list(self.param_grid.keys())
        metrics = {k: v for k, v in best_row.items() if k not in param_names}
        
        return metrics

    def plot_heatmap(self, param_x: str, param_y: str, metric: str = None) -> None:
        """
        Plot heatmap of metric values for two parameters.

        Parameters
        ----------
        param_x : str
            Parameter name for x-axis
        param_y : str
            Parameter name for y-axis
        metric : str, optional
            Metric to plot (uses self.metric if not specified)
        """
        if self.results is None:
            raise ValueError("Must run optimization first using run()")

        import plotly.graph_objects as go

        metric = metric or self.metric

        # Pivot data for heatmap
        pivot = self.results.pivot(index=param_y, columns=param_x, values=metric)

        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='RdYlGn',
            text=pivot.values,
            texttemplate='%{text:.2f}',
            textfont={"size": 10},
            colorbar=dict(title=metric)
        ))

        fig.update_layout(
            title=f"Parameter Optimization Heatmap: {metric}",
            xaxis_title=param_x,
            yaxis_title=param_y,
            height=600,
            template='plotly_white'
        )

        fig.show()

    def summary(self, top_n: int = 5) -> None:
        """
        Print a summary of optimization results.

        Parameters
        ----------
        top_n : int
            Number of top results to display
        """
        if self.results is None:
            raise ValueError("Must run optimization first using run()")

        print(f"\n{'='*80}")
        print(f"  Grid Search Optimization Results")
        print(f"  Optimizing for: {self.metric}")
        print(f"{'='*80}\n")

        print(f"Top {top_n} Parameter Combinations:\n")

        top_results = self.best(top_n)
        
        for i, (idx, row) in enumerate(top_results.iterrows(), 1):
            print(f"{i}. {self.metric}: {row[self.metric]:.4f}")
            
            # Print parameters
            param_names = list(self.param_grid.keys())
            params_str = ", ".join([f"{name}={row[name]}" for name in param_names])
            print(f"   Parameters: {params_str}")
            
            # Print key metrics
            print(f"   Net Profit: {row['net_profit']:.2f} ({row['net_profit_pct']:.2f}%)")
            print(f"   Sharpe: {row['sharpe_ratio']:.2f}, Win Rate: {row['win_rate']:.2f}%")
            print(f"   Max DD: {row['max_drawdown_pct']:.2f}%, Total Trades: {int(row['total_trades'])}")
            print()

        print(f"{'='*80}\n")
