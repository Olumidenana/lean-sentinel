# region imports
from AlgorithmImports import *
# endregion

class CleanAuditedAlgorithm(QCAlgorithm):
    """
    LeanSentinel Audited Version:
    All anti-patterns resolved:
    - Explicit Resolution.Daily
    - Proper warmup exit guard in OnData
    - Indicator readiness validation
    - Safe portfolio allocation via SetHoldings
    - Defensive slice key verification
    - Registered MaximumDrawdownPercentPortfolio risk manager
    """

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # 1. Explicit resolution
        self.spy = self.AddEquity("SPY", Resolution.Daily).Symbol

        # 2. Indicator registration
        self.sma = self.SMA(self.spy, 50, Resolution.Daily)

        # 3. Capital preservation model
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))

        # 4. Set warmup window
        self.SetWarmUp(timedelta(days=50))

    def OnData(self, data: Slice):
        # 1. Warmup guard
        if self.IsWarmingUp:
            return

        # 2. Defensive key and null checks
        if not data.ContainsKey(self.spy) or data[self.spy] is None:
            return

        # 3. Indicator readiness check
        if not self.sma.IsReady:
            return

        current_price = data[self.spy].Close
        sma_val = self.sma.Current.Value

        # 4. Target percentage allocation
        if current_price > sma_val and not self.Portfolio[self.spy].Invested:
            self.SetHoldings(self.spy, 0.95)
        elif current_price < sma_val and self.Portfolio[self.spy].Invested:
            self.Liquidate(self.spy)
