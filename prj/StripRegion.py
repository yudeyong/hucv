import cv2
import numpy as np
import utils
import SampleLine as sl
import const
import SlidingWindow as sw



class StripRegion:
    BG_COLOR = True
    FIRST_LINE_WIDTH = 3
    FIRST_LINE_THRESHOLD = ((FIRST_LINE_WIDTH+1)>>2)*sl.SAMPLING_LINES*0xff

    def __init__(self, points, template):
        self.points = points
        # self.slopes = [2]*2
        # self.slopes[0] = utils.getSlopeBiasByPoints(points[0], points[1])
        # self.slopes[1] = utils.getSlopeBiasByPoints(points[2], points[3])
        self.template = template
        self.samples = []
        #为方便计算, bgColor = 0xff-色值
        self.bgColor = 0
        self.left = max(points[0][0], points[2][0])
        self.right = min(points[1][0], points[3][0])-const.SAMPLING_WIDTH
        self.top = min(points[0][1],points[1][1],points[2][1],points[3][1])
        self.bottom = max(points[0][1],points[1][1],points[2][1],points[3][1])
        self.slope,self.bias = utils.getSlopeBiasByPoints(
            (self.left, (points[0][1] + points[2][1]) >> 1), (self.right, (points[1][1] + points[3][1]) >> 1))
        self.valueAndPosi = []

    def __getDataByX(self, img, x):
        y = int(x * self.slope + self.bias)
        return img[y:y + sl.SAMPLING_LINES, x]

    def __traversal(self, img, left, func, funcPara ):
        i = left
        i1 = self.right
        while (i<i1):
            i += 1
            data = self.__getDataByX(img, i)
            if func(i, data, funcPara):
                return True
        return False

    def __findFirstLine(self, i, data, record):
        total = self.window.append(data)
        if (total < StripRegion.FIRST_LINE_THRESHOLD):
            self.firstLine = i - (StripRegion.FIRST_LINE_WIDTH>>1)
            return True
        else:
            return False

    def __getBackground(self, i, data, record):
        for d in data:
            r = record[d>>16]
            r[0] += 1
            r[1] += d

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

    def __getBkColor(self, gray):
        if not StripRegion.BG_COLOR: return
        colors = [[0,0]] * 16
        self.__traversal(gray, self.left, self.__getBackground, colors)

        maxColorIndex = colors.index(max(colors, key=lambda x: x[0]))
        self.bgColor = 0xff - round(colors[maxColorIndex][1] / colors[maxColorIndex][0])

    def readStrip(self, gray):
        self.__getBkColor(gray)

        self.__getValuesByPostion(gray)

        return
    '''
        # 通过背景色识别 监测区域
        # bb = gray[ self.top:self.bottom ,self.left:self.right]
        # _, bb = cv2.threshold(bb, int(self.bgColor*1), 255.0, cv2.THRESH_BINARY)
        # cv2.imshow("bb", bb)
        # cv2.waitKey()

        lastSample = [-3]
        self.bgColor = 0xff - round(colors[maxColorIndex][1] / colors[maxColorIndex][0])
        self.__traversal(gray, self.left, self.__sampling, lastSample)

        self.__getValues(gray)

        print("****** background color:",self.bgColor)
    '''

    def __setSymbleDebug(self, gray, x1, x2, y):
        gray[y:y + 6, x1:x2] = 0
        gray[y + 2:y + 3, x1:x2] = 0xff

    def findFuncLine(self, bw):
        self.window = sw.SlidingWindgow(StripRegion.FIRST_LINE_WIDTH)
        i = 0
        i1 = self.left + const.SAMPLING_WIDTH
        data = np.empty([StripRegion.FIRST_LINE_WIDTH,sl.SAMPLING_LINES])
        while i<StripRegion.FIRST_LINE_WIDTH:
            data[i, :] = self.__getDataByX(bw, i1)
            i += 1
        self.window.initData(data)
        self.__traversal(bw, i1, self.__findFirstLine, None)
        # while i<self.right

    ############  deprecated  ###########
    # counter = 0
    def __removeBgColor(self, value):
        value += self.bgColor
        return value if value<0xff else 0xff
    def __getValuesByPostion(self, img):
        percent = self.template.setPercentage(1, 0)
        # cv2.line(gray, (self.left, self.top), (self.right, self.bottom), (0,0,255), 1)
        # cv2.line(gray, (self.left, self.bottom), (self.right, self.top), (0,0,255), 1)
        # self.firstLine = self.left +15

        # StripRegion.counter+=1
        # if (StripRegion.counter!=3) :return

        win = sw.SlidingWindgow(const.SAMPLING_WIDTH)
        length = self.right - self.left

        i = 0
        for p in percent:
            # i += 1
            # if (i!=2) :continue
            x = self.firstLine + p[0]*length -const.SAMPLING_WIDTH
            y = int(x*self.slope + self.bias)
            x = round(x)
            colorValue,offsetx = sl.SampleLine.getValue(img[y-const.SAMPLING_MINUS_Y_OFFSET:y+const.SAMPLING_Y_OFFSET,
                                x:x+(const.SAMPLING_WIDTH<<2) ], win)
            offsetx += x
            self.__setSymbleDebug(img,int(offsetx),int(offsetx+const.SAMPLING_WIDTH), y )
            colorValue = self.__removeBgColor(colorValue)
            self.valueAndPosi.append([colorValue, 0.0,offsetx])

        if (len(self.valueAndPosi)<len(percent)):
            return -1
        print('************ new strip *************')
        cutOff = 0xff-self.valueAndPosi[1][0]
        if cutOff==0:
            return -2
        for v in self.valueAndPosi:
            v[1] = (0xff-v[0]) / cutOff
            print("{:.1f}".format(v[1]), ',', end='')
        print()
        cv2.imshow("bb", img)
        # cv2.waitKey()

    def __getValuesByRegion(self, img):
        for line in self.samples:
            value = line.getSampleValueBySeletedRegion( self.bgColor)
            # if value<0:continue
            print("value", value)

            y = int(line.x0 * self.slope + self.bias)
            self.__setSymbleDebug(img,y,line.x0,line.x1)
