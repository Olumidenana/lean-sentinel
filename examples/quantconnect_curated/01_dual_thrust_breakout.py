# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
from AlgorithmImports import *

class DualThrustBreakoutAlgorithm(QCAlgorithm):
    """
    QuantConnect Benchmark Strategy: Dual Thrust Breakout (Michael Chalek)
    Computes daily opening range thresholds (K1, K2) and executes intraday trend continuation.
    """

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # 1. Equity asset with explicit resolution
        self.spy = self.AddEquity("SPY", Resolution.Hour).Symbol

        # Strategy parameters
        self.n_days = 4
        self.k1 = 0.5
        self.k2 = 0.5
        self.upper_trigger = None
        self.lower_trigger = None

        # 2. Risk Management Model
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))

        # 3. Schedule daily threshold calculation right after market open
        self.Schedule.On(
            self.DateRules.EveryDay(self.spy),
            self.TimeRules.AfterMarketOpen(self.spy, 5),
            self.CalculateThresholds
        )

    def CalculateThresholds(self):
        history = self.History(self.spy, self.n_days + 1, Resolution.Daily)
        if history.empty or len(history) < self.n_days:
            return

        highs = history['high']
        lows = history['low']
        closes = history['close']

        hh = max(highs[:-1])
        lc = min(closes[:-1])
        hc = max(closes[:-1])
        ll = min(lows[:-1])

        day_range = max(hh - lc, hc - ll)
        today_open = float(history['open'].iloc[-1])

        self.upper_trigger = today_open + self.k1 * day_range
        self.lower_trigger = today_open - self.k2 * day_range

    def OnData(self, data: Slice):
        if not data.ContainsKey(self.spy) or data[self.spy] is None:
            return

        if self.upper_trigger is None or self.lower_trigger is None:
            return

        current_price = data[self.spy].Price
        is_invested = self.Portfolio[self.spy].Invested

        if current_price > self.upper_trigger:
            if not is_invested or self.Portfolio[self.spy].IsShort:
                self.SetHoldings(self.spy, 1.0)
        elif current_price < self.lower_trigger:
            if not is_invested or self.Portfolio[self.spy].IsLong:
                self.Liquidate(self.spy)
