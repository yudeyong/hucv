import cv2
import numpy as np
import utils
import SampleLine as sl
import const
import SlidingWindow as sw
import StripTemplate as st
import math

DEBUG_SR = not False
DEBUG_LINE =  False

DEBUG_STRIP = not False



class StripRegion:
    BG_COLOR = False
    FIRST_LINE_WIDTH = 3
    FIRST_LINE_THRESHOLD = ((FIRST_LINE_WIDTH+1)>>2)*sl.SAMPLING_LINES*0xff

    def __init__(self, header, template):
        self.midHeader = utils.mid2PBy4P(header)

        self.slope,self.bias = utils.getSlopeBiasBy2P(self.midHeader[0],self.midHeader[1])
        self.cosReciprocal =  utils.getCosReciprocalBy2P(self.midHeader[0],self.midHeader[1])
        self.template = template
        self.samples = []
        self.valueAndPosi = []
        self.funcLine = None
        self.midFuncLine = None
        self.validPos = 0
        self.scale = 1.0

    @staticmethod
    def recognise(gray, regions):
        if DEBUG_STRIP:
            i = 0
        for region in regions:
            region.searchCutOff()
            if DEBUG_STRIP:
                region.drawFullLineDebug(gray)
                i += 1
                region.__drawAllDebug(gray)
                # if i != 2: continue

    def searchCutOff(self, gray):
        x = self.midHeader[0][0]+self.scale * self.template.references[2][0] - 2
        l = x + const.SAMPLING_MAX_WIDTH*st.X_TIMES
        while x<l:
            x = x+1


    def __drawAllDebug(self, gray):
        for p in self.template.references :
            x = self.midHeader[0][0]+self.scale * p[0]
            y = round(x * self.slope + self.bias)
            self.__setSymbleDebug(gray,round(x), round(self.midHeader[0][0]+self.scale*p[1]), y)

    def __setFuncLine(self, f):
        self.funcLine = f
        self.midFuncLine = utils.mid2PBy4P(f)
        self.scale = self.template.getScale( 0, 1, self.midFuncLine[1][0] - self.midHeader[0][0] + 1 )

        #assert(scale between 9.42, 8.8)
        # print(self.scale)

    def matchFuncLine(self, funcLines):
        i = len(funcLines)
        x = self.midFuncLine[0] if self.midFuncLine else 0x7fff
        while i > 0:
            i -= 1
            f = funcLines[i]
            if f[0][0] >= x: continue
            y = f[0][0] * self.slope + self.bias
            if y>f[0][1] and y<f[2][1]:
                self.__setFuncLine( f )
                del funcLines[i]
                return True
        return self.midFuncLine!=None

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

    def drawFullLineDebug(self, gray):
        if self.midFuncLine :
            k, b = utils.getSlopeBiasBy2P(self.midHeader[0], self.midFuncLine[1])
            utils.drawFullLine(gray, self.midHeader[0], k, b, 0)
            pass
        # self.getValuesByPostion(gray)

        return

    def __setSymbleDebug(self, gray, x1, x2, y):
        gray[y:y + 6, x1:x2+1] = 0
        gray[y + 2:y + 3, x1:x2+1] = 0xff

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

    def getValuesByPostion(self, img):
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
            if DEBUG_LINE:
                i += 1
                if (i>2 and i!=13 and i!=14) : pass#continue
                elif i>2:
                    i=i
            x = self.firstLine + p[0]*length -const.SAMPLING_WIDTH
            y = int(x*self.slope + self.bias)
            x = round(x)
            colorValue,offsetx = sl.SampleLine.getValue(img[y-const.SAMPLING_MINUS_Y_OFFSET:y+const.SAMPLING_Y_OFFSET,
                                x:x+(const.SAMPLING_WIDTH<<2) ], win)
            offsetx += x
            self.__setSymbleDebug(img,int(x), x+(const.SAMPLING_WIDTH<<2), y-12 )
            self.__setSymbleDebug(img,int(offsetx),int(offsetx+const.SAMPLING_WIDTH), y )
            colorValue = self.__removeBgColor(colorValue)
            self.valueAndPosi.append([colorValue, 0.0, 0,offsetx])

        if not DEBUG_LINE:
            if (len(self.valueAndPosi)<len(percent)):
                return -1
        print('************ new strip *************')
        self.__setProcessValue()
        cv2.imshow("bb", img)
        # cv2.waitKey()

    def __setProcessValue(self):
        cutOff = 0xff-self.valueAndPosi[1][0]
        if cutOff==0:
            return -2
        for v in self.valueAndPosi:
            v[1] = StripRegion.__funcValue((0xff-v[0]) / cutOff)
            v[2] = StripRegion.__setQualitative(v[1])
            if DEBUG_SR :
                print("{:.2f}".format(v[1]), ',', end='')
        if DEBUG_SR :
            print()
            for v in self.valueAndPosi:
                print(v[2], ',', end='')
            print()

    @staticmethod
    def __setQualitative(v):
        # v = math.sqrt(v)
        if False:
            if v<0.2 : return -2
            if v<0.8 : return -1
            if v<1.15 : return 0
            if v<2.5 : return 1
            if v<4 : return 2
            return 3
        else:
            if v<0.2 : return ''
            if v<0.8 : return '-'
            if v<1.15 : return 'o'
            if v<2.5 : return '+'
            if v<4 : return '++'
            return '+++'

    @staticmethod
    def __funcValue(v):
        return v
        return math.sqrt(v) if not DEBUG_LINE  else v
