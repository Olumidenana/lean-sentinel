# QUANTCONNECT.COM - Democratizing Finance, Empowering Individuals.
# Lean Algorithmic Trading Engine v2.0. Copyright 2014 QuantConnect Corporation.
from AlgorithmImports import *

class CoarseFineFundamentalAlgorithm(QCAlgorithm):
    """
    QuantConnect Benchmark: Dynamic Stock Selection via Morningstar Fundamentals.
    Coarse filter: Dollar volume liquidity & share price.
    Fine filter: Value factor (lowest P/E ratio) & quality balance sheets.
    """

    def Initialize(self):
        self.SetStartDate(2021, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        self.UniverseSettings.Resolution = Resolution.Daily

        # Add Coarse & Fine Universe Selection functions
        self.AddUniverse(self.CoarseSelectionFunction, self.FineSelectionFunction)

        # Risk Management Model
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.06))

        self.symbols = []
        self.last_rebalance = self.Time

    def CoarseSelectionFunction(self, coarse: List[CoarseFundamental]) -> List[Symbol]:
        # Filter for liquid stocks with fundamental data
        filtered = [x for x in coarse if x.HasFundamentalData and x.Price > 10 and x.DollarVolume > 20000000]
        sorted_by_dollar_volume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in sorted_by_dollar_volume[:100]]

    def FineSelectionFunction(self, fine: List[FineFundamental]) -> List[Symbol]:
        # Sort by value factor: Lowest positive Price-to-Earnings (P/E) ratio
        valid_pe = [x for x in fine if x.ValuationRatios.PERatio > 0]
        sorted_by_pe = sorted(valid_pe, key=lambda x: x.ValuationRatios.PERatio)
        self.symbols = [x.Symbol for x in sorted_by_pe[:10]]
        return self.symbols

    def OnData(self, data: Slice):
        # Monthly rebalance logic
        if (self.Time - self.last_rebalance).days < 30:
            return

        if not self.symbols:
            return

        # Equal weighting across selected value basket
        target_weight = 1.0 / len(self.symbols)
        for symbol in self.symbols:
            if data.ContainsKey(symbol) and data[symbol] is not None:
                self.SetHoldings(symbol, target_weight)

        self.last_rebalance = self.Time
