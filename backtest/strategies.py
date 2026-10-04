"""Trading strategies."""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional


class Strategy:
    """Base strategy class."""

    def __init__(self, name: str):
        self.name = name
        self.state = {}

    def get_signal(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.Series],
        features: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, float]:
        """
        Generate trading signals.

        Returns:
            Dict of {symbol: signal} where signal in [-1, 0, 1]
            -1: SELL, 0: HOLD, 1: BUY
        """
        raise NotImplementedError


class MACrossover(Strategy):
    """Moving Average Crossover Strategy."""

    def __init__(self, short_window: int = 5, long_window: int = 20):
        super().__init__("MA_Crossover")
        self.short_window = short_window
        self.long_window = long_window

    def get_signal(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.Series],
        features: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, float]:
        signals = {}

        for symbol, series in data.items():
            if features and symbol in features:
                df = features[symbol]
                if date not in df.index:
                    signals[symbol] = 0
                    continue

                row = df.loc[date]
                ma_short = row.get(f'MA{self.short_window}', np.nan)
                ma_long = row.get(f'MA{self.long_window}', np.nan)

                if pd.isna(ma_short) or pd.isna(ma_long):
                    signals[symbol] = 0
                    continue

                if ma_short > ma_long:
                    signals[symbol] = 1
                elif ma_short < ma_long:
                    signals[symbol] = -1
                else:
                    signals[symbol] = 0
            else:
                signals[symbol] = 0

        return signals


class RSIStrategy(Strategy):
    """RSI-based mean reversion strategy."""

    def __init__(self, oversold: float = 30, overbought: float = 70):
        super().__init__("RSI")
        self.oversold = oversold
        self.overbought = overbought

    def get_signal(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.Series],
        features: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, float]:
        signals = {}

        for symbol, series in data.items():
            if features and symbol in features:
                df = features[symbol]
                if date not in df.index:
                    signals[symbol] = 0
                    continue

                rsi = df.loc[date].get('RSI', np.nan)

                if pd.isna(rsi):
                    signals[symbol] = 0
                    continue

                if rsi < self.oversold:
                    signals[symbol] = 1
                elif rsi > self.overbought:
                    signals[symbol] = -1
                else:
                    signals[symbol] = 0
            else:
                signals[symbol] = 0

        return signals


class MACDStrategy(Strategy):
    """MACD crossover strategy."""

    def __init__(self):
        super().__init__("MACD")

    def get_signal(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.Series],
        features: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, float]:
        signals = {}

        for symbol, series in data.items():
            if features and symbol in features:
                df = features[symbol]
                if date not in df.index:
                    signals[symbol] = 0
                    continue

                macd = df.loc[date].get('MACD', np.nan)
                signal = df.loc[date].get('Signal', np.nan)

                if pd.isna(macd) or pd.isna(signal):
                    signals[symbol] = 0
                    continue

                if macd > signal:
                    signals[symbol] = 1
                elif macd < signal:
                    signals[symbol] = -1
                else:
                    signals[symbol] = 0
            else:
                signals[symbol] = 0

        return signals


class BollingerBandStrategy(Strategy):
    """Bollinger Band mean reversion strategy."""

    def __init__(self):
        super().__init__("BollingerBand")

    def get_signal(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.Series],
        features: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, float]:
        signals = {}

        for symbol, series in data.items():
            if features and symbol in features:
                df = features[symbol]
                if date not in df.index:
                    signals[symbol] = 0
                    continue

                row = df.loc[date]
                close = row.get('Close', np.nan)
                bb_upper = row.get('BB_Upper', np.nan)
                bb_lower = row.get('BB_Lower', np.nan)

                if pd.isna(close) or pd.isna(bb_upper) or pd.isna(bb_lower):
                    signals[symbol] = 0
                    continue

                if close < bb_lower:
                    signals[symbol] = 1
                elif close > bb_upper:
                    signals[symbol] = -1
                else:
                    signals[symbol] = 0
            else:
                signals[symbol] = 0

        return signals


class MomentumStrategy(Strategy):
    """Momentum strategy based on price change."""

    def __init__(self, lookback: int = 10, threshold: float = 0.02):
        super().__init__("Momentum")
        self.lookback = lookback
        self.threshold = threshold

    def get_signal(
        self,
        date: pd.Timestamp,
        data: Dict[str, pd.Series],
        features: Optional[Dict[str, pd.DataFrame]] = None,
    ) -> Dict[str, float]:
        signals = {}

        for symbol in data.keys():
            if features and symbol in features:
                df = features[symbol]
                if date not in df.index:
                    signals[symbol] = 0
                    continue

                idx = df.index.get_loc(date)
                if idx < self.lookback:
                    signals[symbol] = 0
                    continue

                current = df.iloc[idx]['Close']
                past = df.iloc[idx - self.lookback]['Close']
                momentum = (current - past) / past

                if momentum > self.threshold:
                    signals[symbol] = 1
                elif momentum < -self.threshold:
                    signals[symbol] = -1
                else:
                    signals[symbol] = 0
            else:
                signals[symbol] = 0

        return signals
