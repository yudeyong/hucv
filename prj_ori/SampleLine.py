import numpy as np
import const
import SlidingWindow as sw

SAMPLING_LINES = 5

WHITE_THRESHOLD_BASE = 0xe0
WHITE_THRESHOLD = SAMPLING_LINES * WHITE_THRESHOLD_BASE


class SampleLine:
    @staticmethod
    def getValue(data, listP, mid):
        if (len(listP)>4) :
            listP = listP[1:-1]
            mid -= 2
        else: mid -= 1
        x1 = listP[mid][0]
        x2 = listP[mid][1]
        d = data[listP[-1][2]:listP[0][2],x1:x2]
        v = SampleLine.__calculateValue(d)
        data[listP[-1][2]:listP[0][2],x1:x2] = 0
        return v
    @staticmethod
    def __calculateValue( data):
        count = data.size
        data = data.reshape((-1))
        data = np.sort(data)
        value = count>>4
        i0 = (count>>3)+value
        i1 = (count>>2)+value
        value = np.average(data[i0:i1])
        # value += 0xff - bgColor

        # print("val:",value)
        return value

    def __init__(self, data, x):
        self.lines = np.asarray(data)
        self.x0 = x
        self.x1 = x
        self.value = -1.0

    @staticmethod
    def isSamePoint(p1, p2):
        return abs(p1[0] - p2[0]) <= const.SAMPLING_WIDTH and \
               abs(p1[1] - p2[1]) <= const.SAMPLING_WIDTH

    @staticmethod
    def isSameRect(ps1, ps2):
        return SampleLine.isSamePoint(ps1[0], ps2[0]) and \
               SampleLine.isSamePoint(ps1[1], ps2[1]) and \
               SampleLine.isSamePoint(ps1[2], ps2[2]) and \
               SampleLine.isSamePoint(ps1[3], ps2[3])

    @staticmethod
    def isLineSize(point):
        deltaX, deltaY = point
        if deltaX > const.SAMPLING_WIDTH + (const.SAMPLING_WIDTH >> 2): return None
        if deltaX <= (const.SAMPLING_WIDTH >>1): return None
        if deltaY < const.STRIP_HALF_HEIGHT: return None
        if deltaY > const.STRIP_HEIGHT << 1: return None
        return True

    def add(self, data, x):
        self.lines = np.append(self.lines, data)
        self.x1 += 1
        assert self.x1==x

    def getSampleValueBySeletedRegion(self):
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

        self.value = self.__calculateValue(testSamples)
