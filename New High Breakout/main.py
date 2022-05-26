from QuantConnect import Resolution
from QuantConnect.Algorithm import QCAlgorithm
from QuantConnect.Brokerages import BrokerageName
from QuantConnect.Indicators import SimpleMovingAverage, RateOfChange, Maximum


class NewHighBreakout(QCAlgorithm):

    def Initialize(self):
        self.SetBrokerageModel(BrokerageName.InteractiveBrokersBrokerage)
        self.SetStartDate(2021, 1, 1)
        self.SetEndDate(2022, 1, 1)
        self.SetCash(10000)
        self.UniverseSettings.Resolution = Resolution.Daily
        self.spy = self.AddEquity("SPY", Resolution.Daily)
        self.AddUniverse(self.coarse_selection)
        self.averages = {}
        self._changes = None

    def update_spy(self):
        if self.spy.Symbol not in self.averages:
            history = self.History(self.spy.Symbol, 50, Resolution.Daily)
            self.averages[self.spy.Symbol] = SPYSelectionData(history)
        self.averages[self.spy.Symbol].update(self.Time, self.spy.Price)

    def coarse_selection(self, coarse):
        self.update_spy()
        stocks = []
        for stock in sorted(coarse, key=lambda x: x.DollarVolume, reverse=True)[:100]:
            symbol = stock.Symbol
            if symbol == self.spy.Symbol:
                continue
            if symbol not in self.averages:
                self.averages[symbol] = SelectionData(self.History(symbol, 50, Resolution.Daily))
            self.averages[symbol].update(self.Time, stock)
            if stock.Price > self.averages[symbol].ma.Current.Value:
                stocks.append(stock)
        stocks = sorted(stocks, key=lambda stock: self.averages[stock.Symbol].roc, reverse=True)[:10]
        return [stock.Symbol for stock in stocks]

    @property
    def spy_downtrending(self) -> bool:
        return self.averages[self.spy.Symbol].ma.Current.Value > self.spy.Price

    def OnData(self, slice) -> None:
        if self.spy_downtrending:
            for security in self.Portfolio.Securities.keys():
                self.Liquidate(self.Portfolio.Securities[security].Symbol)
            return
        for symbol in self.ActiveSecurities.Keys:
            if symbol == self.spy.Symbol:
                continue
            if self.ActiveSecurities[symbol].Invested:
                if self.averages[symbol].is_ready() and \
                        self.ActiveSecurities[symbol].Close < self.averages[symbol].ma.Current.Value:
                    self.Liquidate(symbol)
            else:
                if self.averages[symbol].is_ready() and \
                        self.ActiveSecurities[symbol].Close >= self.averages[symbol].highs.Current.Value:
                    position_value = self.Portfolio.TotalPortfolioValue / 10
                    if position_value < self.Portfolio.Cash:
                        self.MarketOrder(symbol, int(position_value / self.ActiveSecurities[symbol].Price))


class SelectionData():
    def __init__(self, history):
        self.roc = RateOfChange(50)
        self.ma = SimpleMovingAverage(50)
        self.highs = Maximum(50)

        for data in history.itertuples():
            self.roc.Update(data.Index[1], data.close)
            self.ma.Update(data.Index[1], data.close)
            self.highs.Update(data.Index[1], data.high)

    def is_ready(self):
        return self.roc.IsReady and self.ma.IsReady

    def update(self, time, stock):
        self.roc.Update(time, stock.price)
        self.ma.Update(time, stock.price)
        self.highs.Update(time, stock.high)


class SPYSelectionData():
    def __init__(self, history):
        self.ma = SimpleMovingAverage(200)

        for data in history.itertuples():
            self.ma.Update(data.Index[1], data.close)

    def is_ready(self):
        return self.ma.IsReady

    def update(self, time, price):
        self.ma.Update(time, price)
