import numpy as np
import utils
import SampleLine as sl

class StripRegion:
    def __init__(self, points):
        self.points = points
        self.slopes = [2]*2
        self.slopes[0] = utils.getSlopeBiasByPoints(points[0], points[1])
        self.slopes[1] = utils.getSlopeBiasByPoints(points[2], points[3])
        self.samples = []
        #为方便计算, bgColor = 0xff-色值
        self.bgColor = 0

    def __getBackground(self, i, data, record):
        for d in data:
            r = record[d>>16]
            r[0] += 1
            r[1] += d

    def __traversal(self, gray, func, funcPara ):
        i = self.left
        i1 = self.right
        while (i<i1):
            i += 1
            y = int(i * self.slope + self.bias)
            data = gray[y:y+sl.SAMPLING_LINES,i]
            func(i, data, funcPara)

    def __sampling(self, i, data, lastSample):
        threshold = sl.WHITE_THRESHOLD-self.bgColor
        total = np.sum(data)
        if (total < threshold):
            if lastSample[0] != i - 1:
                sample = sl.SampleLine(data, i)
                self.samples.insert(0,sample)
            else:
                self.samples[0].add(data, i)
            lastSample[0] = i

    def readStrip(self, gray, bw):
        colors = [[0,0]] * 16
        self.left = i = max(self.points[0][0], self.points[2][0])
        self.right = i1 = min(self.points[1][0], self.points[3][0])

        self.slope,self.bias = utils.getSlopeBiasByPoints(
            (i, (self.points[0][1] + self.points[2][1]) >> 1),
        (i1, (self.points[1][1] + self.points[3][1]) >> 1))
        self.bias -= sl.SAMPLING_LINES>>1
        lastSample = [-3]
        self.__traversal(gray, self.__getBackground, colors)
        maxColorIndex = colors.index(max(colors, key=lambda x: x[0]))
        self.bgColor = 0xff - round(colors[maxColorIndex][1] / colors[maxColorIndex][0])
        self.__traversal(gray, self.__sampling, lastSample)

        if False:
            while (i<i1):
                i += 1
                y = int(i * self.slope + self.bias)
                data = gray[y:y+sl.SAMPLING_LINES,i]
                self.__getBackground( data, colors)
                total = np.sum(data)
                if (total<sl.WHITE_THRESHOLD) :
                    if lastSample != i-1:
                        sample = sl.SampleLine(data, i)
                        self.samples.append(sample)
                    else:
                        sample.add(data,i)
                    lastSample = i
                # else:
                #     if lastSample == i-1:
                #         print(i-i0, total/sl.SAMPLING_LINES)

            maxColorIndex = colors.index(max(colors, key=lambda x: x[0]))
            self.bgColor = 0xff-round( colors[maxColorIndex][1]/colors[maxColorIndex][0] )

        self.__getValues()

        i = self.samples[len(self.samples)-1]
        y = int(i.x0 * self.slope + self.bias)
        gray[y:y+5,i.x0:i.x1] = 0xff
        print("****** background color:",self.bgColor)

    def __getValues(self):
        for line in self.samples:
            print("value",line.getSampleValue( self.bgColor))
            break