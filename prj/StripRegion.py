import cv2
import numpy as np
import utils
import SampleLine as sl

class StripRegion:
    def __init__(self, points, template):
        self.points = points
        # self.slopes = [2]*2
        # self.slopes[0] = utils.getSlopeBiasByPoints(points[0], points[1])
        # self.slopes[1] = utils.getSlopeBiasByPoints(points[2], points[3])
        self.template = template
        self.samples = []
        #为方便计算, bgColor = 0xff-色值
        self.bgColor = 0

    def __getBackground(self, i, data, record):
        for d in data:
            r = record[d>>16]
            r[0] += 1
            r[1] += d

    def __traversal(self, img, func, funcPara ):
        i = self.left
        i1 = self.right
        while (i<i1):
            i += 1
            y = int(i * self.slope + self.bias)
            data = img[y:y+sl.SAMPLING_LINES,i]
            func(i, data, funcPara)

    def __sampling(self, i, data, lastSample):
        # t1 = t+b-(b*t)/0xff
        b = self.bgColor
        # threshold = sl.WHITE_THRESHOLD#+self.bgColor
        threshold = round(sl.WHITE_THRESHOLD_BASE + b - b* sl.WHITE_THRESHOLD_BASE/0xff)*sl.SAMPLING_LINES
        total = np.sum(data)
        if (total < threshold):
            if lastSample[0] != i - 1:
                sample = sl.SampleLine(data, i)
                self.samples.insert(0,sample)
            else:
                self.samples[0].add(data, i)
            lastSample[0] = i

    def readStrip(self, gray):
        colors = [[0,0]] * 16
        self.left = i = max(self.points[0][0], self.points[2][0])
        self.right = i1 = min(self.points[1][0], self.points[3][0])
        self.top = min(self.points[0][1],self.points[1][1],self.points[2][1],self.points[3][1])
        self.bottom = max(self.points[0][1],self.points[1][1],self.points[2][1],self.points[3][1])

        self.slope,self.bias = utils.getSlopeBiasByPoints(
            (i, (self.points[0][1] + self.points[2][1]) >> 1),
        (i1, (self.points[1][1] + self.points[3][1]) >> 1))
        self.bias -= sl.SAMPLING_LINES>>1
        lastSample = [-3]
        self.__traversal(gray, self.__getBackground, colors)
        maxColorIndex = colors.index(max(colors, key=lambda x: x[0]))


        # 通过背景色识别 监测区域
        self.bgColor = round(colors[maxColorIndex][1] / colors[maxColorIndex][0])
        # bb = gray[ self.top:self.bottom ,self.left:self.right]
        # _, bb = cv2.threshold(bb, int(self.bgColor*1), 255.0, cv2.THRESH_BINARY)
        # cv2.imshow("bb", bb)
        # cv2.waitKey()

        percent = self.template.setPercentage(1, 0)
        # cv2.line(gray, (self.left, self.top), (self.right, self.bottom), (0,0,255), 1)
        # cv2.line(gray, (self.left, self.bottom), (self.right, self.top), (0,0,255), 1)
        length = self.right - self.left -4
        self.left += 15
        for p in percent:
            x = self.left+p[0]*length
            y = int(x*self.slope + self.bias)
            gray[y:y+6, int(x):self.left+int(p[1]*length) ] = 0
            gray[y+2:y + 3, int(x):self.left + int(p[1] * length)] = 0xff
        cv2.imshow("bb", gray)
        # cv2.waitKey()

        return
        self.bgColor = 0xff - round(colors[maxColorIndex][1] / colors[maxColorIndex][0])
        self.__traversal(gray, self.__sampling, lastSample)

        self.__getValues(gray)

        print("****** background color:",self.bgColor)

    def __getValues(self, img):
        for line in self.samples:
            value = line.getSampleValue( self.bgColor)
            # if value<0:continue
            print("value", value)

            y = int(line.x0 * self.slope + self.bias)
            img[y-2:y + 7, line.x0:line.x1] = 0xff
            img[y+1:y + 3, line.x0:line.x1] = 0
