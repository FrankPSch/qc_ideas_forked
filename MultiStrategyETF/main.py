from AlgorithmImports import *


class SymbolIndicators:
    def __init__(self) -> None:
        self.roc_long = RateOfChangePercent(198)
        self.roc_short = RateOfChangePercent(7)
        self.atr = AverageTrueRange(21)
        
    def update(self, trade_bar):
        self.roc_long.Update(trade_bar.EndTime, trade_bar.Close)
        self.roc_short.Update(trade_bar.EndTime, trade_bar.Close)
        self.atr.Update(trade_bar)
    
    @property
    def ready(self):
        return all((
            self.roc_long.IsReady,
            self.roc_short.IsReady,
            self.atr.IsReady,
        ))


class BaseAlpha(object):
    EQUITY_RISK_PC = 0.01

    def __init__(self, algorithm: QCAlgorithm, indicators: dict[Symbol, SymbolIndicators], bars, ondata_symbols: list[Symbol]) -> None:
        self.algorithm = algorithm
        self.indicators = indicators
        self.bars = bars
        self.ondata_symbols = ondata_symbols
    
    def get_signals(self) -> int:
        raise NotImplementedError()
    
    def calculate_position_size(self, atr):
        return round((self.algorithm.Portfolio.TotalPortfolioValue * self.EQUITY_RISK_PC) / atr)
    
    @property
    def positions(self) -> dict[Symbol, int]:
        return self.algorithm.alpha_map[str(self.__class__)]['positions']
    
    @property
    def symbols(self) -> list[Symbol]:
        return [symbol for symbol in self.ondata_symbols if symbol in self.algorithm.alpha_map[str(self.__class__)]['symbols']]
    

class RateOfChangeAlpha(BaseAlpha):
    def get_signals(self) -> list[Symbol, int]:
        signals = []
        highest_roc = sorted(
            self.symbols, 
            key=lambda symbol: self.indicators[symbol].roc_long, 
            reverse=True,
        )[:5]
        for symbol in self.symbols:
            if not self.algorithm.ActiveSecurities[symbol].Invested:
                if symbol in highest_roc:
                    signals.append((symbol, self.calculate_position_size(self.indicators[symbol].atr.Current.Value)))
            elif symbol not in highest_roc:
                existing_position_size = self.positions[symbol]
                signals.append((symbol, -1 * existing_position_size))
        return signals


class MultiStrategyETF(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2002, 1, 1)
        self.SetEndDate(2022, 11, 1)
        self.SetCash(10000)
        self.SetWarmUp(timedelta(200), Resolution.Daily)
        self.UniverseSettings.Resolution = Resolution.Daily
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage)
        tickers = [
            "GXLE",
            "GXLK",
            "GXLV",
            "GXLF",
            "SXLP",
            "SXLI",
            "GXLC",
            "SXLY",
            "SXLB",
            "SXLU",
        ] if self.LiveMode else [
            "XLE",
            "XLK",
            "XLV",
            "XLF",
            "XLP",
            "XLI",
            "XLC",
            "XLY",
            "XLB",
            "XLU",
        ]
        self.symbol_map = {}
        self.alpha_map = {
            RateOfChangeAlpha: tickers
        }
        for alpha_tickers in self.alpha_map.values():
            for ticker in alpha_tickers:
                self.AddEquity(ticker, Resolution.Daily)

    def update_indicators(self, data) -> Iterator[Symbol]:
        for symbol in self.ActiveSecurities.Keys:
            if not data.Bars.ContainsKey(symbol):
                continue
            if symbol not in self.symbol_map:
                self.symbol_map[symbol] = SymbolIndicators()
            self.symbol_map[symbol].update(data.Bars[symbol])
            if not self.symbol_map[symbol].ready:
                continue
            yield symbol

    def OnData(self, data):
        symbols = list(self.update_indicators(data))
        for Alpha in self.alpha_map:
            for signal in Alpha(self, self.symbol_map, data.Bars, symbols).get_signals():
                if signal:
                    symbol, size = signal
                    self.MarketOrder(symbol, size)
