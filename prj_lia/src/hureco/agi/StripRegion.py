from cv2 import HoughLinesP, threshold as cvthreshold, THRESH_BINARY, imshow, waitKey
from numpy import pi as np_pi, sum as np_sum, sort as np_sort, \
    average as np_average, array as np_array, delete as np_delete, bincount as np_bincount, \
    argmax as np_argmax, arange as np_arange

from hureco import SlidingWindow as sw, utils, result

_DEBUG_SR = False
_DEBUG_LINE = not False

_DEBUG_STRIP = not False and _DEBUG_SR
_DEBUG_DRAW_ALL = False and _DEBUG_SR

_FC_THRESHOLD = 211

_STAND = 40


class StripRegion:
    # function control
    # samplys
    SAMPLY_THRESHOLD = 239

    @staticmethod
    def _locateIndex(listP, index):
        """
        @deprecated
        定位 index
        :param listP:
        :param index:
        :return:  -1 not found, >0 index
        """
        l = index-1
        r = index+1
        length = len(listP)
        last = -2
        while l>=0 and r<length :
            if l >= length - r:
                if len(listP[l][2])>0:
                    if last == l + 1:
                        return l
                    last = l
                l -= 1
            else:
                if len(listP[r][2])>0:
                    if last + 1 == r:
                        return last
                    last = r
                r += 1
        return -1

    def __init__(self, listP, i, index, size, slope, fcX, y, lines, config):
        # 找中点
        index = index + (size >> 1)
        if len(listP[index][2]) == 0:
            # index = StripRegion._locateIndex(listP, index)
            # if index<0:
            return
        if size & 1 == 0:
            # 下标大的
            self.midX = listP[index][2][0] if listP[index][1] >= listP[index + 1][1] else listP[index + 1][2][0]
            # 均值
            self.midY = (listP[index][1] + listP[index + 1][1]) >> 1
        else:
            self.midX = listP[index][2][0]
            self.midY = listP[index][1]
        # 整个模板的斜率
        self.setSlope = slope
        self.fcX = fcX
        self.refX = fcX
        self.top = fcX * slope + y
        self.config = config
        self.lines = lines
        self.samples = []
        self.result = result.Result(i)
        x0 = round(self.fcX - config.fcHeader) - 150
        if x0 < 0: x0 = 0
        x1 = round(self.fcX + lines[-1][1]) + 110
        if x1 >= config.STRIPS_AREA[2]:
            x1 = config.STRIPS_AREA[2] - 1
        self.result.area = (x0, x1, round(y + 6), round(y + config.STRIP_INTERVAL))

    @staticmethod
    def checkFunctionLineX(src, y, testArea, STRIP_WIDTH, threshold=_FC_THRESHOLD):
        y = int(y)
        width = STRIP_WIDTH - ((STRIP_WIDTH+6) >> 2)
        #src1 = src
        #utils.drawRectBy2P(src, (testArea[0], y+testArea[1]), (testArea[2], y+testArea[3]))
        src = src[y + testArea[1]:y + testArea[3], testArea[0]:testArea[2]]

        minValue = width * src.shape[0] * 255
        win = sw.SlidingWindow(width)

        win.initData(src, True)
        i = width
        x = i
        i1 = src.shape[1]
        while True:
            if minValue > win.total:
                minValue = win.total
                x = i
            if i >= i1: break;
            win.append(src[:, i])
            i += 1
        if _DEBUG_STRIP:
            # utils.drawRectBy2P(src, (x + testArea[0] - width - 1, y + testArea[1]+3), (x+ testArea[0] , y + testArea[3]-3))
            # waitKey()
            pass
        # print(round(minValue / (width * src.shape[0]),1) ," <? ",threshold)
        if minValue / (width * src.shape[0]) < threshold:
            return x + testArea[0] - width - 1
        else:
            return -1
        # print(minValue/(width*src.shape[0]))
        return x

    def getFunctionLineY(self, src):

        # 开始处理Y
        # 检测窗口高度
        HEIGHT = 9
        marginTop = int(self.top) - HEIGHT
        if marginTop < 0: marginTop = 0

        marginBottom = int(self.top + self.config.STRIP_INTERVAL) + HEIGHT
        if marginBottom >= src.shape[0]: marginBottom = src.shape[0]

        # data[:,:] = 0
        right = self.fcX + self.config.STRIP_WIDTH - 3
        # draw 监测区域
        if _DEBUG_STRIP:
            # utils.drawRectBy2P(src,(self.fcX + 2, marginTop), (right+1, marginBottom))
            # imshow("fc", src)
            # waitKey()
            pass
        y0, y1 = StripRegion._getSampleY(src, (self.fcX + 3, marginTop, right, marginBottom), HEIGHT)
        if True:
            self.fcY1 = y1
            self.fcY0 = y0
            self.refHeight = (self.fcY1 - self.fcY0)
            self.refY = self.fcY0
        else:
            self.fcY0 = marginTop
            self.fcY1 = y + FUNC_LINE[3] + HEIGHT
        # src[self.fcY0:self.fcY1, self.fcX:self.fcX+STRIP_WIDTH]=0

        self.points[1] = (self.fcX, (y1 + y0) / 2)
        # 膜条的斜率
        self.slope, b = utils.getFitLine(self.points)

        self.sideSlope, _ = StripRegion._findSlope(src, right, self.fcY0)
        if not self.sideSlope is None:
            # utils.drawFullLine(src, 0, self.sideSlope, self.fcY0 + b, -16)
            # print("set slope",self.sideSlope,self.setSlope)
            self.slope = (self.sideSlope + self.setSlope * 3) / 4
        if _DEBUG_STRIP:
            # 画趋势线
            utils.drawFullLine(src, 0, self.slope, b, -16)
            waitKey()
        return

    @staticmethod
    def _findSlope(src, x, y):
        '''
        通过膜条边缘获取膜条角度
        :param src:
        :param x:
        :param y:
        :return: 边缘斜率, 边缘截距(截距没用)
        '''
        if y<10 :
            y=10;
        src = src[y - 10:y + 13, x:x + 230]
        _, bw = cvthreshold(src, 220, 255.0, THRESH_BINARY)
        # imshow('bw',bw)
        # waitKey

        bw = utils.toCanny(bw, 3)
        lines = HoughLinesP(bw, 1, np_pi / 270, 100, minLineLength=160, maxLineGap=40)

        # imshow('canny', bw)
        # waitKey()
        if lines is None:
            #print('line is none')
            return None, None
        x0 = x1 = y0 = y1 = 0
        for l in lines:
            line = l[0]
            x0 += line[0]
            x1 += line[2]
            y0 += line[1]
            y1 += line[3]
        slope, b = utils.getSlopeBias((x0, y0, x1, y1))
        return slope, b

    @staticmethod
    def _getSampleY(src, rect, HEIGHT):
        '''

        :param data: srcImg
        :param rect: dectect area
        :param HEIGHT: window size
        :return:
        '''

        data = src[rect[1]:rect[3], rect[0]:rect[2]]
        # assert data.shape[0]>HEIGHT
        win = sw.SlidingWindow(HEIGHT)

        win.initData(data, False)

        i1 = data.shape[0]
        oldValue = [0] * HEIGHT
        minValue = maxValue = 0
        minY = maxY = i = HEIGHT - 1
        maxBorder = ((i1 + i) >> 1)+3
        minBorder = maxBorder+3*2
        maxBorder += 3
        oldValue[0] = win.total
        recordCursor = 0
        while recordCursor < HEIGHT:
            #init win
            oldValue[recordCursor] = win.total
            recordCursor += 1
            i += 1
            win.append(data[i])
        recordCursor = 0
        while True:
            delta = win.total - oldValue[recordCursor]
            if i < minBorder and minValue > delta:
                minValue = delta
                minY = i
            if i > maxBorder and maxValue < delta:
                maxValue = delta
                maxY = i
            i += 1
            if i >= i1: break;
            oldValue[recordCursor] = win.total
            recordCursor += 1
            if recordCursor >= HEIGHT:
                recordCursor = 0
            win.append(data[i])
        return minY + rect[1] - HEIGHT, maxY + rect[1] - HEIGHT

    @staticmethod
    def _getMidHalfByPW(l, w, minWidth):
        '''
        根据点, 宽度得到缩小的中心范围
        :param l:
        :param w:
        :param minWidth:
        :return:
        '''
        delta = w * 0.75
        # 最小宽度
        if delta < minWidth: delta = minWidth

        # assert w>delta
        # margin
        w = (w - delta) / 2
        l += w
        return l, l + delta

    @staticmethod
    def _getMidHalfBy2P(l, r, minWidth):
        return StripRegion._getMidHalfByPW(l, r - l, minWidth)

    def recognise(self, gray):
        i = 0
        STRIP_WIDTH = self.config.STRIP_WIDTH
        HALF_WIDTH = STRIP_WIDTH / 2
        # 收窄边界
        baseY0, baseY1 = StripRegion._getMidHalfByPW(self.refY, self.refHeight, 8)
        for line in self.lines:
            # if i<10 :
            #     i += 1
            #     continue
            x0, x1 = StripRegion._getMidHalfBy2P(self.fcX + line[0], self.fcX + line[1], 5)
            # print("L01",line[0],line[1],"x0,1=",x0,x1, end='')
            slope = self.slope
            deltaY = (x0 - self.refX) * slope * 2
            y0 = int(round(baseY0 + deltaY))
            y1 = int(round(baseY1 + deltaY))
            value = StripRegion._calculateValue(gray[y0:y1, int(x0):int(x1)])
            sx = -3
            if value < StripRegion.SAMPLY_THRESHOLD:
                if _DEBUG_STRIP:
                    # print("##", i, value)
                    pass
                l = int(x0 - HALF_WIDTH)
                t = int(y0 - STRIP_WIDTH)
                if t < 0: t = 0
                r = int(x1 + HALF_WIDTH)
                b = int(y1 + STRIP_WIDTH)
                sx = StripRegion.checkFunctionLineX(gray, 0,
                                                    (l, t, r, b)
                                                    , STRIP_WIDTH - 4, StripRegion.SAMPLY_THRESHOLD)
                # t = y0
                # b = y1
                # if self.sideSlope is None:
                #     # if sx>0:
                #     #     t, b = StripRegion._getSampleY(gray, (l,t,r,b), 8)
                #     #     height = b-t-self.config.STRIP_HEIGHT
                #     #     if height>=-5 and height<=6:
                #     #         pass#todo 暂时不用校正, 后续如果需要, 首先可以优化header中点精度, 再不行再在这里优化
                #     #         # print("h:", height)
                #     #         t = y0
                #     #         b = y1
                #     #     else:
                #     #         t = y0
                #     #         b = y1
                #     # else:
            t = y0
            b = y1
            if sx > 0:
                if sx < x0:
                    x0 = sx
                    x0 += StripRegion._narrowImg(gray[t:b, int(x0):int(x1)], STRIP_WIDTH - 4)
                    x1 = x0 + STRIP_WIDTH - 4
                if _DEBUG_STRIP:
                    # utils.drawRectBy2P(gray, (round(x0), int(t)), (round(x1), int(b)))
                    # utils.drawDot(gray, (int((x0 + x1) / 2), int((y0 + y1 ) / 2)),  0)
                    # imshow("stripRegion", gray)
                    # waitKey(10)
                    pass
            # else:

            value = StripRegion._calculateValue(gray[t + 1:b - 1, int(x0 + 1):int(x1 - 1)])
            self.result.appendValue(value, _STAND)
            if _DEBUG_STRIP:
                utils.drawRectBy2P(gray, (round(x0), int(t)), (round(x1), int(b)))
            # utils.drawDot(gray, (int((x0 + x1) / 2), int((y0 + y1) / 2)), sx + 6)
            # print(",sx=",sx,x0,x1)
            i += 1

    @staticmethod
    def _narrowImg(src, width):
        w = src.shape[1]
        l = 0
        r = w - 1
        suml = np_sum(src[:, l])
        sumr = np_sum(src[:, r])
        while w > width:
            if suml <= sumr:
                r -= 1
                sumr = np_sum(src[:, r])
            else:
                l += 1
                suml = np_sum(src[:, l])
            w -= 1
        return l

    @staticmethod
    def _calculateValue(data):
        '''
        取排名75%-87.5%的像素区间求均值
        :param data:
        :return:
        '''
        data = data.flatten()

        # s = data.size
        # print( "dsize=",s, "-",end='')
        i = 3
        while data.size > 80 and i > 0:
            data = StripRegion._filteringAnomaly(data, StripRegion._two_sigma)
            i -= 1
        count = data.size
        # print(count, '=', s-count,round((s-count)*100/s),"%")
        data = np_sort(data)
        value = (count >> 3) + 1
        i1 = (count >> 1)
        i0 = i1 - value if i1 > value else 0

        value = np_average(data[i0:i1])
        # value += 0xff - bgColor

        # print("val:",value)
        return value

    def getHeaderMid(self, listP, offset, size):
        list = [0] * size
        for i in range(0, size):
            list[i] = listP[i + offset][2][0][0]

        midy = (listP[size - 1 + offset][1] + listP[offset][1]) >> 1
        src = np_array(list)
        left = StripRegion._filteringAnomaly(src, StripRegion._modeCheck)

        src = StripRegion._filteringAnomaly(left, StripRegion._two_sigma)
        midx = np_average(src)
        self.points = [()] * 2
        self.points[0] = (midx, midy)

    @staticmethod
    def _filteringAnomaly(data, func):
        '''
        过滤噪点, 异常值
        :param data:
        :param list:
        :return:
        '''
        if data.max() - data.min() <= 2: return data
        index = func(data)
        data = np_delete(data, index)
        return data

    @staticmethod
    def _modeCheck(Ser1):
        c = np_bincount(Ser1)
        # 返回众数
        i = np_argmax(c)
        rule = (i - 2 > Ser1) | (i + 2 < Ser1)
        index = np_arange(Ser1.shape[0])[rule]
        return index

    # 定义3σ法则(实际使用的更严格的2σ,也许多次3σ更好,需要试)识别异常值函数
    @staticmethod
    def _two_sigma(Ser1):
        '''
        Ser1：表示传入DataFrame的某一列。
        '''
        rule = (Ser1.mean() - 2 * Ser1.std() > Ser1) | (Ser1.mean() + 2 * Ser1.std() < Ser1)
        index = np_arange(Ser1.shape[0])[rule]
        return index
