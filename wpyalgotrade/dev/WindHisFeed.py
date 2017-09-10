# -*- coding: UTF-8 -*-

from pyalgotrade import bar
from pyalgotrade import barfeed
from pyalgotrade.barfeed import membf
from pyalgotrade.barfeed import csvfeed
from pyalgotrade import dataseries
from pyalgotrade import resamplebase
from pyalgotrade.utils import dt
from pyalgotrade.utils import csvutils
from WindPy import *

import datetime
import pyalgotrade.logger


logger = pyalgotrade.logger.getLogger("wind")
KTYPE_TO_BASE_FREQUENCY = {'5': bar.Frequency.MINUTE, '15': bar.Frequency.MINUTE, '30': bar.Frequency.MINUTE,
                           '60': bar.Frequency.HOUR
    , 'D': bar.Frequency.DAY, 'W': bar.Frequency.WEEK, 'M': bar.Frequency.MONTH}  # pyalgtrade 真实freq

KTYPE_TO_CALL_FREQUENCY = {'5': bar.Frequency.MINUTE * 5, '15': bar.Frequency.MINUTE * 15,
                           '30': bar.Frequency.MINUTE * 30, '60': bar.Frequency.HOUR
    , 'D': bar.Frequency.DAY, 'W': bar.Frequency.WEEK, 'M': bar.Frequency.MONTH}  # 调用tushare所使用的每隔几分钟启动一次docall


'''def localnow():
    return dt.as_utc(datetime.datetime.now())
'''

def parse_date(date):
    # Sample: 2005-12-30
    # This custom parsing works faster than:
    # datetime.datetime.strptime(date, "%Y-%m-%d")
    datetimes = date.split("/")
    if len(datetimes) == 3:
        year = int(datetimes[0])
        month = int(datetimes[1])
        day = int(datetimes[2])
    else:
        year = int(date.split("-")[0])
        month = int(date.split("-")[1])
        day = int(date.split("-")[2])

    ret = datetime.datetime(year, month, day)
    return ret


class RowParser(csvfeed.RowParser):
    def __init__(self, dailyBarTime, frequency, timezone=None, sanitize=False, barClass=bar.BasicBar):
        self.__dailyBarTime = dailyBarTime
        self.__frequency = frequency
        self.__timezone = timezone
        self.__sanitize = sanitize
        self.__barClass = barClass

    def __parseDate(self, dateString):
        #print dateString
        #ret = parse_date(dateString)
        ret = dateString
        # Time on Yahoo! Finance CSV files is empty. If told to set one, do it.
        if self.__dailyBarTime is not None:
            ret = datetime.datetime.combine(ret, self.__dailyBarTime)
        # Localize the datetime if a timezone was given.
        if self.__timezone:
            ret = dt.localize(ret, self.__timezone)
        return ret

    def getFieldNames(self):
        # It is expected for the first row to have the field names.
        return None

    def getDelimiter(self):
        return ","

    def parseBar(self, csvRowDict):
        dateTime = self.__parseDate(csvRowDict["Date"])
        close = float(csvRowDict["CLOSE"])
        open_ = float(csvRowDict["OPEN"])
        high = float(csvRowDict["HIGH"])
        low = float(csvRowDict["LOW"])
        volume = 100000000
        # Since w.wsd doesn't support volume, the volume here is big enough.
        adjClose = float(csvRowDict["CLOSE"])

        '''if self.__sanitize:
            open_, high, low, close = common.sanitize_ohlc(open_, high, low, close)
        '''

        return self.__barClass(dateTime, open_, high, low, close, volume, adjClose, self.__frequency)


