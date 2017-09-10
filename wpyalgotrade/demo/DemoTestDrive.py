# -*- coding: utf-8 -*-

from wpyalgotrade.dev import WindHisFeed
from wpyalgotrade.dev import WindCSVFeed
from wpyalgotrade.dev import Volatility

import matplotlib.pyplot as pyplot
from pylab import *

from pyalgotrade.stratanalyzer import returns
from pyalgotrade.stratanalyzer import sharpe
from pyalgotrade.stratanalyzer import drawdown
from pyalgotrade.stratanalyzer import trades
from pyalgotrade.broker import backtesting
from pyalgotrade.broker import slippage
from pyalgotrade.broker import fillstrategy
from pyalgotrade import plotter

from WindBollingerDemo import BBands
from WindHisDemo import SMACrossOver
from FOFStrategyDemo import EqualWeight
from FOFStrategyDemo import RiskBudget
from FOFStrategyDemo import TargetRisk

from wpyalgotrade.dev import ReportGenerator

if __name__ == '__main__':
    # 确定所需标的
    instruments = ['600030.SH']
    # instruments = ['000300.SH', '000905.SH', 'H11008.CSI', 'gold', 'wti', "NH0100"]

    # 加载相关数据(使用Wind)
    feed = WindHisFeed.Feed()
    for i in instruments:
        feed.addBarsFromWind(i, ['CLOSE', 'HIGH', 'LOW', 'OPEN'], '2015-01-01', '2017-08-01')

    # 加载相关数据(使用CSV文件)
    '''feed = WindHisFeed.Feed()
    feed.addBarsFromCSV("000300.SH", "data/000300.SH.CSV")
    feed.addBarsFromCSV("000905.SH", "data/000905.SH.CSV")
    feed.addBarsFromCSV("H11008.CSI", "data/H11008.CSI.CSV")
    feed.addBarsFromCSV("gold", "data/gold.csv")
    feed.addBarsFromCSV("wti", "data/wti.csv")
    feed.addBarsFromCSV("NH0100", "data/NH0100.CSV")'''

    report = ReportGenerator.Report()

    # 加载比较数据(可选)
    # benchmark = '000300.SH'
    # feed.addBarsFromWind(benchmark, ['CLOSE', 'HIGH', 'LOW', 'OPEN'], '2009-01-01', '2017-08-01')

    # 加载交易费用(可选)
    '''broker_commission = backtesting.TradePercentage(0.0001)
    slip = slippage.NoSlippage()
    fill = fillstrategy.DefaultStrategy(volumeLimit=0.1)
    fill.setSlippageModel(slip)
    brk = backtesting.Broker(1000000, feed, broker_commission)
    brk.setFillStrategy(fill)'''

    # 设置策略所需变量
    bBandsPeriod = 30
    sma_period = 10
    refresh = 20
    budget = [1.0/len(instruments) for i in range(len(instruments))]
    targetvol = 0.1
    # budget = [0.1, 0.1, 0.6, 0.1, 0.1]

    # 选择策略
    # myStrategy = BBands(feed, instruments, bBandsPeriod)
    myStrategy = SMACrossOver(feed, instruments, sma_period, None, report)
    # myStrategy = EqualWeight(feed, instruments, refresh)
    # myStrategy = TargetRisk(feed, instruments, refresh, targetvol, 250)
    # myStrategy = RiskBudget(feed, instruments, refresh, budget, 250)

    # 加载分析指标
    returnsAnalyzer = returns.Returns()
    myStrategy.attachAnalyzer(returnsAnalyzer)
    sharpeRatioAnalyzer = sharpe.SharpeRatio()
    myStrategy.attachAnalyzer(sharpeRatioAnalyzer)
    drawDownAnalyzer = drawdown.DrawDown()
    myStrategy.attachAnalyzer(drawDownAnalyzer)
    volAnalyzer = Volatility.Volatility()
    myStrategy.attachAnalyzer(volAnalyzer)

    # 加载画图选项
    plt = plotter.StrategyPlotter(myStrategy, False, True, True)
    plt.getPortfolioSubplot()

    # 运行策略
    myStrategy.run()

    # 输出分析指标
    myStrategy.info("Final portfolio value: $%.2f" % myStrategy.getResult())
    myStrategy.info("Sharpe ratio: %.2f" % sharpeRatioAnalyzer.getSharpeRatio(0.02))
    myStrategy.info("Max. drawdown: %.2f %%" % (drawDownAnalyzer.getMaxDrawDown() * 100))
    myStrategy.info("Volatility: %.2f %%" % (volAnalyzer.getVolatility() * 100))

    # 画图
    plt.plot()
