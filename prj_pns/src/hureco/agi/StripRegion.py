import cv2
import numpy

from hureco import SlidingWindow as sw, utils, result

_DEBUG_SR = False
_DEBUG_LINE = not False

_DEBUG_STRIP = not False and _DEBUG_SR
_DEBUG_DRAW_ALL = False and _DEBUG_SR

_FC_THRESHOLD = 200

_STAND = 40


class StripRegion:
    # function control
    # samplys
    SAMPLY_THRESHOLD = 239

    def __init__(self, index, slope, fcX, fcY, config):
        # 找中点
        # 整个模板的斜率
        self.setSlope = slope
        self.fcX = fcX
        self.fcY = fcY
        self.config = config
        self.index = index
        self.samples = []

    @staticmethod
    def validateFunctionLineX(src, x, y, STRIP_WIDTH):
        #x 位置优化
        OFFSETX = 2
        x += OFFSETX
        grey = src[y-STRIP_WIDTH:y+STRIP_WIDTH, x - STRIP_WIDTH:x]


        list0, result0, top0 = utils.derivative(grey, grey.shape[1] >> 1, 0, 1, 1)
        print(  result0, top0, x-OFFSETX, x-STRIP_WIDTH+result0+OFFSETX-1)
        return x-STRIP_WIDTH+result0+OFFSETX-1

    @staticmethod
    def checkFunctionLine(src, y, delta, STRIP_WIDTH, STRIP_INTERVAL, threshold=_FC_THRESHOLD):
        width = STRIP_WIDTH-(round(STRIP_WIDTH)>>4)
        y += (STRIP_WIDTH-width)/2
        y = round(y)
        y1 = y + round(STRIP_INTERVAL - ((STRIP_INTERVAL)//16))
        y += 1
        width = round(width)
        STRIP_WIDTH = round(STRIP_WIDTH)
        # cv2.imshow('canny1', src)

        # utils.drawRectBy2P(src, (testArea[0], y+testArea[1], testArea[2], y+testArea[3]))
        src = src[y:y1-1, delta:delta+(STRIP_WIDTH<<2)]
        # cv2.imshow('canny2', src)
        # cv2.waitKey()

        minValue = width * src.shape[0] * 255

        width >>= 1
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

        if minValue / (width * src.shape[0]) < threshold:
            # print(minValue / (width * src.shape[0]) )
            # print(numpy.median(src))
            # todo 缩小范围, 精确FCLine位置
            # 确定当前x区间
            src = src[:, x - width:x]
            buf = src[:,0]
            i = (numpy.average(buf)>=threshold)*1
            buf = src[:,-1]
            # cv2.imshow('canny3', src)
            # 剪裁x区间白边
            i1 = (numpy.average(buf)>=threshold)*1
            if i+i1>0: src = src[:,i:src.shape[1]-i1]
            if numpy.median(src)< threshold:
                list0, result0, top0 = utils.derivative(src, src.shape[0]>>1,1, -1, 1)
                list1, result1, top1 = utils.derivative(src, src.shape[0]>>1,1, 1, 1)
                i = result1 - result0
                # print(top0,top1,i,numpy.average(src[-1]),result0,result1)
                if (top0<300 or top1<300) and i<=20: #fc line 直到边界
                    if top1<300 : #下边界
                        #3倍中位数+1倍平均数 再平均
                        if (numpy.average(src[-1]) + numpy.median(src[-1])*3)*0.25 < 136:
                            if src.shape[0]-result0<30:
                                result1 = src.shape[0]-1
                                i = result1 - result0
                        else:
                            print("miss fc line border in y axis" )
                    # else: top0<300 todo
                    # src[ result0+(i>>1)-1: result0+(i>>1)+ 1, :] = 255
                    # cv2.imshow('canny3', src)
                    # cv2.waitKey()
                # else:
                src[ result0+(i>>1)-1: result0+(i>>1)+ 1, :] = 255
                # cv2.imshow('canny3', src)

                src[result0 + (i >> 1) - 1: result0 + (i >> 1) + 1, :] = 255
                # print(result0,result1, i)
                i = result0+((i+1)>>1)
                return x, y+i

        # print(numpy.median(src))
        # src[:,:]=0
        # cv2.imshow('canny3', src)
        # cv2.waitKey()
        return -1,0
        # print(minValue/(width*src.shape[0]))

    @staticmethod
    def _findSlope(src, x, y):
        '''
        通过膜条边缘获取膜条角度
        :param src:
        :param x:
        :param y:
        :return: 边缘斜率, 边缘截距(截距没用)
        '''
        src = src[y - 10:y + 13, x:x + 230]
        _, bw = cv2.threshold(src, 220, 255.0, cv2.THRESH_BINARY)
        # imshow('bw',bw)

        bw = utils.toCanny(bw, 3)
        lines = cv2.HoughLinesP(bw, 1, numpy.pi / 270, 100, minLineLength=160, maxLineGap=40)

        # imshow('canny', bw)
        # waitKey()
        if lines is None:
            # print(lines)
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
        maxBorder = ((i1 + i) >> 1)
        minBorder = maxBorder
        maxBorder += 3
        oldValue[0] = win.total
        recordCursor = 0
        while recordCursor < HEIGHT:
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
                # utils.drawRectBy2P(gray, (round(x0), int(t)), (round(x1), int(b)))
                # utils.drawDot(gray, (int((x0 + x1) / 2), int((y0 + y1 ) / 2)),  0)
            # else:

            value = StripRegion._calculateValue(gray[t + 1:b - 1, int(x0 + 1):int(x1 - 1)])
            self.result.appendValue(value, _STAND)
            utils.drawRectBy2P(gray, (round(x0), int(t)), (round(x1), int(b)))
            # utils.drawDot(gray, (int((x0 + x1) / 2), int((y0 + y1) / 2)), sx + 6)
            # print(",sx=",sx,x0,x1)
            i += 1

    @staticmethod
    def _narrowImg(src, width):
        w = src.shape[1]
        l = 0
        r = w - 1
        suml = numpy.sum(src[:, l])
        sumr = numpy.sum(src[:, r])
        while w > width:
            if suml <= sumr:
                r -= 1
                sumr = numpy.sum(src[:, r])
            else:
                l += 1
                suml = numpy.sum(src[:, l])
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
        data = numpy.sort(data)
        value = (count >> 3) + 1
        i1 = (count >> 1)
        i0 = i1 - value if i1 > value else 0

        value = numpy.average(data[i0:i1])
        # value += 0xff - bgColor

        # print("val:",value)
        return value

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
        data = numpy.delete(data, index)
        return data

    @staticmethod
    def _modeCheck(Ser1):
        c = numpy.bincount(Ser1)
        # 返回众数
        i = numpy.argmax(c)
        rule = (i - 2 > Ser1) | (i + 2 < Ser1)
        index = numpy.arange(Ser1.shape[0])[rule]
        return index

    # 定义3σ法则(实际使用的更严格的2σ,也许多次3σ更好,需要试)识别异常值函数
    @staticmethod
    def _two_sigma(Ser1):
        '''
        Ser1：表示传入DataFrame的某一列。
        '''
        rule = (Ser1.mean() - 2 * Ser1.std() > Ser1) | (Ser1.mean() + 2 * Ser1.std() < Ser1)
        index = numpy.arange(Ser1.shape[0])[rule]
        return index
