"""Backtest analysis and reporting."""
import pandas as pd
import numpy as np
import json
from typing import Dict, List
from datetime import datetime


class BacktestAnalyzer:
    """Analyze backtest results."""

    def __init__(self, results_file: str = "backtest_results.json"):
        self.results_file = results_file
        self.results = []
        self.load_results()

    def load_results(self):
        """Load results from JSON file."""
        try:
            with open(self.results_file, 'r') as f:
                self.results = json.load(f)
        except FileNotFoundError:
            print(f"Results file {self.results_file} not found")

    def generate_report(self) -> str:
        """Generate a comprehensive backtest report."""
        if not self.results:
            return "No results to analyze"

        report = []
        report.append("=" * 100)
        report.append("COMPREHENSIVE BACKTEST ANALYSIS REPORT")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("=" * 100)

        # 1. Summary Statistics
        report.append("\n" + "SECTION 1: SUMMARY STATISTICS".center(100, "-"))
        df = pd.DataFrame(self.results)

        report.append(f"\nTotal Strategies Tested: {len(self.results)}")
        report.append(f"\nAverage Performance Metrics:")
        report.append(f"  Mean Sharpe Ratio:       {df['sharpe_ratio'].mean():.2f}")
        report.append(f"  Mean Total Return:       {df['total_return'].mean():.2%}")
        report.append(f"  Mean Annualized Return:  {df['annualized_return'].mean():.2%}")
        report.append(f"  Mean Max Drawdown:       {df['max_drawdown'].mean():.2%}")
        report.append(f"  Mean Volatility:         {df['volatility'].mean():.2%}")

        # 2. Best Performers
        report.append("\n" + "SECTION 2: BEST PERFORMERS".center(100, "-"))

        top_sharpe = df.nlargest(5, 'sharpe_ratio')
        report.append("\nTop 5 by Sharpe Ratio:")
        for i, (_, row) in enumerate(top_sharpe.iterrows(), 1):
            report.append(f"\n{i}. {row['strategy_name']}")
            report.append(f"   Sharpe Ratio:       {row['sharpe_ratio']:.2f}")
            report.append(f"   Total Return:       {row['total_return']:.2%}")
            report.append(f"   Annualized Return:  {row['annualized_return']:.2%}")
            report.append(f"   Max Drawdown:       {row['max_drawdown']:.2%}")

        # 3. Risk Analysis
        report.append("\n" + "SECTION 3: RISK ANALYSIS".center(100, "-"))

        min_drawdown = df.nlargest(5, 'max_drawdown')  # Best (least negative)
        report.append("\nLowest Max Drawdown (Best Risk Control):")
        for i, (_, row) in enumerate(min_drawdown.iterrows(), 1):
            report.append(f"\n{i}. {row['strategy_name']}")
            report.append(f"   Max Drawdown:       {row['max_drawdown']:.2%}")
            report.append(f"   Volatility:         {row['volatility']:.2%}")
            report.append(f"   Total Return:       {row['total_return']:.2%}")

        # 4. Return vs Risk
        report.append("\n" + "SECTION 4: RETURN VS RISK ANALYSIS".center(100, "-"))

        df['return_per_risk'] = df['annualized_return'] / (np.abs(df['max_drawdown']) + 0.0001)
        best_risk_adjusted = df.nlargest(5, 'return_per_risk')

        report.append("\nBest Return/Risk Ratio (Annualized Return / Abs Max Drawdown):")
        for i, (_, row) in enumerate(best_risk_adjusted.iterrows(), 1):
            ratio = row['annualized_return'] / (np.abs(row['max_drawdown']) + 0.0001)
            report.append(f"\n{i}. {row['strategy_name']}")
            report.append(f"   Return/Risk Ratio:  {ratio:.2f}")
            report.append(f"   Return:             {row['annualized_return']:.2%}")
            report.append(f"   Max Drawdown:       {row['max_drawdown']:.2%}")

        # 5. Trading Activity
        report.append("\n" + "SECTION 5: TRADING ACTIVITY ANALYSIS".center(100, "-"))

        high_activity = df.nlargest(5, 'total_trades')
        report.append("\nMost Active Strategies (by number of trades):")
        for i, (_, row) in enumerate(high_activity.iterrows(), 1):
            report.append(f"\n{i}. {row['strategy_name']}: {int(row['total_trades'])} trades")
            report.append(f"   Sharpe Ratio: {row['sharpe_ratio']:.2f}")

        # 6. Recommendations
        report.append("\n" + "SECTION 6: RECOMMENDATIONS".center(100, "-"))

        best = df.loc[df['sharpe_ratio'].idxmax()]
        report.append(f"\nBest Overall Strategy (by Sharpe Ratio):")
        report.append(f"  Strategy:          {best['strategy_name']}")
        report.append(f"  Sharpe Ratio:      {best['sharpe_ratio']:.2f}")
        report.append(f"  Total Return:      {best['total_return']:.2%}")
        report.append(f"  Max Drawdown:      {best['max_drawdown']:.2%}")
        report.append(f"\nRecommendation:")
        report.append(f"  {best['strategy_name']} shows the best risk-adjusted returns.")
        report.append(f"  Consider using this as the primary strategy for live trading.")

        # 7. Implementation Notes
        report.append("\n" + "SECTION 7: IMPLEMENTATION NOTES".center(100, "-"))
        report.append("""
- All backtests used:
  * Initial Capital: $100,000
  * Commission: 0.1% per trade
  * Slippage: 0.1%
  * Position sizing: Conservative (5-6% per position max)

- Results are based on synthetic market data (representative but not real)
  * Real market conditions may differ significantly
  * Past performance does not guarantee future results

- Consider:
  * Running live paper trading first
  * Gradually scaling into live trading
  * Monitoring strategy performance regularly
  * Adjusting parameters as market conditions change
""")

        report.append("\n" + "=" * 100)

        return "\n".join(report)

    def save_report(self, filepath: str = "backtest_report.txt"):
        """Save report to file."""
        report = self.generate_report()
        with open(filepath, 'w') as f:
            f.write(report)
        print(f"Report saved to {filepath}")
        return report


def create_summary_table(results: List[Dict]) -> pd.DataFrame:
    """Create summary table from results."""
    df = pd.DataFrame(results)

    # Sort by Sharpe ratio
    df = df.sort_values('sharpe_ratio', ascending=False)

    # Round numeric columns
    numeric_cols = ['total_return', 'annualized_return', 'sharpe_ratio', 'max_drawdown', 'volatility']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = df[col].round(4)

    return df
