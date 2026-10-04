"""Unit tests for backtest framework."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backtest.engine import BacktestEngine, BacktestConfig
from backtest.data import prepare_features
from backtest.strategies import (
    MACrossover,
    RSIStrategy,
    MACDStrategy,
    BollingerBandStrategy,
    MomentumStrategy,
)
from backtest.synthetic_data import generate_synthetic_ohlcv


class TestSyntheticData:
    """Test synthetic data generation."""

    def test_generate_ohlcv(self):
        """Test OHLCV data generation."""
        df = generate_synthetic_ohlcv(
            'TEST',
            '2023-01-01',
            '2023-12-31',
            initial_price=100,
            trend=0.0005,
            volatility=0.02,
            seed=42,
        )

        assert len(df) > 0
        assert all(col in df.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume'])
        assert all(df['Close'] > 0)
        assert all(df['High'] >= df['Close'])
        assert all(df['Low'] <= df['Close'])


class TestFeatures:
    """Test technical feature preparation."""

    def test_prepare_features(self):
        """Test feature preparation."""
        df = generate_synthetic_ohlcv(
            'TEST',
            '2023-01-01',
            '2023-12-31',
            initial_price=100,
            seed=42,
        )

        features = prepare_features(df)

        # Check MA features
        assert 'MA5' in features.columns
        assert 'MA20' in features.columns
        assert 'MA50' in features.columns

        # Check technical indicators
        assert 'RSI' in features.columns
        assert 'MACD' in features.columns
        assert 'ATR' in features.columns
        assert 'BB_Upper' in features.columns
        assert 'BB_Lower' in features.columns

        # Check no NaN values
        assert features.isna().sum().sum() == 0


class TestStrategies:
    """Test strategy signal generation."""

    def test_ma_crossover(self):
        """Test MA crossover strategy."""
        df = generate_synthetic_ohlcv(
            'TEST',
            '2023-01-01',
            '2023-12-31',
            seed=42,
        )
        features = prepare_features(df)

        strategy = MACrossover(5, 20)

        # Get signal on a recent date
        if len(features) > 0:
            date = features.index[-1]
            row = features.loc[date]

            # Should generate valid signal
            signal = strategy.get_signal(date, {f: row for f in ['TEST']}, {'TEST': features})
            assert isinstance(signal, dict)

    def test_rsi_strategy(self):
        """Test RSI strategy."""
        df = generate_synthetic_ohlcv('TEST', '2023-01-01', '2023-12-31', seed=42)
        features = prepare_features(df)

        strategy = RSIStrategy(30, 70)

        if len(features) > 0:
            date = features.index[-1]
            row = features.loc[date]
            signal = strategy.get_signal(date, {'TEST': row}, {'TEST': features})
            assert isinstance(signal, dict)

    def test_macd_strategy(self):
        """Test MACD strategy."""
        df = generate_synthetic_ohlcv('TEST', '2023-01-01', '2023-12-31', seed=42)
        features = prepare_features(df)

        strategy = MACDStrategy()

        if len(features) > 0:
            date = features.index[-1]
            row = features.loc[date]
            signal = strategy.get_signal(date, {'TEST': row}, {'TEST': features})
            assert isinstance(signal, dict)


class TestBacktestEngine:
    """Test backtest engine."""

    def test_engine_initialization(self):
        """Test engine initialization."""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)

        assert engine.cash == 100000
        assert len(engine.trades) == 0
        assert len(engine.portfolio_values) == 0

    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation."""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)

        # Create mock data
        current_data = {
            'TEST': pd.Series({'Close': 100, 'name': pd.Timestamp('2023-01-01')}),
        }

        # Initially should be just cash
        value = engine._calculate_portfolio_value(current_data)
        assert value == 100000

        # Add a position
        engine.positions['TEST'] = 10
        value = engine._calculate_portfolio_value(current_data)
        assert value == 100000 + (10 * 100)

    def test_simple_backtest_run(self):
        """Test a simple backtest run."""
        # Generate test data
        df = generate_synthetic_ohlcv('TEST', '2023-01-01', '2023-06-30', seed=42)
        features = prepare_features(df)
        data = {'TEST': features}

        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)

        # Simple strategy: buy on first date, hold
        def simple_strategy(date, current_data, positions, cash):
            if 'TEST' not in positions or positions['TEST'] == 0:
                if cash > 0:
                    close_price = current_data['TEST']['Close']
                    qty = int(cash * 0.5 / close_price)
                    if qty > 0:
                        return [{'symbol': 'TEST', 'side': 'BUY', 'qty': qty}]
            return []

        metrics = engine.run(data, simple_strategy)

        assert 'final_value' in metrics
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert len(engine.trades) > 0


class TestMetricsCalculation:
    """Test performance metrics calculation."""

    def test_sharpe_ratio_calculation(self):
        """Test Sharpe ratio calculation."""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)

        # Simulate portfolio values
        engine.portfolio_values = [100000] * 10 + [105000] * 10
        engine.dates = pd.date_range('2023-01-01', periods=20)

        metrics = engine._calculate_metrics()

        assert 'sharpe_ratio' in metrics
        assert isinstance(metrics['sharpe_ratio'], (int, float))

    def test_max_drawdown_calculation(self):
        """Test max drawdown calculation."""
        config = BacktestConfig(initial_capital=100000)
        engine = BacktestEngine(config)

        # Simulate portfolio with drawdown
        engine.portfolio_values = [100000, 105000, 100000, 95000, 98000, 102000]
        engine.dates = pd.date_range('2023-01-01', periods=6)

        metrics = engine._calculate_metrics()

        assert 'max_drawdown' in metrics
        assert metrics['max_drawdown'] < 0  # Should be negative


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
