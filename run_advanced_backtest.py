#!/usr/bin/env python3
"""Advanced backtest with parameter optimization."""
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
from backtest.optimizer import StrategyOptimizer
from backtest.analysis import BacktestAnalyzer


def main():
    symbols = ['Stock_A', 'Stock_B', 'Stock_C', 'Stock_D', 'Stock_E',
               'Stock_F', 'Stock_G', 'Stock_H', 'Stock_I', 'Stock_J']

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print(f"Advanced Backtest Framework")
    print(f"{'='*100}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Symbols: {len(symbols)} stocks")
    print(f"Initial Capital: $100,000\n")

    # Initialize runner
    runner = BacktestRunner(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
    )

    # Load synthetic data
    print("Generating synthetic market data...")
    runner.data = generate_dataset(symbols, start_date, end_date)

    print("Preparing technical features...")
    runner.features = {}
    for symbol, df in runner.data.items():
        runner.features[symbol] = prepare_features(df)

    print(f"Ready: {len(runner.data)} symbols × {len(runner.features[symbols[0]])} days\n")

    # Phase 1: Individual Strategy Testing
    print("\n" + "="*100)
    print("PHASE 1: INDIVIDUAL STRATEGY TESTING")
    print("="*100 + "\n")

    print("Testing baseline strategies...")
    baseline_strategies = [
        MACrossover(5, 20),
        RSIStrategy(30, 70),
        MACDStrategy(),
        BollingerBandStrategy(),
        MomentumStrategy(10, 0.02),
    ]

    baseline_results = []
    for strategy in baseline_strategies:
        result = runner.backtest_strategy(strategy)
        baseline_results.append(result)
        print(f"  {strategy.name:20s} → Sharpe: {result.sharpe_ratio:6.2f}, Return: {result.total_return:7.2%}")

    # Phase 2: Parameter Optimization
    print("\n" + "="*100)
    print("PHASE 2: PARAMETER OPTIMIZATION")
    print("="*100)

    optimizer = StrategyOptimizer(runner)

    print("\nOptimizing individual strategy parameters...")
    optimizer.optimize_ma_crossover()
    optimizer.optimize_rsi()
    optimizer.optimize_momentum()

    # Phase 3: Strategy Ensembles
    print("\n" + "="*100)
    print("PHASE 3: ADVANCED ENSEMBLE COMBINATIONS")
    print("="*100 + "\n")

    # Ensemble 1: Trend + Momentum
    print("[1] Trend-Following with Momentum")
    ensemble1 = [
        MACrossover(5, 20),
        MACrossover(10, 50),
        MACDStrategy(),
        MomentumStrategy(10, 0.02),
    ]
    result1 = runner.backtest_ensemble(ensemble1, ensemble_name="TrendMomentum")
    print(f"    Sharpe: {result1.sharpe_ratio:.2f}, Return: {result1.total_return:.2%}\n")

    # Ensemble 2: Mean Reversion focused
    print("[2] Mean-Reversion Strategy")
    ensemble2 = [
        RSIStrategy(30, 70),
        BollingerBandStrategy(),
        RSIStrategy(25, 75),
    ]
    weights = {
        'RSI': 0.4,
        'BollingerBand': 0.4,
    }
    result2 = runner.backtest_ensemble(
        ensemble2,
        weights={s.name: weights.get(s.name, 0.33) for s in ensemble2},
        ensemble_name="MeanReversion"
    )
    print(f"    Sharpe: {result2.sharpe_ratio:.2f}, Return: {result2.total_return:.2%}\n")

    # Ensemble 3: MACD-focused with support
    print("[3] MACD-Driven with Confirmation")
    ensemble3 = [
        MACDStrategy(),
        RSIStrategy(30, 70),
        MomentumStrategy(10, 0.02),
    ]
    weights = {
        'MACD': 0.5,
        'RSI': 0.25,
        'Momentum': 0.25,
    }
    result3 = runner.backtest_ensemble(
        ensemble3,
        weights={s.name: weights.get(s.name, 0.33) for s in ensemble3},
        ensemble_name="MACDConfirmed"
    )
    print(f"    Sharpe: {result3.sharpe_ratio:.2f}, Return: {result3.total_return:.2%}\n")

    # Print all results
    print("\n" + "="*100)
    print("FINAL RESULTS SUMMARY")
    print("="*100 + "\n")
    runner.print_results()

    # Export and analyze
    runner.export_results('backtest_results.json')

    # Generate comprehensive report
    print("\nGenerating detailed analysis report...")
    analyzer = BacktestAnalyzer('backtest_results.json')
    report = analyzer.generate_report()
    analyzer.save_report('backtest_report.txt')

    print("\n" + report)

    # Find and highlight best strategy
    best = max(runner.results, key=lambda r: r.sharpe_ratio)
    print("\n" + "="*100)
    print("RECOMMENDED STRATEGY FOR DEPLOYMENT")
    print("="*100)
    print(f"\nStrategy: {best.strategy_name}")
    print(f"Sharpe Ratio (Risk-Adjusted Return): {best.sharpe_ratio:.2f}")
    print(f"Total Return: {best.total_return:.2%}")
    print(f"Annualized Return: {best.annualized_return:.2%}")
    print(f"Max Drawdown: {best.max_drawdown:.2%}")
    print(f"Number of Trades: {best.total_trades}")
    print(f"\n✓ This strategy is ready for paper trading validation.")
    print("✓ Consider implementing with position sizing: 5-10% per trade")
    print("✓ Monitor for market regime changes and adjust as needed")


if __name__ == '__main__':
    main()
