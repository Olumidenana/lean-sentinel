"""
Institutional QuantConnect LEAN 5-Component Modular Framework Templates.
Each template decomposes into Universe, Alpha, Portfolio, Execution, and Risk.
"""

MOMENTUM_FRAMEWORK_TEMPLATE = '''# region imports
from AlgorithmImports import *
# endregion

class InstitutionalMomentumAlgorithm(QCAlgorithm):
    """
    LeanSentinel Generated Algorithm: Institutional Cross-Sectional Momentum
    Fully decomposed across the QuantConnect 5-Component Framework.
    """

    def Initialize(self):
        # 1. Backtest Horizon & Initial Capital
        self.SetStartDate(2022, 1, 1)
        self.SetCash(100000)

        # 2. Brokerage & Account Sizing
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        # 3. Universe Selection: Liquid US Equities
        self.UniverseSettings.Resolution = Resolution.Daily
        self.AddUniverse(self.CoarseSelectionFunction)

        # 4. Alpha Creation Model
        self.AddAlpha(CrossSectionalMomentumAlphaModel(lookback=20, top_n=5))

        # 5. Portfolio Construction Model
        self.SetPortfolioConstruction(InsightWeightingPortfolioConstructionModel())

        # 6. Execution Model: Smooth institutional execution
        self.SetExecution(ImmediateExecutionModel())

        # 7. Risk Management Model: Capital preservation
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.06))
        self.AddRiskManagement(TrailingStopRiskManagementModel(0.04))

        # 8. Warmup to eliminate cold-start issues
        self.SetWarmUp(timedelta(days=30))

    def CoarseSelectionFunction(self, coarse):
        # Filter for dollar volume liquidity and clean share price
        filtered = [x for x in coarse if x.HasFundamentalData and x.Price > 10 and x.DollarVolume > 20000000]
        sorted_by_volume = sorted(filtered, key=lambda x: x.DollarVolume, reverse=True)
        return [x.Symbol for x in sorted_by_volume[:50]]

    def OnData(self, data: Slice):
        # Safety guard for warmup
        if self.IsWarmingUp:
            return


class CrossSectionalMomentumAlphaModel(AlphaModel):
    """
    Alpha Model: Computes relative ROC momentum and emits long Insights
    for top decile assets.
    """
    def __init__(self, lookback=20, top_n=5):
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
            top_symbols = [sym for sym, _ in ranked[:self.top_n]]

            for symbol in top_symbols:
                # 5-day insight duration with weight proportionate to momentum
                insights.append(
                    Insight.Price(
                        symbol,
                        timedelta(days=5),
                        InsightDirection.Up,
                        confidence=0.8,
                        weight=1.0 / self.top_n
                    )
                )

        return insights

    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
        for security in changes.AddedSecurities:
            symbol = security.Symbol
            if symbol not in self.roc_by_symbol:
                roc = algorithm.ROC(symbol, self.lookback, Resolution.Daily)
                self.roc_by_symbol[symbol] = roc

        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            if symbol in self.roc_by_symbol:
                self.roc_by_symbol.pop(symbol, None)
'''

MEAN_REVERSION_FRAMEWORK_TEMPLATE = '''# region imports
from AlgorithmImports import *
# endregion

class InstitutionalMeanReversionAlgorithm(QCAlgorithm):
    """
    LeanSentinel Generated Algorithm: Multi-Asset Bollinger & RSI Mean Reversion
    Fully decomposed across the QuantConnect 5-Component Framework.
    """

    def Initialize(self):
        self.SetStartDate(2022, 1, 1)
        self.SetCash(100000)
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage, AccountType.Margin)

        self.UniverseSettings.Resolution = Resolution.Hour

        # Universe: Liquid ETFs
        symbols = [Symbol.Create(t, SecurityType.Equity, Market.USA) for t in ["SPY", "QQQ", "IWM", "TLT", "GLD"]]
        self.SetUniverseSelection(ManualUniverseSelectionModel(symbols))

        # Alpha Model
        self.AddAlpha(BollingerRsiMeanReversionAlphaModel())

        # Equal weighting across active signals
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())

        # Execution Model
        self.SetExecution(VolumeWeightedAveragePriceExecutionModel())

        # Risk Management Model: Strict drawdown capping
        self.AddRiskManagement(MaximumDrawdownPercentPortfolio(0.05))

        self.SetWarmUp(timedelta(days=35))

    def OnData(self, data: Slice):
        if self.IsWarmingUp:
            return


class BollingerRsiMeanReversionAlphaModel(AlphaModel):
    def __init__(self):
        self.symbols_data = {}

    def Update(self, algorithm: QCAlgorithm, data: Slice) -> List[Insight]:
        insights = []
        if algorithm.IsWarmingUp:
            return insights

        for symbol, sd in self.symbols_data.items():
            if not data.ContainsKey(symbol) or data[symbol] is None:
                continue
            if not sd.is_ready:
                continue

            price = data[symbol].Close
            bb_lower = sd.bb.LowerBand.Current.Value
            bb_upper = sd.bb.UpperBand.Current.Value
            rsi = sd.rsi.Current.Value

            # Oversold condition -> Mean reversion long
            if price < bb_lower and rsi < 30:
                insights.append(Insight.Price(symbol, timedelta(hours=12), InsightDirection.Up, confidence=0.75))
            # Overbought condition -> Mean reversion short or flat
            elif price > bb_upper and rsi > 70:
                insights.append(Insight.Price(symbol, timedelta(hours=12), InsightDirection.Down, confidence=0.75))

        return insights

    def OnSecuritiesChanged(self, algorithm: QCAlgorithm, changes: SecurityChanges):
        for security in changes.AddedSecurities:
            symbol = security.Symbol
            if symbol not in self.symbols_data:
                self.symbols_data[symbol] = SymbolState(algorithm, symbol)

        for security in changes.RemovedSecurities:
            symbol = security.Symbol
            self.symbols_data.pop(symbol, None)


class SymbolState:
    def __init__(self, algorithm: QCAlgorithm, symbol: Symbol):
        self.bb = algorithm.BB(symbol, 20, 2.0, MovingAverageType.Simple, Resolution.Hour)
        self.rsi = algorithm.RSI(symbol, 14, MovingAverageType.Wilders, Resolution.Hour)

    @property
    def is_ready(self) -> bool:
        return self.bb.IsReady and self.rsi.IsReady
'''
