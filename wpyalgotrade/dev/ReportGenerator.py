# -*- coding: utf-8 -*-
import xlrd
import xlwt


class Report(object):
    def __init__(self):
        self.__f = xlwt.Workbook(encoding='utf-8')
        self.__sheet = self.__f.add_sheet(u'sheet1', cell_overwrite_ok=True)
        self.__index = 0
        self.__instrument = None
        self.__direction = None
        self.__volume = 0
        self.__price = 0
        self.__datetime = None

        row0 = [u'datetime', u'instrument', u'direction', u'price', u'volume']
        for i in range(0, len(row0)):
            self.__sheet.write(0, i, row0[i])

    def addInstrument(self, instrument):
        self.__instrument = instrument

    def addVolume(self, volume):
        self.__volume = volume

    def addDirection(self, direction):
        self.__direction = direction

    def addPrice(self, price):
        self.__price = price

    def addDatetime(self, datetime):
        self.__datetime = str(datetime)

    def submit(self):
        self.__index += 1
        try:
            self.__sheet.write(self.__index, 0, self.__datetime)
            self.__sheet.write(self.__index, 1, self.__instrument)
            self.__sheet.write(self.__index, 2, self.__direction)
            self.__sheet.write(self.__index, 3, self.__price)
            self.__sheet.write(self.__index, 4, self.__volume)
            self.__f.save(r'BacktestingReport.xls')
        except Exception:
            print 'Exception'

    def reset(self):
        self.__index = 0
        self.__instrument = None
        self.__direction = None
        self.__volume = 0
        self.__price = 0

    def save(self):
        self.__f.save(r'BacktestingReport.xls')





