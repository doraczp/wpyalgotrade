# -*- coding: utf-8 -*-

from wpyalgotrade.dev import WindHisFeed
from wpyalgotrade.dev import WindCSVFeed

import matplotlib.pyplot as pyplot
from pylab import *

from pyalgotrade import plotter

from WindBollingerDemo import BBands
from WindHisDemo import SMACrossOver
from FOFStrategyDemo import EqualWeight
from FOFStrategyDemo import RiskBudget
from FOFStrategyDemo import TargetRisk

if __name__ == '__main__':
    # 确定所需标的
    instruments = ["000300.SH", "000905.SH"]

    # 加载相关数据(使用Wind)
    # feed = WindHisFeed.Feed()
    # for i in instruments:
      # feed.addBarsFromWind(i, ['CLOSE', 'HIGH', 'LOW', 'OPEN'], '2017-01-01', '2017-08-01')


    # 加载相关数据(使用CSV文件)
    feed = WindCSVFeed.Feed()
    feed.addBarsFromCSV("000300.SH", "data/000300.SH.CSV")
    feed.addBarsFromCSV("000905.SH", "data/000905.SH.CSV")
    # feed.addBarsFromCSV("H11008.CSI", "data/H11008.CSI.CSV")
    # feed.addBarsFromCSV("gold", "data/gold.csv")
    # feed.addBarsFromCSV("wti", "data/wti.csv")
    # feed.addBarsFromCSV("NH0100", "data/NH0100.CSV")

    # 设置策略所需变量
    bBandsPeriod = 30
    # sma_period = 10
    # refresh = 20
    # budget = [1.0/len(instruments) for i in range(len(instruments))]
    # targetvol = 0.1
    # budget = [0.1, 0.1, 0.6, 0.1, 0.1]

    # 选择策略
    myStrategy = BBands(feed, instruments, bBandsPeriod)
    # myStrategy = SMACrossOver(feed, instruments, sma_period)
    # myStrategy = EqualWeight(feed, instruments, refresh)
    # myStrategy = TargetRisk(feed, instruments, refresh, targetvol, 250)
    # myStrategy = RiskBudget(feed, instruments, refresh, budget, 250)

    # 加载画图选项
    # 这里要画多张图并保存
    plts = []
    for ins in instruments:
        plt = plotter.StrategyPlotter(myStrategy, False, False, False)
        plt.getInstrumentSubplot(ins).addDataSeries("upper", myStrategy.getBollingerBands()[
            instruments.index(ins)].getUpperBand())
        plt.getInstrumentSubplot(ins).addDataSeries("middle", myStrategy.getBollingerBands()[
            instruments.index(ins)].getMiddleBand())
        plt.getInstrumentSubplot(ins).addDataSeries("lower", myStrategy.getBollingerBands()[
            instruments.index(ins)].getLowerBand())
        plts.append(plt)

    # 运行策略
    myStrategy.run()

    # 画图
    i = 0
    for plt in plts:
        f, subplot = plt.buildFigureAndSubplots()
        savefig('fig' + str(i + 1))
        pyplot.show()
        i += 1
