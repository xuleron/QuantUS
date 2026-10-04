"""Backtest runner for strategy evaluation."""
import pandas as pd
import numpy as np
from typing import Dict, List, Callable, Tuple
from dataclasses import dataclass
import json

from .engine import BacktestEngine, BacktestConfig
from .data import load_data, prepare_features
from .strategies import Strategy
from .portfolio import PortfolioManager


@dataclass
class BacktestResult:
    """Backtest result with metrics."""
    strategy_name: str
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    max_drawdown: float
    volatility: float
    total_trades: int
    final_value: float

    def to_dict(self) -> Dict:
        return {
            'strategy_name': str(self.strategy_name),
            'total_return': float(round(self.total_return, 4)),
            'annualized_return': float(round(self.annualized_return, 4)),
            'sharpe_ratio': float(round(self.sharpe_ratio, 4)),
            'max_drawdown': float(round(self.max_drawdown, 4)),
            'volatility': float(round(self.volatility, 4)),
            'total_trades': int(self.total_trades),
            'final_value': float(round(self.final_value, 2)),
        }


class BacktestRunner:
    """Runner for backtesting multiple strategies."""

    def __init__(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float = 100000,
    ):
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.data = None
        self.features = None
        self.results = []

    def load_data(self):
        """Load and prepare data."""
        print(f"Loading data for {self.symbols}...")
        self.data = load_data(
            self.symbols,
            self.start_date,
            self.end_date,
        )

        print("Preparing features...")
        self.features = {}
        for symbol, df in self.data.items():
            self.features[symbol] = prepare_features(df)

        print(f"Loaded {len(self.data)} symbols with {len(self.features[self.symbols[0]])} days")

    def backtest_strategy(
        self,
        strategy: Strategy,
        rebalance_freq: int = 1,  # rebalance every N days
        use_portfolio_manager: bool = True,
    ) -> BacktestResult:
        """
        Backtest a single strategy.

        Args:
            strategy: Strategy instance
            rebalance_freq: Rebalance frequency in days
            use_portfolio_manager: Whether to use portfolio manager

        Returns:
            BacktestResult
        """
        config = BacktestConfig(
            initial_capital=self.initial_capital,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        engine = BacktestEngine(config)
        portfolio_mgr = PortfolioManager() if use_portfolio_manager else None

        def strategy_fn(date, current_data, positions, cash):
            # Get strategy signals
            signals = strategy.get_signal(date, current_data, self.features)

            if portfolio_mgr:
                # Generate orders using portfolio manager
                combined_signals = {s: sig for s, sig in signals.items()}
                prices = {}
                for s in current_data:
                    series = current_data[s]
                    price = series.get('Close') if 'Close' in series else series.get('close')
                    if price:
                        prices[s] = price

                orders = portfolio_mgr.generate_orders(
                    combined_signals,
                    positions,
                    cash,
                    prices,
                    signal_threshold=0.5,
                )
            else:
                # Simple signal-based orders
                orders = []
                for symbol, signal in signals.items():
                    series = current_data[symbol]
                    close_price = series.get('Close') if 'Close' in series else series.get('close')
                    if not close_price or close_price <= 0:
                        continue

                    if signal > 0.5 and symbol not in positions:
                        qty = int(cash * 0.08 / close_price)
                        if qty > 0:
                            orders.append({
                                'symbol': symbol,
                                'side': 'BUY',
                                'qty': qty,
                            })
                    elif signal < -0.5 and symbol in positions:
                        orders.append({
                            'symbol': symbol,
                            'side': 'SELL',
                            'qty': positions[symbol],
                        })

            return orders

        metrics = engine.run(self.features, strategy_fn)

        result = BacktestResult(
            strategy_name=strategy.name,
            **metrics,
        )

        self.results.append(result)
        return result

    def backtest_ensemble(
        self,
        strategies: List[Strategy],
        weights: Dict[str, float] = None,
        ensemble_name: str = "Ensemble",
    ) -> BacktestResult:
        """
        Backtest multiple strategies combined.

        Args:
            strategies: List of strategy instances
            weights: Weights for each strategy (default: equal)
            ensemble_name: Name for this ensemble

        Returns:
            BacktestResult
        """
        config = BacktestConfig(
            initial_capital=self.initial_capital,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        engine = BacktestEngine(config)
        portfolio_mgr = PortfolioManager()

        if weights is None:
            weights = {s.name: 1/len(strategies) for s in strategies}

        def strategy_fn(date, current_data, positions, cash):
            # Get signals from all strategies
            all_signals = {}
            for strategy in strategies:
                signals = strategy.get_signal(date, current_data, self.features)
                all_signals[strategy.name] = signals

            # Combine signals
            combined = {}
            all_symbols = set()
            for signals in all_signals.values():
                all_symbols.update(signals.keys())

            for symbol in all_symbols:
                weighted_signal = 0
                for strategy in strategies:
                    signal = all_signals[strategy.name].get(symbol, 0)
                    weight = weights[strategy.name]
                    weighted_signal += signal * weight
                combined[symbol] = weighted_signal

            # Generate orders
            orders = portfolio_mgr.generate_orders(
                combined,
                positions,
                cash,
                {s: current_data[s]['Close'] for s in current_data},
                signal_threshold=0.2,
            )

            return orders

        metrics = engine.run(self.features, strategy_fn)

        result = BacktestResult(
            strategy_name=ensemble_name,
            **metrics,
        )

        self.results.append(result)
        return result

    def print_results(self):
        """Print backtest results."""
        if not self.results:
            print("No results to print")
            return

        print("\n" + "="*100)
        print("BACKTEST RESULTS")
        print("="*100)

        sorted_results = sorted(self.results, key=lambda r: r.sharpe_ratio, reverse=True)

        for i, result in enumerate(sorted_results, 1):
            print(f"\n{i}. {result.strategy_name}")
            print(f"   Total Return:       {result.total_return:>8.2%}")
            print(f"   Annualized Return:  {result.annualized_return:>8.2%}")
            print(f"   Sharpe Ratio:       {result.sharpe_ratio:>8.2f}")
            print(f"   Max Drawdown:       {result.max_drawdown:>8.2%}")
            print(f"   Volatility:         {result.volatility:>8.2%}")
            print(f"   Total Trades:       {result.total_trades:>8d}")
            print(f"   Final Value:        ${result.final_value:>10,.0f}")

    def export_results(self, filepath: str = "backtest_results.json"):
        """Export results to JSON."""
        results_dicts = [r.to_dict() for r in self.results]
        with open(filepath, 'w') as f:
            json.dump(results_dicts, f, indent=2)
        print(f"Results exported to {filepath}")
