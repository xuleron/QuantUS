#!/usr/bin/env python3
"""Backtest with realistic market data."""
from datetime import datetime, timedelta
from backtest.runner import BacktestRunner
from backtest.strategies import (
    MACrossover, RSIStrategy, MACDStrategy,
    BollingerBandStrategy, MomentumStrategy,
)
from backtest.improved_data import generate_realistic_dataset
from backtest.data import prepare_features


def main():
    symbols = ['Growth_A', 'Growth_B', 'Growth_C',
               'Value_A', 'Value_B', 'Value_C',
               'Volatile_A', 'Volatile_B', 'Volatile_C', 'Volatile_D']

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print("=" * 100)
    print("REALISTIC MARKET DATA BACKTEST")
    print("=" * 100)
    print("Using improved synthetic data with:")
    print("  ✓ Realistic trends and volatility")
    print("  ✓ Volatility clustering (risk on/off)")
    print("  ✓ Momentum effects")
    print("  ✓ Mean reversion dynamics")
    print("  ✓ Volume spikes on volatile days\n")

    runner = BacktestRunner(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
    )

    print("Generating realistic market data...")
    runner.data = generate_realistic_dataset(symbols, start_date, end_date)

    print("\nPreparing technical features...")
    runner.features = {}
    for symbol, df in runner.data.items():
        runner.features[symbol] = prepare_features(df)

    print(f"Ready: {len(runner.data)} symbols × {len(runner.features[symbols[0]])} days\n")

    # Test best performing strategies from previous runs
    print("=" * 100)
    print("BACKTESTING BEST STRATEGIES")
    print("=" * 100 + "\n")

    strategies = [
        ("MACD", MACDStrategy()),
        ("Momentum(5,0.03)", MomentumStrategy(5, 0.03)),
        ("Momentum(5,0.01)", MomentumStrategy(5, 0.01)),
        ("RSI(35,80)", RSIStrategy(35, 80)),
        ("MA(5,20)", MACrossover(5, 20)),
        ("MA(5,50)", MACrossover(5, 50)),
    ]

    for name, strategy in strategies:
        strategy.name = name
        result = runner.backtest_strategy(strategy)
        print(f"{name:20s} → Return: {result.total_return:7.2%}  Sharpe: {result.sharpe_ratio:6.2f}  DD: {result.max_drawdown:7.2%}")

    # Test optimized ensembles
    print("\n" + "=" * 100)
    print("OPTIMIZED ENSEMBLE COMBINATIONS")
    print("=" * 100 + "\n")

    # Ensemble 1: MACD + Momentum
    print("[1] MACD + Momentum Ensemble")
    ens1_strats = [
        MACDStrategy(),
        MomentumStrategy(5, 0.03),
    ]
    result1 = runner.backtest_ensemble(
        ens1_strats,
        weights={'MACD': 0.6, 'Momentum(5,0.03)': 0.4},
        ensemble_name="MACD-Momentum"
    )
    print(f"    Return: {result1.total_return:7.2%}  Sharpe: {result1.sharpe_ratio:6.2f}  DD: {result1.max_drawdown:7.2%}\n")

    # Ensemble 2: Balanced
    print("[2] Balanced Multi-Strategy")
    ens2_strats = [
        MACDStrategy(),
        RSIStrategy(35, 80),
        MomentumStrategy(5, 0.03),
        MACrossover(5, 20),
    ]
    result2 = runner.backtest_ensemble(
        ens2_strats,
        ensemble_name="Balanced-Ensemble"
    )
    print(f"    Return: {result2.total_return:7.2%}  Sharpe: {result2.sharpe_ratio:6.2f}  DD: {result2.max_drawdown:7.2%}\n")

    # Ensemble 3: Growth focused
    print("[3] Growth-Focused (High Return)")
    ens3_strats = [
        MomentumStrategy(5, 0.01),
        MomentumStrategy(10, 0.01),
        MACrossover(5, 20),
    ]
    result3 = runner.backtest_ensemble(
        ens3_strats,
        weights={
            'Momentum(5,0.01)': 0.4,
            'Momentum(10,0.01)': 0.3,
            'MA(5,20)': 0.3,
        },
        ensemble_name="Growth-Focused"
    )
    print(f"    Return: {result3.total_return:7.2%}  Sharpe: {result3.sharpe_ratio:6.2f}  DD: {result3.max_drawdown:7.2%}\n")

    # Summary and recommendation
    print("=" * 100)
    print("RESULTS SUMMARY")
    print("=" * 100 + "\n")

    runner.print_results()
    runner.export_results('backtest_results_realistic.json')

    best = max(runner.results, key=lambda r: r.total_return)
    best_sharpe = max(runner.results, key=lambda r: r.sharpe_ratio)

    print("\n" + "=" * 100)
    print("FINAL RECOMMENDATIONS")
    print("=" * 100 + "\n")

    print("🏆 BEST RETURN:")
    print(f"   Strategy: {best.strategy_name}")
    print(f"   Return: {best.total_return:.2%}")
    print(f"   Sharpe: {best.sharpe_ratio:.2f}")
    print(f"   Max DD: {best.max_drawdown:.2%}\n")

    print("⭐ BEST RISK-ADJUSTED (Sharpe):")
    print(f"   Strategy: {best_sharpe.strategy_name}")
    print(f"   Return: {best_sharpe.total_return:.2%}")
    print(f"   Sharpe: {best_sharpe.sharpe_ratio:.2f}")
    print(f"   Max DD: {best_sharpe.max_drawdown:.2%}\n")

    print("📊 COMPARISON TO BENCHMARKS:")
    print(f"   Our Best: {best.total_return:.2%}")
    print(f"   QQQ Hist: 15-20%")
    print(f"   S&P 500:  10-12%")
    print(f"   SPY/VOO: 10-12%\n")

    print("💡 NEXT STEPS:")
    print("   1. Use REAL market data (yfinance) for actual validation")
    print("   2. Test with multiple time periods (bull/bear/sideways)")
    print("   3. Implement with Alpaca paper trading")
    print("   4. Compare paper vs backtest vs real results")
    print("   5. Adjust parameters based on real market feedback")


if __name__ == '__main__':
    main()
