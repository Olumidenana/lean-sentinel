# region imports
from AlgorithmImports import *
# endregion

class InstitutionalFrameworkAlgorithm(QCAlgorithm):
    """
    Gold Standard 5-Component QuantConnect Algorithm Framework.
    Decomposed into Universe, Alpha, Portfolio, Execution, and Risk.
    """

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # 1. Universe Selection Model
        self.UniverseSettings.Resolution = Resolution.Daily
        self.SetUniverseSelection(CoarseFundamentalUniverseSelectionModel(self.CoarseFilter))

        # 2. Alpha Creation Model
        self.AddAlpha(CrossSectionalMomentumAlphaModel(lookback=20, top_n=5))

        # 3. Portfolio Construction Model
        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())

        # 4. Execution Model
        self.SetExecution(ImmediateExecutionModel())

        # 5. Risk Management Model
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))
        self.AddRiskManagement(TrailingStopRiskManagementModel(0.03))

        self.SetWarmUp(timedelta(days=30))

    def CoarseFilter(self, coarse: List[CoarseFundamental]) -> List[Symbol]:
        filtered = [x for x in coarse if x.HasFundamentalData and x.Price > 15 and x.DollarVolume > 25000000]
        sorted_by_volume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in sorted_by_volume[:30]]

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return


class CrossSectionalMomentumAlphaModel(AlphaModel):
    def __init__(self, lookback: int = 20, top_n: int = 5):
        self.lookback = lookback
        self.top_n = top_n
        self.roc_by_symbol = {}

    def Update(self, algorithm: QCAlgorithm, data: Slice) -> List[Insight]:
        insights = []
        if algorithm.IsWarmingUp:
            return insights

        scores = {}
        for symbol, roc in self.roc_by_symbol.items():
            if roc.IsReady and data.ContainsKey(symbol) and data[symbol] is not None:
                scores[symbol] = roc.Current.Value

        if len(scores) >= self.top_n:
            ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
            for symbol, _ in ranked[:self.top_n]:
                insights.append(
                    Insight.Price(
                        symbol,
                        timedelta(days=5),
                        InsightDirection.Up,
                        confidence=0.85,
                        weight=1.0 / self.top_n
                    )
                )

        return insights

    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
        for security in changes.AddedSecurities:
            symbol = security.Symbol
            if symbol not in self.roc_by_symbol:
                self.roc_by_symbol[symbol] = algorithm.ROC(symbol, self.lookback, Resolution.Daily)

        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            self.roc_by_symbol.pop(symbol, None)