class CSVRowParser(csvfeed.RowParser):
    def __init__(self, dailyBarTime, frequency, timezone=None, sanitize=False, barClass=bar.BasicBar):
        self.__dailyBarTime = dailyBarTime
        self.__frequency = frequency
        self.__timezone = timezone
        self.__sanitize = sanitize
        self.__barClass = barClass

    def __parseDate(self, dateString):
        ret = parse_date(dateString)
        # Time on Yahoo! Finance CSV files is empty. If told to set one, do it.
        if self.__dailyBarTime is not None:
            ret = datetime.datetime.combine(ret, self.__dailyBarTime)
        # Localize the datetime if a timezone was given.
        if self.__timezone:
            ret = dt.localize(ret, self.__timezone)
        return ret

    def getFieldNames(self):
        # It is expected for the first row to have the field names.
        fieldnames = ['empty', 'instrument', 'abbr', 'date', 'open', 'high', 'low', 'close', 'volume']
        return None

    def getDelimiter(self):
        return ","

    def parseBar(self, csvRowDict):
        dateTime = self.__parseDate(csvRowDict['\xc8\xd5\xc6\xda'])
        close = float(csvRowDict['\xca\xd5\xc5\xcc\xbc\xdb(\xd4\xaa)'])
        open_ = float(csvRowDict['\xbf\xaa\xc5\xcc\xbc\xdb(\xd4\xaa)'])
        high = float(csvRowDict['\xd7\xee\xb8\xdf\xbc\xdb(\xd4\xaa)'])
        low = float(csvRowDict['\xd7\xee\xb5\xcd\xbc\xdb(\xd4\xaa)'])
        volume = int(csvRowDict['\xb3\xc9\xbd\xbb\xc1\xbf(\xb9\xc9)'])
        adjClose = close

        ''' if self.__sanitize:
            open_, high, low, close = common.sanitize_ohlc(open_, high, low, close)
        '''

        return self.__barClass(dateTime, open_, high, low, close, volume, adjClose, self.__frequency)


class Feed(membf.BarFeed):
    def __init__(self, frequency=bar.Frequency.DAY, timezone=None, maxLen=dataseries.DEFAULT_MAX_LEN):
        w.start()

        if not w.isconnected():
            raise Exception('Wind is not connected!')

        '''if isinstance(timezone, int):
            raise Exception(
                "timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")
        '''

        if frequency not in [bar.Frequency.DAY, bar.Frequency.WEEK, bar.Frequency.MINUTE]:
            raise Exception("Invalid frequency.")

        super(Feed, self).__init__(frequency, maxLen)
        self.__barFilter = None
        self.__dailyTime = datetime.time(0, 0, 0)

        self.__timezone = timezone
        self.__sanitizeBars = False
        self.__barClass = bar.BasicBar

    def barsHaveAdjClose(self):
        return True

    def getDailyBarTime(self):
        return self.__dailyTime

    def setDailyBarTime(self, time):
        self.__dailyTime = time

    def getBarFilter(self):
        return self.__barFilter

    def setBarFilter(self, barFilter):
        self.__barFilter = barFilter

    def addBarsFromWind(self, instrument, fields, startdate, enddate, timezone = None):

        if isinstance(timezone, int):
            raise Exception(
                "timezone as an int parameter is not supported anymore. Please use a pytz timezone instead.")

        if timezone is None:
            timezone = self.__timezone

        loadedBars = []

        data = w.wsd(instrument, fields, startdate, enddate)
        # print 'w.wsd(' + instrument + ',' + str(fields) + ',' +startdate + ',' + enddate+')'
        reader = data.Data
        reader.append(data.Times)
        fields.append('Date')
        reader = map(list, zip(*reader))

        if len(reader) < 1:
            raise Exception('Cannot acquire data!')

        rowParser = RowParser(self.getDailyBarTime(), self.getFrequency(), timezone, self.__sanitizeBars, self.__barClass)

        for row in reader:
            if len(row) != len(fields):
                continue
            dictRow = dict((n, v) for n, v in zip(fields, row))
            bar_ = rowParser.parseBar(dictRow)
            if bar_ is not None and (self.__barFilter is None or self.__barFilter.includeBar(bar_)):
                loadedBars.append(bar_)

        self.addBarsFromSequence(instrument, loadedBars)

    def addBarsFromCSV(self, instrument, path, timezone=None):
        """Loads bars for a given instrument from a CSV formatted file.
        The instrument gets registered in the bar feed.
        :param instrument: Instrument identifier.
        :type instrument: string.
        :param path: The path to the CSV file.
        :type path: string.
        :param timezone: The timezone to use to localize bars. Check :mod:`pyalgotrade.marketsession`.
        :type timezone: A pytz timezone.
        """

        loadedBars = []
        csvrowParser = CSVRowParser(
            self.getDailyBarTime(), self.getFrequency(), timezone, self.__sanitizeBars, self.__barClass
        )

        reader = csvutils.FastDictReader(open(path, "r"), fieldnames=csvrowParser.getFieldNames(), delimiter=csvrowParser.getDelimiter())


        for row in reader:
            bar_ = csvrowParser.parseBar(row)
            if bar_ is not None and (self.__barFilter is None or self.__barFilter.includeBar(bar_)):
                loadedBars.append(bar_)

        self.addBarsFromSequence(instrument, loadedBars)

