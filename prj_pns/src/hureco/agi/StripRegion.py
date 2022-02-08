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
        self.slope = slope
        self.fcX = fcX
        self.fcY = fcY
        self.config = config
        self.index = index
        self.samples = []

    @staticmethod
    def validateFunctionLineX(src, x, y, STRIP_WIDTH):
        # x 位置优化
        OFFSETX = 2
        x += OFFSETX
        grey = src[y - STRIP_WIDTH:y + STRIP_WIDTH, x - STRIP_WIDTH:x]

        list0, result0, top0 = utils.derivative(grey, grey.shape[1] >> 1, 0, 1, 1)
        # print(  result0, top0, x-OFFSETX, x-STRIP_WIDTH+result0+OFFSETX-1)
        return x - STRIP_WIDTH + result0 + OFFSETX - 1

    @staticmethod
    def checkFunctionLine(src, y, delta, STRIP_WIDTH, STRIP_INTERVAL, threshold=_FC_THRESHOLD):
        width = STRIP_WIDTH - (round(STRIP_WIDTH) >> 4)
        y += (STRIP_WIDTH - width) / 2
        y = round(y)
        y1 = y + round(STRIP_INTERVAL - ((STRIP_INTERVAL) // 16))
        y += 1
        width = round(width)
        STRIP_WIDTH = round(STRIP_WIDTH)
        # cv2.imshow('canny1', src)

        # utils.drawRectBy2P(src, (testArea[0], y+testArea[1], testArea[2], y+testArea[3]))
        src = src[y:y1 - 1, delta:delta + (STRIP_WIDTH << 2)]
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
            buf = src[:, 0]
            i = (numpy.average(buf) >= threshold) * 1
            buf = src[:, -1]
            # cv2.imshow('canny3', src)
            # 剪裁x区间白边
            i1 = (numpy.average(buf) >= threshold) * 1
            if i + i1 > 0: src = src[:, i:src.shape[1] - i1]
            if numpy.median(src) < threshold:
                list0, result0, top0 = utils.derivative(src, src.shape[0] >> 1, 1, -1, 1)
                list1, result1, top1 = utils.derivative(src, src.shape[0] >> 1, 1, 1, 1)
                i = result1 - result0
                # print(top0,top1,i,numpy.average(src[-1]),result0,result1)
                if (top0 < 300 or top1 < 300) and i <= 20:  # fc line 直到边界
                    if top1 < 300:  # 下边界
                        # 3倍中位数+1倍平均数 再平均
                        if (numpy.average(src[-1]) + numpy.median(src[-1]) * 3) * 0.25 < 136:
                            if src.shape[0] - result0 < 30:
                                result1 = src.shape[0] - 1
                                i = result1 - result0
                        else:
                            print("miss fc line border in y axis")
                    # else: top0<300 todo
                    # src[ result0+(i>>1)-1: result0+(i>>1)+ 1, :] = 255
                    # cv2.imshow('canny3', src)
                    # cv2.waitKey()
                # else:
                src[result0 + (i >> 1) - 1: result0 + (i >> 1) + 1, :] = 255
                # cv2.imshow('canny3', src)

                src[result0 + (i >> 1) - 1: result0 + (i >> 1) + 1, :] = 255
                # print(result0,result1, i)
                i = result0 + ((i + 1) >> 1)
                return x, y + i

        # print(numpy.median(src))
        # src[:,:]=0
        # cv2.imshow('canny3', src)
        # cv2.waitKey()
        return -1, 0
        # print(minValue/(width*src.shape[0]))

    skip = 5

    def recognise(self, src):
        StripRegion.skip -= 1
        if StripRegion.skip > 0: return
        i = 0
        STRIP_HEIGHT = self.config.STRIP_HEIGHT
        debug_y = self.fcY
        x = self.fcX
        x1 = round(self.config.lines[2][1]//4)
        backgroud = StripRegion._calculateValue(src[debug_y-2:debug_y+2, x+x1:x+3*x1],True)
        self.result = []
        j = 2
        # print('b', backgroud)
        while j < len(self.config.lines) - 1:
            x1 = self.config.lines[j][1]
            x += x1
            j += 1
            x2 = self.config.lines[j][1]
            debug_y += (x2 + x1) * self.slope
            x1 = x + x2
            left = round(x) - 4
            right = round(x) + 10
            top = round(debug_y) - 9
            bottom = round(debug_y) + 9
            grey = src[top: bottom, left: right]
            list0, result0, top0 = utils.derivative(grey, 2+grey.shape[1] >> 1, 0, -1, 1)
            list1, result1, top1 = utils.derivative(grey, -2+grey.shape[1] >> 1, 0, 1, 1)
            median = int(255 - numpy.median(grey))
            # print(result0, top0, result1, top1, median)

            # utils.drawDot(src, (x + 6, debug_y), 3)
            # utils.drawRectBy2P(src, (left, top), (right, bottom)) # 此处画框 影响判读值
            if not ((top0 > 200 and top0 > (median << 2)) or (top0 > 120 and top0 > (median << 3))):
                result0 = 0
            delta_right = left + result1 - right
            if not ((top1 > 200 and top1 > (median << 2)) or (top1 > 120 and top1 > (median << 3))):
                delta_right = 0
            if result0 * delta_right != 0 and result1 - result0 < 6:  # 左右调整都不为0 且距离过近, 提高约束条件
                if top0 < top1:
                    if (top0 < 300 or top0 < (median << 3)):
                        result0 = 0
                else:
                    if (top1 < 300 or top1 < (median << 3)):
                        delta_right = 0

            left += result0
            right += delta_right
            while right-left>8:
                right -= 1
                left += 1
            top += 2
            bottom -= 2
            value = StripRegion._calculateValue(src[top:bottom, left:right])
            value = value-backgroud if value>=backgroud else 0

            # print('v', round(value,2), round(value/38,2))
            if not False or _DEBUG_STRIP:
                utils.drawRectBy2P(src, (left, top), (right, bottom))
                cv2.imshow('1-strip', src[round(self.fcY - STRIP_HEIGHT // 2):round(self.fcY + STRIP_HEIGHT // 2), :])
            # gray[round(y):round(bottom), :])

                # cv2.waitKey()
            x = x1
            j += 1
            self.result.append((left, top, right, bottom, i, value))
            i += 1
        return

    @staticmethod
    def _calculateValue(data, order=False):
        '''
        取排名50%-62.5%的像素区间求均值
        :param data:
        :param order: false 偏黑区, true 偏白区
        :return:
        '''
        data = data.flatten()

        # s = data.size
        # print( "dsize=",s, "-",end='')
        i = 3
        while data.size > 80 and i > 0:
            data = StripRegion._filteringAnomaly(data, StripRegion.
                                                 _two_sigma)
            i -= 1
        count = data.size
        # print(count, '=', s-count,round((s-count)*100/s),"%")
        if order : data = 255-data
        data = numpy.sort(data)
        value = (count >> 3) + 1
        i1 = (count >> 1)
        i0 = i1 - value if i1 > value else 0

        value = numpy.average(data[i0:i1])
        if not order: value = 255 - value

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
