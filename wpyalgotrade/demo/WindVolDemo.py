# -*- coding: UTF-8 -*-

from pyalgotrade import strategy
from pyalgotrade.technical import stats
from pyalgotrade import plotter
from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
from wpyalgotrade.dev import WindHisFeed

import datetime
import numpy as np

class Volatility(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, refresh, volwindow, benchmark, volthreshold=0.2, retthreshold=0.1, riskfree=0.035):
        super(Volatility, self).__init__(feed)
        self.__instrument = instrument
        self.__position = None
        self.setUseAdjustedValues(True)
        self.__prices = feed[instrument].getPriceDataSeries()

        self.__refresh = refresh
        self.__volwindow = volwindow
        self.__volthreshold = volthreshold
        self.__retthreshold = retthreshold
        self.__riskfree = riskfree
        self.__benchmark = benchmark

    def getVolatility(self, instrument):
        prices = self.getFeed()[instrument].getPriceDataSeries()
        values = np.asarray(prices[-1 * self.__volwindow : -1])
        rts = values / np.roll(values, 1) - 1
        return np.std(rts[1:])

    def getReturnIndex(self, instrument):
        bm_price = self.getFeed()[self.__benchmark].getPriceDataSeries()
        price = self.getFeed()[instrument].getPriceDataSeries()

        bm_ret = bm_price[-1] / bm_price[-1 * self.__volwindow] - 1
        ret = price[-1] / price[-1 * self.__volwindow] - 1
        return (ret-self.__riskfree)/(bm_ret-self.__riskfree)


    def onEnterOk(self, position):
        execInfo = position.getEntryOrder().getExecutionInfo()
        self.info("BUY at $%.2f" % (execInfo.getPrice()))

    def onEnterCanceled(self, position):
        self.__position = None

    def onExitOk(self, position):
        execInfo = position.getExitOrder().getExecutionInfo()
        self.info("SELL at $%.2f" % (execInfo.getPrice()))
        self.__position = None

    def onExitCanceled(self, position):
        self.__position = None

    def onBars(self, bars):
        priceDS = self.getFeed()[self.__instrument].getPriceDataSeries()
        if len(priceDS) % self.__refresh == 0 and len(priceDS) >= self.__volwindow:
            vol = self.getVolatility(self.__instrument)
            retindex = self.getReturnIndex(self.__instrument)

            if self.__position is None:
                if vol < self.__volthreshold and retindex < self.__retthreshold:
                    shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument].getPrice())
                    # Enter a buy market order. The order is good till canceled.
                    self.__position = self.enterLong(self.__instrument, shares, True)
            elif not self.__position.exitActive() and (vol > self.__volthreshold or retindex > self.__retthreshold):
                self.__position.exitMarket()

# 以下可以转移至DemoTestDrive.py中
if __name__ == '__main__':
    benchmark = '000300.SH'
    feed = WindHisFeed.Feed()
    # fields = ['CLOSE', 'HIGH', 'LOW', 'OPEN']
    feed.addBarsFromWind('600030.SH', ['CLOSE', 'HIGH', 'LOW', 'OPEN'], '2015-01-06', '2017-08-01')
    feed.addBarsFromWind(benchmark, ['CLOSE', 'HIGH', 'LOW', 'OPEN'], '2015-01-06', '2017-08-01')

    # Evaluate the strategy with the feed's bars.
    myStrategy = Volatility(feed, '600030.SH', 60, 20, benchmark, 0.2, 0.1, 0.035)

    # Attach a returns analyzers to the strategy.
    returnsAnalyzer = returns.Returns()
    myStrategy.attachAnalyzer(returnsAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    myStrategy.attachAnalyzer(sharpeRatioAnalyzer)
    drawDownAnalyzer = drawdown.DrawDown()
    myStrategy.attachAnalyzer(drawDownAnalyzer)
    tradesAnalyzer = trades.Trades()
    myStrategy.attachAnalyzer(tradesAnalyzer)

    # Attach the plotter to the strategy.
    plt = plotter.StrategyPlotter(myStrategy)
    # Include the SMA in the instrument's subplot to get it displayed along with the closing prices.
    # plt.getInstrumentSubplot('600030.SH').addDataSeries("SMA", myStrategy.getSMA())
    # Plot the simple returns on each bar.
    plt.getOrCreateSubplot("returns").addDataSeries("Simple returns", returnsAnalyzer.getReturns())

    # Run the strategy.
    myStrategy.run()
    myStrategy.info("Final portfolio value: $%.2f" % myStrategy.getResult())
    myStrategy.info("Sharpe ratio: $%.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.05))
    myStrategy.info("Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100))

    # Plot the strategy.
    plt.plot()

