from pyalgotrade import strategy
from pyalgotrade import plotter
from pyalgotrade.technical import bollinger
from pyalgotrade.stratanalyzer import sharpe

import xlwt

from wpyalgotrade.dev import WindHisFeed


class BBands(strategy.BacktestingStrategy):
    def __init__(self, feed, instruments, bBandsPeriod):
        super(BBands, self).__init__(feed)
        self.__instrument = instruments
        self.__bbands = [bollinger.BollingerBands(feed[ins].getCloseDataSeries(), bBandsPeriod, 2) for ins in instruments]

        self.__file = xlwt.Workbook(encoding='utf-8')
        self.__sheets = [self.__file.add_sheet(str(ins)) for ins in instruments]
        # self.__sheet = self.__file.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__sheetindex = 1

        row0 = [u'datetime', u'lower', u'middle', u'upper', u'price']
        for i in range(0, len(row0)):
            for ins in range(len(instruments)):
                self.__sheets[ins].write(0, i, row0[i])


    def getBollingerBands(self):
        return self.__bbands

    def onEnterOk(self, position):
        execOrder = position.getEntryOrder()
        self.info("%s BUY at $%.2f" % (execOrder.getInstrument(), execOrder.getExecutionInfo().getPrice()))

    def onExitOk(self, position):
        execOrder = position.getExitOrder()
        self.info("%s SELL at $%.2f" % (execOrder.getInstrument(), execOrder.getExecutionInfo().getPrice()))

    def onBars(self, bars):
        for ins in range(len(self.__instrument)):
            lower = self.__bbands[ins].getLowerBand()[-1]
            upper = self.__bbands[ins].getUpperBand()[-1]
            middle = self.__bbands[ins].getMiddleBand()[-1]

            if lower is None:
                return

            price = self.getFeed()[self.__instrument[ins]].getPriceDataSeries()[-1]
            self.__sheets[ins].write(self.__sheetindex, 0, bars.getDateTime())
            self.__sheets[ins].write(self.__sheetindex, 1, lower)
            self.__sheets[ins].write(self.__sheetindex, 2, upper)
            self.__sheets[ins].write(self.__sheetindex, 3, middle)
            self.__sheets[ins].write(self.__sheetindex, 4, price)
            self.__file.save(r'bollinger.xls')

            '''shares = self.getBroker().getShares(self.__instrument[ins])
            bar = bars[self.__instrument[ins]]
            if shares == 0 and bar.getClose() < lower:
                sharesToBuy = int(self.getBroker().getCash(False) / len(self.__instrument) / bar.getClose())
                self.marketOrder(self.__instrument[ins], sharesToBuy)
            elif shares > 0 and bar.getClose() > upper:
                self.marketOrder(self.__instrument[ins], -1 * shares)'''

        self.__sheetindex += 1