from pyalgotrade import strategy
import numpy as np
import statsmodels.api as sm
import scipy.stats as scs
import scipy.optimize as sco
import xlwt


class EqualWeight(strategy.BacktestingStrategy):
    def __init__(self, feed, instruments, refresh):
        super(EqualWeight, self).__init__(feed)
        self.__instrument = instruments
        self.__refresh = refresh
        self.__file = xlwt.Workbook(encoding='utf-8')
        self.__sheet = self.__file.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__totalcash = 1000000
        self.__sheetindex = 0

    def adjustlev(self, weight, pos, lev):
        weight[pos] = weight[pos] * lev
        return weight / np.sum(weight)

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
        priceDS = self.getFeed()[self.__instrument[0]].getPriceDataSeries()
        portfolioValue = 0
        pos = self.getBroker().getPositions()
        if len(pos) > 0:
            for ins in self.__instrument:
                portfolioValue = portfolioValue + self.getBroker().getPositions()[ins] * \
                                                  self.getFeed()[ins].getPriceDataSeries()[-1]
        self.__sheet.write(self.__sheetindex, 0, bars.getDateTime())
        self.__sheet.write(self.__sheetindex, 1, portfolioValue + self.getBroker().getCash())
        self.__file.save(r'values.xls')

        self.__sheetindex += 1

        if len(priceDS) % self.__refresh != 0:
            return
        weight = np.array([1.0 / len(self.__instrument) for i in range(len(self.__instrument))])
        weight = self.adjustlev(weight, 2, 1.4)

        for ins in range(len(self.__instrument)):
            bar = bars[self.__instrument[ins]]
            shares = self.getBroker().getShares(self.__instrument[ins])

            # if shares > 0:
            #     self.marketOrder(self.__instrument[ins], -1 * shares)

            sharesToBuy = int(self.__totalcash * 0.9 * weight[ins] / bar.getClose())

            # print self.__instrument[ins]
            # print bar.getClose()

            self.marketOrder(self.__instrument[ins], sharesToBuy - shares)


class RiskBudget(strategy.BacktestingStrategy):
    # target volatility
    def __init__(self, feed, instruments, refresh, budget, window):
        super(RiskBudget, self).__init__(feed)
        self.__instrument = instruments
        self.__refresh = refresh
        self.__budget = budget
        self.__window = window
        self.__lastweight = np.array([1.0 / len(self.__instrument) for i in range(len(self.__instrument))])
        self.__totalcash = 1000000
        self.__file = xlwt.Workbook(encoding='utf-8')
        self.__file2 = xlwt.Workbook(encoding='utf-8')
        self.__sheet = self.__file.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__sheet2 = self.__file2.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__sheetindex = 0

    def calculateWeights(self):
        prices = []
        for i in range(len(self.__instrument)):
            p = np.asarray(self.getFeed()[self.__instrument[i]].getPriceDataSeries()[-1 * self.__window: -1])
            rts = p / np.roll(p, 1) - 1
            prices.append(rts[1:].tolist())

        retmat = np.array(prices)

        def minRisk(weight):
            w = np.array(weight)
            sigma = np.dot(w.T, np.dot(np.cov(retmat), w))
            rci = np.dot(np.cov(retmat), w) / sigma
            return np.sum((w * rci - np.array(self.__budget) * sigma)**2)

        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        bnds = tuple((0, 1) for x in range(len(self.__instrument)))
        org = np.array([1.0 / len(self.__instrument) for i in range(len(self.__instrument))])
        opts = sco.minimize(minRisk, org, method='SLSQP', bounds=bnds, constraints=cons)

        w = opts['x']
        if w[2] < 0.4:
            w = self.__lastweight

        return w

    def onBars(self, bars):
        priceDS = self.getFeed()[self.__instrument[0]].getPriceDataSeries()
        portfolioValue = 0
        pos = self.getBroker().getPositions()
        if len(pos) > 0:
            for ins in self.__instrument:
                portfolioValue = portfolioValue + self.getBroker().getPositions()[ins] * \
                                                  self.getFeed()[ins].getPriceDataSeries()[-1]
        # print portfolioValue + self.getBroker().getCash()

        self.__sheet.write(self.__sheetindex, 0, bars.getDateTime())
        self.__sheet.write(self.__sheetindex, 1, portfolioValue + self.getBroker().getCash())
        self.__file.save(r'values.xls')
        self.__sheet2.write(self.__sheetindex, 0, bars.getDateTime())
        for i in range(len(self.__lastweight)):
            self.__sheet2.write(self.__sheetindex, i+1, self.__lastweight[i])
        self.__file2.save(r'weights.xls')

        if len(priceDS) % 20 != 0:
            return
        if len(priceDS) < self.__window:
            return

        # calculate weights
        weight = self.calculateWeights()
        self.__lastweight = weight
        self.__sheet2.write(self.__sheetindex, 0, bars.getDateTime())
        for i in range(len(weight)):
            self.__sheet.write(self.__sheetindex, i, self.__lastweight[i])

        print bars.getDateTime()
        print weight

        for ins in range(len(self.__instrument)):
            bar = bars[self.__instrument[ins]]
            shares = self.getBroker().getShares(self.__instrument[ins])
            sharesToBuy = int(self.__totalcash * 0.9 * weight[ins] / bar.getClose())
            self.marketOrder(self.__instrument[ins], sharesToBuy - shares)

        self.__sheetindex += 1


