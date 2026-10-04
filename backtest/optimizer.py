"""Strategy parameter optimization."""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Callable
from itertools import product

from .runner import BacktestRunner, BacktestResult
from .strategies import (
    Strategy,
    MACrossover,
    RSIStrategy,
    MACDStrategy,
    BollingerBandStrategy,
    MomentumStrategy,
)


class StrategyOptimizer:
    """Optimize strategy parameters."""

    def __init__(self, runner: BacktestRunner):
        self.runner = runner
        self.optimization_results = []

    def optimize_ma_crossover(self) -> List[BacktestResult]:
        """Optimize MA Crossover parameters."""
        print("\nOptimizing MA Crossover...")
        results = []

        short_windows = [3, 5, 7, 10]
        long_windows = [20, 30, 50, 100]

        for short, long in product(short_windows, long_windows):
            if short >= long:
                continue

            strategy = MACrossover(short_window=short, long_window=long)
            strategy.name = f"MA({short},{long})"
            result = self.runner.backtest_strategy(strategy)
            results.append(result)
            print(f"  MA({short},{long}): Sharpe={result.sharpe_ratio:.2f}, Return={result.total_return:.2%}")

        self.optimization_results.extend(results)
        return results

    def optimize_rsi(self) -> List[BacktestResult]:
        """Optimize RSI parameters."""
        print("\nOptimizing RSI...")
        results = []

        oversold_levels = [20, 25, 30, 35]
        overbought_levels = [65, 70, 75, 80]

        for oversold, overbought in product(oversold_levels, overbought_levels):
            if oversold >= overbought:
                continue

            strategy = RSIStrategy(oversold=oversold, overbought=overbought)
            strategy.name = f"RSI({oversold},{overbought})"
            result = self.runner.backtest_strategy(strategy)
            results.append(result)
            print(f"  RSI({oversold},{overbought}): Sharpe={result.sharpe_ratio:.2f}, Return={result.total_return:.2%}")

        self.optimization_results.extend(results)
        return results

    def optimize_momentum(self) -> List[BacktestResult]:
        """Optimize Momentum parameters."""
        print("\nOptimizing Momentum...")
        results = []

        lookbacks = [5, 10, 15, 20]
        thresholds = [0.01, 0.02, 0.03, 0.05]

        for lookback, threshold in product(lookbacks, thresholds):
            strategy = MomentumStrategy(lookback=lookback, threshold=threshold)
            strategy.name = f"Momentum({lookback},{threshold})"
            result = self.runner.backtest_strategy(strategy)
            results.append(result)
            print(f"  Momentum({lookback},{threshold}): Sharpe={result.sharpe_ratio:.2f}, Return={result.total_return:.2%}")

        self.optimization_results.extend(results)
        return results

    def find_best_combinations(self, top_n: int = 10) -> List[Tuple[List[BacktestResult], float]]:
        """
        Find best strategy combinations using optimization results.

        Returns:
            List of (strategies, combined_sharpe) tuples
        """
        if not self.optimization_results:
            print("No optimization results. Run optimization first.")
            return []

        # Sort by Sharpe ratio
        sorted_results = sorted(
            self.optimization_results,
            key=lambda r: r.sharpe_ratio,
            reverse=True,
        )

        print(f"\nTop {top_n} Individual Strategies:")
        for i, result in enumerate(sorted_results[:top_n], 1):
            print(f"{i:2d}. {result.strategy_name:30s} Sharpe={result.sharpe_ratio:6.2f} Return={result.total_return:7.2%}")

        # Create combinations of top strategies
        combinations = []
        for i in range(min(top_n, len(sorted_results))):
            for j in range(i+1, min(top_n, len(sorted_results))):
                for k in range(j+1, min(top_n, len(sorted_results))):
                    # Average Sharpe of combined strategies
                    avg_sharpe = np.mean([
                        sorted_results[i].sharpe_ratio,
                        sorted_results[j].sharpe_ratio,
                        sorted_results[k].sharpe_ratio,
                    ])
                    combinations.append((
                        [sorted_results[i], sorted_results[j], sorted_results[k]],
                        avg_sharpe,
                    ))

        # Sort combinations by average Sharpe
        combinations.sort(key=lambda x: x[1], reverse=True)

        return combinations[:top_n]
