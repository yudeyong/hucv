import numpy as np
import const

SAMPLING_LINES = 5

WHITE_THRESHOLD = SAMPLING_LINES * 0xe0


class SampleLine:
    def __init__(self, data, x):
        self.lines = np.asarray(data)
        self.x0 = x
        self.x1 = x
        self.value = -1.0

    def add(self, data, x):
        self.lines = np.append(self.lines, data)
        self.x1 += 1
        assert self.x1==x

    def getSampleValue(self, bgColor):
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

        testSamples = np.sort(testSamples)
        i0 = (count>>3)
        i1 = count>>2

        if (i1<2+i0):
            i0 = 1
            i1 = 4
        value = np.average(testSamples[i0:i1])
        value = 0xff - value
        value -= bgColor
        self.value = value
        print(value)
        return value
