import numpy as np
import const
import SlidingWindow as sw

SAMPLING_LINES = 5

WHITE_THRESHOLD_BASE = 0xe0
WHITE_THRESHOLD = SAMPLING_LINES * WHITE_THRESHOLD_BASE


class SampleLine:
    @staticmethod
    def getValue(data, slideWindow):
        data = np.swapaxes(data,0,1)
        i = const.SAMPLING_WIDTH
        slideWindow.initData(data[:i])
        min = slideWindow.total
        x = i
        i1 = data.shape[0]
        while i<i1:
            slideWindow.append(data[i])
            i += 1
            if min>slideWindow.total:
                min = slideWindow.total
                x = i
        value = SampleLine.__calculateValue(data[x-const.SAMPLING_WIDTH:x,:])
        return value, x-const.SAMPLING_WIDTH

    @staticmethod
    def __calculateValue( data):
        count = data.size
        data = data.reshape((-1))
        data = np.sort(data)
        i0 = (count>>3)
        i1 = count>>2
        value = np.average(data[i0:i1])
        # value += 0xff - bgColor

        # print("val:",value)
        return value

    # @staticmethod
    # def __calculateYValue( data):
    #     count = data.shape[0]
    #     data = np.sort(data)
    #     i0 = (count>>3)
    #     i1 = count>>2
    #     if (i1<2+i0):
    #         i0 = 1
    #         i1 = 4
    #     # value = np.average(data[i0:i1])
    #     value = data[(i0 + i1)>>1]
    #
    #     print(value)
    #     return value

    def __init__(self, data, x):
        self.lines = np.asarray(data)
        self.x0 = x
        self.x1 = x
        self.value = -1.0

    def add(self, data, x):
        self.lines = np.append(self.lines, data)
        self.x1 += 1
        assert self.x1==x

    def getSampleValueBySeletedRegion(self, bgColor):
        filter = self.lines < WHITE_THRESHOLD
        testSamples = self.lines[filter]
        count = testSamples.shape[0]
        l = self.lines.shape[0]
        # 异常
        if self.x1-self.x0<const.SAMPLING_MIN_WIDTH:
            return -1
        if self.x1 - self.x0 > const.SAMPLING_MAX_WIDTH:
            return -2
        if count < l - (l >> 1) :
            return -4
        if count < 5:
            return -8

        self.value = self.__calculateValue(testSamples, bgColor)

