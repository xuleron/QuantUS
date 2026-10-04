"""Portfolio and position management."""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple


class PortfolioManager:
    """Manages portfolio positions and strategy signals."""

    def __init__(
        self,
        max_positions: int = 5,
        max_weight_per_stock: float = 0.3,
        position_sizing: str = 'equal',
    ):
        self.max_positions = max_positions
        self.max_weight_per_stock = max_weight_per_stock
        self.position_sizing = position_sizing

    def combine_signals(
        self,
        strategy_signals: Dict[str, Dict[str, float]],
        weights: Dict[str, float] = None,
    ) -> Dict[str, float]:
        """
        Combine signals from multiple strategies.

        Args:
            strategy_signals: Dict of {strategy_name: {symbol: signal}}
            weights: Dict of {strategy_name: weight}

        Returns:
            Dict of {symbol: combined_signal}
        """
        if not strategy_signals:
            return {}

        if weights is None:
            weights = {name: 1/len(strategy_signals) for name in strategy_signals}

        combined = {}
        all_symbols = set()
        for signals in strategy_signals.values():
            all_symbols.update(signals.keys())

        for symbol in all_symbols:
            weighted_signal = 0
            for strategy_name, signals in strategy_signals.items():
                signal = signals.get(symbol, 0)
                weight = weights.get(strategy_name, 0)
                weighted_signal += signal * weight
            combined[symbol] = weighted_signal

        return combined

    def generate_orders(
        self,
        combined_signals: Dict[str, float],
        current_positions: Dict[str, float],
        cash: float,
        current_prices: Dict[str, float],
        signal_threshold: float = 0.3,
    ) -> List[Dict]:
        """
        Generate orders based on combined signals.

        Args:
            combined_signals: Dict of {symbol: signal}
            current_positions: Dict of {symbol: quantity}
            cash: Available cash
            current_prices: Dict of {symbol: price}
            signal_threshold: Minimum signal strength to trade

        Returns:
            List of orders [{symbol, side, qty}, ...]
        """
        orders = []

        # Rank signals
        ranked = sorted(
            [(s, sig) for s, sig in combined_signals.items() if abs(sig) >= signal_threshold],
            key=lambda x: abs(x[1]),
            reverse=True,
        )

        # Close positions with contrary signals
        for symbol, position in current_positions.items():
            if position <= 0.1:
                continue
            signal = combined_signals.get(symbol, 0)

            if signal < -signal_threshold:
                orders.append({
                    'symbol': symbol,
                    'side': 'SELL',
                    'qty': position,
                })

        # Open new positions conservatively
        active_symbols = set([s for s in current_positions if current_positions.get(s, 0) > 0.1])
        available_cash = cash * 0.7  # Keep 30% cash buffer

        for symbol, signal in ranked:
            if len(active_symbols) >= self.max_positions:
                break

            if symbol in active_symbols:
                continue

            price = current_prices.get(symbol, 0)
            if price <= 0:
                continue

            if signal > signal_threshold:
                # Conservative position sizing
                num_free_slots = max(1, self.max_positions - len(active_symbols))
                position_size = available_cash / num_free_slots
                qty = int(position_size * 0.06 / price)  # 6% per position max

                if qty > 0:
                    orders.append({
                        'symbol': symbol,
                        'side': 'BUY',
                        'qty': qty,
                    })
                    active_symbols.add(symbol)

        return orders
