#!/usr/bin/env python3
"""Main backtest runner script."""
import sys
from datetime import datetime, timedelta

from backtest.runner import BacktestRunner
from backtest.strategies import (
    MACrossover,
    RSIStrategy,
    MACDStrategy,
    BollingerBandStrategy,
    MomentumStrategy,
)
from backtest.synthetic_data import generate_dataset
from backtest.data import prepare_features


def main():
    # Select stocks to test
    symbols = ['Stock_A', 'Stock_B', 'Stock_C', 'Stock_D', 'Stock_E', 'Stock_F', 'Stock_G', 'Stock_H', 'Stock_I', 'Stock_J']

    # Backtest period
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print(f"Backtest Period: {start_date} to {end_date}")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Initial Capital: $100,000\n")

    # Initialize runner
    runner = BacktestRunner(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
    )

    # Generate synthetic data instead of loading real data
    print("Generating synthetic data...")
    runner.data = generate_dataset(symbols, start_date, end_date)

    print("Preparing features...")
    runner.features = {}
    for symbol, df in runner.data.items():
        runner.features[symbol] = prepare_features(df)

    print(f"Generated {len(runner.data)} symbols with {len(runner.features[symbols[0]])} days\n")

    # Test individual strategies
    print("\n" + "="*100)
    print("BACKTESTING INDIVIDUAL STRATEGIES")
    print("="*100 + "\n")

    strategies = [
        MACrossover(short_window=5, long_window=20),
        MACrossover(short_window=10, long_window=50),
        RSIStrategy(oversold=30, overbought=70),
        RSIStrategy(oversold=25, overbought=75),
        MACDStrategy(),
        BollingerBandStrategy(),
        MomentumStrategy(lookback=10, threshold=0.02),
        MomentumStrategy(lookback=20, threshold=0.03),
    ]

    for i, strategy in enumerate(strategies, 1):
        print(f"[{i}/{len(strategies)}] Testing {strategy.name}...")
        result = runner.backtest_strategy(strategy)
        print(f"  → Sharpe: {result.sharpe_ratio:.2f}, Return: {result.total_return:>7.2%}")

    # Test strategy combinations
    print("\n" + "="*100)
    print("BACKTESTING STRATEGY COMBINATIONS")
    print("="*100 + "\n")

    # Ensemble 1: All strategies equal weight
    print("[1] Testing Equal-Weighted Ensemble...")
    ensemble1_strats = [
        MACrossover(5, 20),
        RSIStrategy(30, 70),
        MACDStrategy(),
        BollingerBandStrategy(),
    ]
    result = runner.backtest_ensemble(
        ensemble1_strats,
        ensemble_name="Equal-Weighted Ensemble",
    )
    print(f"  → Sharpe: {result.sharpe_ratio:.2f}, Return: {result.total_return:>7.2%}")

    # Ensemble 2: Trend following focus
    print("[2] Testing Trend-Following Ensemble...")
    ensemble2_strats = [
        MACrossover(5, 20),
        MACrossover(10, 50),
        MACDStrategy(),
        MomentumStrategy(10, 0.02),
    ]
    weights = {
        'MA_Crossover': 0.3,
        'MACD': 0.3,
        'Momentum': 0.4,
    }
    result = runner.backtest_ensemble(
        ensemble2_strats,
        weights={s.name: weights.get(s.name, 0.25) for s in ensemble2_strats},
        ensemble_name="Trend-Following Ensemble",
    )
    print(f"  → Sharpe: {result.sharpe_ratio:.2f}, Return: {result.total_return:>7.2%}")

    # Ensemble 3: Mean reversion focus
    print("[3] Testing Mean-Reversion Ensemble...")
    ensemble3_strats = [
        RSIStrategy(30, 70),
        RSIStrategy(25, 75),
        BollingerBandStrategy(),
        MomentumStrategy(20, 0.03),
    ]
    weights = {
        'RSI': 0.35,
        'BollingerBand': 0.35,
        'Momentum': 0.3,
    }
    result = runner.backtest_ensemble(
        ensemble3_strats,
        weights={s.name: weights.get(s.name, 0.25) for s in ensemble3_strats},
        ensemble_name="Mean-Reversion Ensemble",
    )
    print(f"  → Sharpe: {result.sharpe_ratio:.2f}, Return: {result.total_return:>7.2%}")

    # Ensemble 4: Balanced ensemble
    print("[4] Testing Balanced Ensemble...")
    ensemble4_strats = [
        MACrossover(5, 20),
        RSIStrategy(30, 70),
        MACDStrategy(),
        BollingerBandStrategy(),
        MomentumStrategy(10, 0.02),
    ]
    result = runner.backtest_ensemble(
        ensemble4_strats,
        ensemble_name="Balanced Ensemble",
    )
    print(f"  → Sharpe: {result.sharpe_ratio:.2f}, Return: {result.total_return:>7.2%}")

    # Print all results
    runner.print_results()

    # Export results
    runner.export_results('backtest_results.json')

    # Find best strategy
    best = max(runner.results, key=lambda r: r.sharpe_ratio)
    print(f"\n{'='*100}")
    print(f"BEST STRATEGY: {best.strategy_name} (Sharpe: {best.sharpe_ratio:.2f})")
    print(f"{'='*100}")


if __name__ == '__main__':
    main()
