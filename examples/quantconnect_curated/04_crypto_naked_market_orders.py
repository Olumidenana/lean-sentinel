# QuantConnect Community Forum Case Study #2: Crypto Unsafe Execution
from AlgorithmImports import *

class CryptoUnsafeExecutionAlgorithm(QCAlgorithm):
    """
    Common QuantConnect Forum Trap:
    - Subscribes to high-volatility crypto (BTCUSD, ETHUSD) without explicit Resolution.
    - Executes raw MarketOrders based on naive momentum without checking cash/margin.
    - No RiskManagementModel registered (vulnerable to liquidation spikes).
    """

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetCash(50000)
        self.SetBrokerageModel(BrokerageName.Coinbase, AccountType.Cash)

        # Defect 1: Missing explicit Resolution
        self.AddCrypto("BTCUSD")
        self.AddCrypto("ETHUSD")

        self.fast = self.EMA("BTCUSD", 12)
        self.slow = self.EMA("BTCUSD", 26)
        self.SetWarmUp(30)

    def OnData(self, data: Slice):
        # Defect 2: No warmup guard
        btc_bar = data["BTCUSD"]

        # Defect 3: No .IsReady check
        if self.fast.Current.Value > self.slow.Current.Value:
            # Defect 4: Naked MarketOrder bypassing portfolio weighting
            self.MarketOrder("BTCUSD", 1)
        else:
            self.MarketOrder("BTCUSD", -1)