class TargetRisk(strategy.BacktestingStrategy):
    # target volatility
    def __init__(self, feed, instruments, refresh, vol, window):
        super(TargetRisk, self).__init__(feed)
        self.__instrument = instruments
        self.__refresh = refresh
        self.__vol = vol
        self.__window = window
        self.__totalcash = 1000000
        self.__lastweight = np.array([1.0 / len(self.__instrument) for i in range(len(self.__instrument))])
        self.__file = xlwt.Workbook(encoding='utf-8')
        self.__file2 = xlwt.Workbook(encoding='utf-8')
        self.__sheet = self.__file.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__sheet2 = self.__file2.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__sheetindex1 = 0
        self.__sheetindex2 = 0

    def calculateWeights(self):
        prices = []
        expret = []
        for i in range(len(self.__instrument)):
            p = np.asarray(self.getFeed()[self.__instrument[i]].getPriceDataSeries()[-1 * self.__window : -1])
            r = p[-1] / p[0] - 1
            rts = p / np.roll(p, 1) - 1
            prices.append(rts[1:].tolist())
            expret.append(r)

        expret = np.array(expret) / self.__window
        retmat = np.array(prices)
        covmat = np.cov(prices)

        def maxExpectRet(weight):
            w = np.array(weight)
            return -np.dot(w.T, expret)

        cons = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sqrt(np.dot(x.T, np.dot(np.cov(retmat) * 252, x))) - self.__vol})
        bnds = tuple((0, 1) for x in range(len(self.__instrument)))
        org = np.array([1.0 / len(self.__instrument) for i in range(len(self.__instrument))])
        opts = sco.minimize(maxExpectRet, org, method='SLSQP', bounds=bnds, constraints=cons)

        return opts['x']

    def onBars(self, bars):
        priceDS = self.getFeed()[self.__instrument[0]].getPriceDataSeries()

        portfolioValue = 0
        pos = self.getBroker().getPositions()
        if len(pos) > 0:
            for ins in self.__instrument:
                portfolioValue = portfolioValue + self.getBroker().getPositions()[ins] * \
                                                  self.getFeed()[ins].getPriceDataSeries()[-1]

        self.__sheet.write(self.__sheetindex1, 0, bars.getDateTime())
        self.__sheet.write(self.__sheetindex1, 1, portfolioValue + self.getBroker().getCash())
        self.__file.save(r'values.xls')
        self.__sheetindex1 += 1
        self.__sheet2.write(self.__sheetindex2, 0, bars.getDateTime())
        for i in range(len(self.__lastweight)):
            self.__sheet2.write(self.__sheetindex2, i + 1, self.__lastweight[i])
        self.__file2.save(r'weights.xls')

        if len(priceDS) % 20 != 0:
            return
        if len(priceDS) < self.__window:
            return

        # calculate weights
        weight = self.calculateWeights()
        self.__lastweight = weight
        print bars.getDateTime()
        print weight
        for ins in range(len(self.__instrument)):
            bar = bars[self.__instrument[ins]]
            shares = self.getBroker().getShares(self.__instrument[ins])
            # self.marketOrder(self.__instrument[ins], -1 * shares)
            sharesToBuy = int((portfolioValue + self.getBroker().getCash()) * 0.75 * weight[ins] / bar.getClose())
            if sharesToBuy == 0:
                sharesToBuy += 1
            self.marketOrder(self.__instrument[ins], sharesToBuy - shares)

        self.__sheetindex2 += 1