"""Backtest engine for strategy evaluation."""
import numpy as np
import pandas as pd
from typing import Callable, Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class BacktestConfig:
    """Backtest configuration."""
    initial_capital: float = 100000
    commission: float = 0.001
    slippage: float = 0.001
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    max_leverage: float = 2.0


@dataclass
class Trade:
    """Represents a single trade."""
    date: pd.Timestamp
    symbol: str
    side: str  # 'BUY' or 'SELL'
    quantity: float
    price: float
    commission: float


class BacktestEngine:
    """Main backtest engine."""

    def __init__(self, config: BacktestConfig = None):
        self.config = config or BacktestConfig()
        self.trades: List[Trade] = []
        self.portfolio_values = []
        self.dates = []
        self.positions = {}  # symbol -> quantity
        self.cash = self.config.initial_capital

    def run(
        self,
        data: Dict[str, pd.DataFrame],
        strategy_fn: Callable,
    ) -> Dict:
        """
        Run backtest with given strategy.

        Args:
            data: Dict of {symbol: DataFrame} with columns [open, high, low, close, volume]
            strategy_fn: Function that takes (date, data, positions, cash) and returns orders
                        Orders format: [{'symbol': str, 'side': 'BUY'/'SELL', 'qty': float}]

        Returns:
            Dict with performance metrics
        """
        # Get all dates
        all_dates = sorted(set().union(*[df.index for df in data.values()]))

        for date in all_dates:
            # Get current data for this date
            current_data = {}
            for symbol, df in data.items():
                if date in df.index:
                    current_data[symbol] = df.loc[date]

            if not current_data:
                continue

            # Get orders from strategy
            orders = strategy_fn(date, current_data, self.positions.copy(), self.cash)

            # Execute orders
            for order in orders or []:
                self._execute_order(order, current_data)

            # Record portfolio value
            portfolio_value = self._calculate_portfolio_value(current_data)
            self.portfolio_values.append(portfolio_value)
            self.dates.append(date)

        return self._calculate_metrics()

    def _execute_order(self, order: Dict, current_data: Dict[str, pd.Series]):
        """Execute a single order with proper risk management."""
        symbol = order['symbol']
        side = order['side']
        qty = order['qty']

        if symbol not in current_data or qty <= 0:
            return

        series = current_data[symbol]
        close_price = series.get('Close') if 'Close' in series else series.get('close')
        if close_price is None or close_price <= 0:
            return

        # Apply slippage
        if side == 'BUY':
            execution_price = close_price * (1 + self.config.slippage)
        else:
            execution_price = close_price * (1 - self.config.slippage)

        # Calculate total cost
        gross_cost = qty * execution_price
        commission = gross_cost * self.config.commission
        total_cost = gross_cost + commission

        if side == 'BUY':
            # Check cash availability
            if total_cost > self.cash:
                # Reduce quantity to fit available cash
                qty = (self.cash * 0.95) / (execution_price * (1 + self.config.commission))
                if qty < 1:
                    return
                total_cost = qty * execution_price + (qty * execution_price * self.config.commission)

            self.cash -= total_cost
            self.positions[symbol] = self.positions.get(symbol, 0) + qty
        else:
            # SELL: Check position availability
            current_qty = self.positions.get(symbol, 0)
            if qty > current_qty:
                qty = current_qty

            if qty <= 0:
                return

            proceeds = qty * execution_price - commission
            self.cash += proceeds
            self.positions[symbol] = current_qty - qty
            if self.positions[symbol] <= 0.1:  # Close position if nearly empty
                del self.positions[symbol]

        self.trades.append(Trade(
            date=current_data[symbol].name,
            symbol=symbol,
            side=side,
            quantity=qty,
            price=execution_price,
            commission=commission,
        ))

    def _calculate_portfolio_value(self, current_data: Dict[str, pd.Series]) -> float:
        """Calculate total portfolio value."""
        stock_value = 0
        for symbol, qty in self.positions.items():
            if symbol in current_data:
                series = current_data[symbol]
                close_price = series.get('Close') if 'Close' in series else series.get('close')
                if close_price is not None and close_price > 0:
                    stock_value += qty * close_price
        return self.cash + stock_value

    def _calculate_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.portfolio_values:
            return {}

        portfolio_values = np.array(self.portfolio_values)
        returns = (portfolio_values - self.config.initial_capital) / self.config.initial_capital

        # Daily returns
        daily_returns = np.diff(portfolio_values) / portfolio_values[:-1]

        # Annualized metrics (assuming 252 trading days)
        trading_days = len(self.portfolio_values)
        if trading_days > 1:
            annual_factor = 252 / trading_days
        else:
            annual_factor = 1

        total_return = returns[-1] if returns.size > 0 else 0
        annualized_return = (1 + total_return) ** annual_factor - 1

        # Volatility
        if len(daily_returns) > 1:
            volatility = np.std(daily_returns) * np.sqrt(252)
        else:
            volatility = 0

        # Sharpe ratio (assuming 2% risk-free rate)
        risk_free_rate = 0.02
        if volatility > 0:
            sharpe = (annualized_return - risk_free_rate) / volatility
        else:
            sharpe = 0

        # Max drawdown
        cumsum = portfolio_values
        running_max = np.maximum.accumulate(cumsum)
        drawdown = (cumsum - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Win rate
        if len(self.trades) > 0:
            # Pair buy and sell trades to calculate profit
            buy_trades = {t.symbol: [] for t in self.trades}
            sell_trades = {t.symbol: [] for t in self.trades}

            for trade in self.trades:
                if trade.side == 'BUY':
                    buy_trades[trade.symbol].append(trade)
                else:
                    sell_trades[trade.symbol].append(trade)

            winning_sells = 0
            total_sells = 0

            for symbol in sell_trades:
                if symbol in buy_trades and len(buy_trades[symbol]) > 0:
                    avg_buy_price = np.mean([t.price for t in buy_trades[symbol]])
                    for sell_trade in sell_trades[symbol]:
                        total_sells += 1
                        if sell_trade.price > avg_buy_price:
                            winning_sells += 1

            win_rate = winning_sells / total_sells if total_sells > 0 else 0
        else:
            win_rate = 0

        return {
            'total_return': total_return,
            'annualized_return': annualized_return,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'volatility': volatility,
            'total_trades': len(self.trades),
            'final_value': portfolio_values[-1] if len(portfolio_values) > 0 else self.config.initial_capital,
        }
