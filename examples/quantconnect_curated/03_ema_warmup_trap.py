# QuantConnect Community Forum Case Study #1: The Indicator Warmup Trap
# Frequently posted bug by beginner and AI quant developers
from AlgorithmImports import *

class EmaWarmupTrapAlgorithm(QCAlgorithm):
    """
    Common QuantConnect Forum Trap:
    - Calls SetWarmUp(50) but forgets `if self.IsWarmingUp: return` in OnData().
    - Trades immediately during historical warmup bars.
    - Reads self.ema.Current.Value before checking self.ema.IsReady.
    - Subscribes with AddEquity() without explicit Resolution.
    - Uses naked MarketOrder with hardcoded share counts.
    """

    def Initialize(self):
        self.SetStartDate(2023, 1, 1)
        self.SetCash(100000)

        # Defect 1: Missing explicit Resolution
        self.AddEquity("TSLA")

        # Defect 2: Indicator created
        self.ema = self.EMA("TSLA", 50)

        # Defect 3: Warmup declared without OnData guard
        self.SetWarmUp(50)

    def OnData(self, data: Slice):
        # Defect 4: Missing `if self.IsWarmingUp: return`
        # Causes trades to execute prematurely during warmup backfill!

        # Defect 5: Unchecked indicator readiness (.Current.Value before .IsReady)
        val = self.ema.Current.Value

        # Defect 6: Direct subscript access without ContainsKey()
        tsla_bar = data["TSLA"]

        # Defect 7: Naked MarketOrder bypasses portfolio risk
        if tsla_bar.Close > val:
            self.MarketOrder("TSLA", 50)
        else:
            self.MarketOrder("TSLA", -50)
