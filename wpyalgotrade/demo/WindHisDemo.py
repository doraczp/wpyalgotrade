# -*- coding: utf-8 -*-

from pyalgotrade import strategy
from pyalgotrade.technical import ma
from pyalgotrade.technical import cross


class SMACrossOver(strategy.BacktestingStrategy):
    def __init__(self, feed, instrument, smaPeriod, brk=None, report=None):
        # super(SMACrossOver, self).__init__(feed, brk)
        super(SMACrossOver, self).__init__(feed)
        self.__instrument = instrument
        self.__position = [None for i in range(len(instrument))]
        self.setUseAdjustedValues(True)
        self.__prices = [feed[ins].getPriceDataSeries() for ins in instrument]

        self.__sma = [ma.SMA(self.__prices[i], smaPeriod) for i in range(len(instrument))]
        self.__report = report

    def getSMA(self, i):
        return self.__sma[i]

    def onEnterOk(self, position):
        execOrder = position.getEntryOrder()
        self.info("%s BUY at $%.2f" % (execOrder.getInstrument(), execOrder.getExecutionInfo().getPrice()))
        self.__report.addDatetime(execOrder.getSubmitDateTime())
        self.__report.addDirection('BUY')
        self.__report.addPrice(execOrder.getExecutionInfo().getPrice())
        self.__report.addVolume(execOrder.getQuantity())
        self.__report.submit()

    def onEnterCanceled(self, position):
        index = self.__position.index(position)
        self.__position[index] = None

    def onExitOk(self, position):
        execOrder = position.getExitOrder()
        self.info("%s SELL at $%.2f" % (execOrder.getInstrument(), execOrder.getExecutionInfo().getPrice()))
        self.__report.addDatetime(execOrder.getSubmitDateTime())
        self.__report.addDirection('SELL')
        self.__report.addPrice(execOrder.getExecutionInfo().getPrice())
        self.__report.addVolume(execOrder.getQuantity())
        self.__report.submit()
        index = self.__position.index(position)
        self.__position[index] = None

    def onExitCanceled(self, position):
        # If the exit was canceled, re-submit it.
        index = self.__position.index(position)
        self.__position[index].exitMarket()

    def onBars(self, bars):
        # If a position was not opened, check if we should enter a long position.
        for ins in range(len(self.__instrument)):
            if self.__position[ins] is None:
                if cross.cross_above(self.__prices[ins], self.__sma[ins]) > 0:
                    shares = int(self.getBroker().getCash() * 0.9 / bars[self.__instrument[ins]].getPrice())
                    # Enter a buy market order. The order is good till canceled.
                    self.__report.addInstrument(self.__instrument[ins])
                    # self.__position = self.enterLong(self.__instrument[ins], shares, True)
                    try:
                        self.__position[ins] = self.enterLong(self.__instrument[ins], shares, True)
                    except:
                        self.error('Not enough cash!')

            # Check if we have to exit the position.
            elif not self.__position[ins].exitActive() and cross.cross_below(self.__prices[ins], self.__sma[ins]) > 0:
                self.__report.addInstrument(self.__instrument[ins])
                self.__position[ins].exitMarket()