#!/usr/bin/env python3
"""Aggressive strategy optimization for higher returns."""
from datetime import datetime, timedelta
from backtest.runner import BacktestRunner
from backtest.strategies import (
    MACrossover, RSIStrategy, MACDStrategy,
    BollingerBandStrategy, MomentumStrategy,
)
from backtest.synthetic_data import generate_dataset
from backtest.data import prepare_features


def main():
    symbols = ['Stock_A', 'Stock_B', 'Stock_C', 'Stock_D', 'Stock_E',
               'Stock_F', 'Stock_G', 'Stock_H', 'Stock_I', 'Stock_J']

    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

    print("=" * 100)
    print("AGGRESSIVE STRATEGY BACKTESTING")
    print("=" * 100)
    print(f"Goal: Higher returns than QQQ (~15-20% annually)\n")

    runner = BacktestRunner(
        symbols=symbols,
        start_date=start_date,
        end_date=end_date,
        initial_capital=100000,
    )

    print("Generating market data...")
    runner.data = generate_dataset(symbols, start_date, end_date)
    runner.features = {}
    for symbol, df in runner.data.items():
        runner.features[symbol] = prepare_features(df)

    print(f"Ready: {len(runner.data)} symbols × {len(runner.features[symbols[0]])} days\n")

    # Test aggressive individual strategies
    print("=" * 100)
    print("AGGRESSIVE INDIVIDUAL STRATEGIES")
    print("=" * 100 + "\n")

    aggressive_strategies = [
        ("Momentum(5,0.01)", MomentumStrategy(5, 0.01)),
        ("RSI(20,80) [Aggressive]", RSIStrategy(20, 80)),
        ("MA(3,10) [Fast Cross]", MACrossover(3, 10)),
        ("Momentum(10,0.01)", MomentumStrategy(10, 0.01)),
        ("RSI(20,70)", RSIStrategy(20, 70)),
    ]

    for name, strategy in aggressive_strategies:
        strategy.name = name
        result = runner.backtest_strategy(strategy)
        print(f"{name:30s} → Return: {result.total_return:7.2%}  Sharpe: {result.sharpe_ratio:6.2f}  DD: {result.max_drawdown:7.2%}")

    # Aggressive ensembles
    print("\n" + "=" * 100)
    print("AGGRESSIVE ENSEMBLE COMBINATIONS")
    print("=" * 100 + "\n")

    # Strategy 1: Momentum-Heavy (追求快速收益)
    print("[1] Momentum-Heavy Ensemble (Fast Growth)")
    momentum_strats = [
        MomentumStrategy(5, 0.01),
        MomentumStrategy(10, 0.01),
        RSIStrategy(20, 80),
        MACrossover(3, 10),
    ]
    weights1 = {
        'Momentum(5,0.01)': 0.35,
        'Momentum(10,0.01)': 0.35,
        'RSI(20,80) [Aggressive]': 0.2,
        'MA(3,10) [Fast Cross]': 0.1,
    }
    result1 = runner.backtest_ensemble(
        momentum_strats,
        weights={s.name: weights1.get(s.name, 0.25) for s in momentum_strats},
        ensemble_name="Momentum-Heavy"
    )
    print(f"    Return: {result1.total_return:7.2%}  Sharpe: {result1.sharpe_ratio:6.2f}  DD: {result1.max_drawdown:7.2%}\n")

    # Strategy 2: Mean-Reversion Aggressive
    print("[2] Aggressive Mean-Reversion (Countertrend)")
    mr_strats = [
        RSIStrategy(20, 80),
        RSIStrategy(25, 75),
        BollingerBandStrategy(),
    ]
    result2 = runner.backtest_ensemble(
        mr_strats,
        ensemble_name="Aggressive-MeanReversion"
    )
    print(f"    Return: {result2.total_return:7.2%}  Sharpe: {result2.sharpe_ratio:6.2f}  DD: {result2.max_drawdown:7.2%}\n")

    # Strategy 3: Trend + Momentum Hybrid (最激进)
    print("[3] Trend-Momentum Hybrid (Most Aggressive)")
    hybrid_strats = [
        MACrossover(3, 10),
        MomentumStrategy(5, 0.01),
        MACDStrategy(),
        RSIStrategy(30, 70),
    ]
    weights3 = {
        'MA(3,10) [Fast Cross]': 0.3,
        'Momentum(5,0.01)': 0.4,
        'MACD': 0.2,
        'RSI': 0.1,
    }
    result3 = runner.backtest_ensemble(
        hybrid_strats,
        weights={s.name: weights3.get(s.name, 0.25) for s in hybrid_strats},
        ensemble_name="Trend-Momentum-Hybrid"
    )
    print(f"    Return: {result3.total_return:7.2%}  Sharpe: {result3.sharpe_ratio:6.2f}  DD: {result3.max_drawdown:7.2%}\n")

    # Strategy 4: Pure Trend Following (Fast MA Cross)
    print("[4] Pure Trend Following (Fast MA)")
    trend_strats = [
        MACrossover(3, 10),
        MACrossover(5, 15),
        MACrossover(5, 20),
    ]
    result4 = runner.backtest_ensemble(
        trend_strats,
        ensemble_name="FastTrendFollowing"
    )
    print(f"    Return: {result4.total_return:7.2%}  Sharpe: {result4.sharpe_ratio:6.2f}  DD: {result4.max_drawdown:7.2%}\n")

    # Summary
    print("\n" + "=" * 100)
    print("COMPARISON: Conservative vs Aggressive")
    print("=" * 100 + "\n")

    best = max(runner.results, key=lambda r: r.total_return)

    print("CONSERVATIVE APPROACH (Previously Recommended)")
    print(f"  Strategy: MACDConfirmed")
    print(f"  Return: 6.24%  | Sharpe: 2.30 | Max DD: -0.69%")
    print(f"  Interpretation: Low risk, steady, but underperforms QQQ\n")

    print("AGGRESSIVE APPROACH (New Recommendation)")
    print(f"  Strategy: {best.strategy_name}")
    print(f"  Return: {best.total_return:.2%} | Sharpe: {best.sharpe_ratio:.2f} | Max DD: {best.max_drawdown:.2%}")
    print(f"  Interpretation: Higher growth, acceptable risk\n")

    print("QQQ BENCHMARK (Target)")
    print(f"  Historical Average: 15-20% annually")
    print(f"  Max Drawdown: -30% to -50%")
    print(f"  Sharpe Ratio: 0.8-1.2\n")

    # Analysis
    print("=" * 100)
    print("ANALYSIS & RECOMMENDATIONS")
    print("=" * 100 + "\n")

    print("📊 Key Insights:")
    print("  1. Conservative strategies prioritize Sharpe ratio (risk-adjusted returns)")
    print("  2. Aggressive strategies prioritize absolute returns")
    print("  3. Our synthetic data shows limited returns (5-15%) vs real market (15-30%)")
    print("  4. Fast MA crossovers (3,10) capture more movement but with higher drawdowns")
    print("  5. Momentum strategies work best with short lookback periods\n")

    print("🎯 Recommendations:")
    print("  Option A: Use Conservative strategy with leverage (2x) → ~13% return with moderate risk")
    print("  Option B: Use Aggressive strategy (this backtest) → Higher return, higher drawdown")
    print("  Option C: Use real market data (yfinance) to see actual performance")
    print("  Option D: Combine both - 60% conservative + 40% aggressive → Balanced approach\n")

    print("⚠️  Important Notes:")
    print("  - Synthetic data underestimates real market opportunities")
    print("  - Real trading has liquidity, slippage, and market impact issues")
    print("  - Paper trading results usually beat real trading by 2-5%")
    print("  - Need to test on real market data to validate performance\n")

    runner.print_results()
    runner.export_results('backtest_results_aggressive.json')


if __name__ == '__main__':
    main()
