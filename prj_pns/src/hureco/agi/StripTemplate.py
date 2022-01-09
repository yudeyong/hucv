import math
import numpy
from cv2 import imdecode, imread, line as cvline, imshow, waitKey, HoughLinesP, threshold as cvthreshold, THRESH_BINARY
from numpy import fromfile, uint8 as npuint8, pi as np_pi

from hureco import utils
from hureco.agi import StripRegion as sr

_DEBUG = not False
_DEBUG_DRAW_LOCATION = not False and _DEBUG
# tail line
# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
# RGB_GRAY = 0x10000
_DEBUG_HEADER = not False and _DEBUG
# None 不使用canny, 0, 5效果比较好
CANNY_GAUSS = 7

ZOOMOUT_FIRST = True

PRE_X_TIMES = 2
PRE_Y_TIMES = 2

X_TIMES = 1 if ZOOMOUT_FIRST else PRE_X_TIMES
Y_TIMES = 1 if ZOOMOUT_FIRST else PRE_Y_TIMES


class StripTemplate:

    def __init__(self, config):
        # self.name = jsonDic['name']
        self.references = []
        self.titles = []
        self.config = config

        posi = 0
        flag = False
        if hasattr(config, "references"):
            lines = config.references
        else:
            lines = config.lines
            self.lines = list(filter(lambda x: x[0] != 'blank', lines))
        fcHeader = 0
        for line in lines:
            if not flag:
                if line[0] != 'Functional Control':
                    fcHeader += line[1]
                    continue
                else:
                    flag = True
            if line[0] != 'blank':
                self.references.append([posi, posi + line[1]])
                self.titles.append(line[0])
            posi += line[1]
        unitStrip = self.config.STRIP_AREA_WIDTH / (self.references[2][0] - self.references[1][0])
        config.fcHeader = unitStrip * fcHeader
        for line in self.references:
            line[0] = line[0] * unitStrip
            line[1] = line[1] * unitStrip
        # self.references.append((posi, posi))

    def _checkShape(self, shape):
        return shape[0] < self.config.VALID_XY[3] and shape[0] > self.config.VALID_XY[2] \
               and shape[1] < self.config.VALID_XY[1] and shape[1] > self.config.VALID_XY[0]

    def getImg(self, file):
        src = imdecode(fromfile(file, dtype=npuint8), -1)
        if src is None: return "file not found " + file, None
        if not self._checkShape(src.shape):
            return "invalid size.", None
        self.src = src = numpy.flip(src)
        # 识别区域
        src = src[src.shape[0] - self.config.BOARD_AREA[1] - self.config.BOARD_AREA[3]:src.shape[0] -
                                                                                       self.config.BOARD_AREA[1],
              self.config.BOARD_AREA[0]:self.config.BOARD_AREA[0] + self.config.BOARD_AREA[2]]
        if ZOOMOUT_FIRST:
            src = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
        return None, src

    # 找最顶线,最左线
    @staticmethod
    def _filterLines(src, lines):
        '''

        :param src: _DEBUG only
        :param lines:
        :return:  h(slope, bias),v(slope,bias)
        '''
        v2ndBias = h2ndBias = vMinBias = hMinBias = 0x7fff
        vSlope = hSlope = 0.0
        v2ndSlope = hSlopeSetting = 0.05
        h2ndSlope = vSlopeSetting = 20
        # for l in lines:
        #     line = l[0]
        #     cvline(self.src, (line[[0]], line[1]), (line[2], line[3]), (0, 0, 0 ), 1)
        # imshow('canny', self.img)
        # waitKey()
        for line in lines:
            # line = l[0]
            # cvline(src, (line[[0]], line[1]), (line[2], line[3]), (255, 0, 255 ), 1)
            slope, bias = utils.getSlopeBias(line)
            if abs(slope) > vSlopeSetting:
                aBias = abs(bias)
                if aBias < abs(v2ndBias):
                    if aBias < abs(vMinBias):
                        v2ndBias = vMinBias
                        v2ndSlope = vSlope
                        vMinBias = bias
                        vSlope = slope
                    else:
                        v2ndBias = bias
                        v2ndSlope = slope
            elif abs(slope) < hSlopeSetting:
                aBias = abs(bias)
                if aBias < abs(h2ndBias):
                    if aBias < abs(hMinBias):
                        h2ndBias = hMinBias
                        h2ndSlope = hSlope
                        hMinBias = bias
                        hSlope = slope
                    else:
                        h2ndBias = bias
                        h2ndSlope = slope
        # utils.drawFullLine(self.src,(0,round(h2ndBias)), hSlope, h2ndBias, -3)
        # utils.drawFullLine(self.src,(0,round(v2ndBias)), vSlope, v2ndBias, -3)
        if abs(h2ndSlope - hSlope) < 0.02 and abs(h2ndBias - hMinBias) < 4:
            hSlope = (hSlope + h2ndSlope) / 2
            hMinBias = (hMinBias + h2ndBias) / 2
            # utils.drawFullLine(self.src,(0,round(hMinBias)), hSlope, hMinBias, 8)
        if (v2ndSlope == vSlope and abs(v2ndBias - vMinBias) < 4) or (
                abs(v2ndSlope - vSlope) < 0.051 and abs(v2ndBias - vMinBias) < 4 * abs(vSlope)):
            vSlope = (vSlope + v2ndSlope) / 2
            vMinBias = (vMinBias + v2ndBias) / 2
            # utils.drawFullLine(self.src,(0,round(vMinBias)), vSlope, vMinBias, 8)
        if _DEBUG_DRAW_LOCATION:
            utils.drawFullLine(src, 0, hSlope, hMinBias, -2)
            utils.drawFullLine(src, 0, vSlope, vMinBias, -2)
            # imshow('canny', src)
            # waitKey()
        return (hSlope, hMinBias), (vSlope, vMinBias)

    def _findTopLine(src, lines):
        '''

        :param src: _DEBUG only
        :param lines:
        :return:  h(slope, bias),v(slope,bias)
        '''
        h2ndBias = hMinBias = 0x7fff
        hSlope = 0.0
        hSlopeSetting = 0.05
        h2ndSlope = 20
        # for l in lines:
        #     line = l[0]
        #     cvline(self.src, (line[[0]], line[1]), (line[2], line[3]), (0, 0, 0 ), 1)
        # imshow('canny', self.src)
        # waitKey()
        for l in lines:
            line = l[0]
            # cvline(src, (line[[0]], line[1]), (line[2], line[3]), (255, 0, 255 ), 1)
            slope, bias = utils.getSlopeBias(line)
            if abs(slope) < hSlopeSetting:
                aBias = abs(bias)
                if aBias < abs(h2ndBias):
                    if aBias < abs(hMinBias):
                        h2ndBias = hMinBias
                        h2ndSlope = hSlope
                        hMinBias = bias
                        hSlope = slope
                    else:
                        h2ndBias = bias
                        h2ndSlope = slope
            # utils.drawFullLine(self.src,(0,round(h2ndBias)), hSlope, h2ndBias, -3)
            # utils.drawFullLine(self.src,(0,round(v2ndBias)), vSlope, v2ndBias, -3)
        if abs(h2ndSlope - hSlope) < 0.02 and abs(h2ndBias - hMinBias) <= 4:
            hSlope = (hSlope + h2ndSlope) / 2
            hMinBias = (hMinBias + h2ndBias) / 2
        if _DEBUG_DRAW_LOCATION:
            utils.drawFullLine(src, 0, hSlope, hMinBias, -2)
            # imshow('canny', src)
            # waitKey()
        # print("len:",len(lines))
        return (hSlope, hMinBias)

    LEFT_BOARD = 16  # 左侧线边界, 小于边界的忽略

    @staticmethod
    def _findLeftestLine(lines):
        # 找最左线
        min = 0x7ffff
        i = len(lines)
        left = 0
        while i > 0:
            i -= 1
            line = lines[i]
            # <10 太左边了, 忽略
            if line[0] < StripTemplate.LEFT_BOARD and abs(line[0] - line[2]) < 10 and line[0] + line[2] < min:
                min = line[0] + line[2]
                left = i
        return left

    @staticmethod
    def _removeDecline(lines):
        # 去掉斜率与最左侧线不一致的线,
        # 去掉太左边的线
        left = StripTemplate._findLeftestLine(lines)
        line = lines[left]
        krLeft = (line[0] - line[2]) / (line[1] - line[3])  # k的倒数
        i = len(lines)
        removeLines = []
        while i > 0:
            i -= 1
            line = lines[i]
            kr = (line[0] - line[2]) / (line[1] - line[3])
            if (abs((kr - krLeft) / (1 + kr * krLeft)) > 1 / 56) or line[0] < StripTemplate.LEFT_BOARD:
                removeLines.append(i)
        return numpy.delete(lines, removeLines, 0)

    @staticmethod
    def _mergeLines(lines):
        if lines.shape[0] == 1: return
        result = numpy.zeros(4)
        min = 0x7fff
        max = 0
        for line in lines:
            result[0] += line[0]
            result[2] += line[2]
            if min > line[3]: min = line[3]
            if max < line[1]: max = line[1]
        l = lines.shape[0]
        result[0] = round(result[0] / l)
        result[2] = round(result[2] / l)
        result[3] = min
        result[1] = max
        return result

    @staticmethod
    def _mergeClosedLines(lines, distance=8):
        l = lines[numpy.lexsort(lines[:, ::-1].T)]
        i = len(l) - 1
        last = l[i]
        lineGroup = [i]
        removeLines = []
        while i > 0:
            i -= 1
            line = l[i]
            flag = (i == 0)
            if last[0] - line[0] + last[2] - line[2] <= distance:
                lineGroup.append(i)
            else:
                flag = True
            if flag:
                last = StripTemplate._mergeLines(l[lineGroup])  # 临时用下last
                if not last is None:
                    l[lineGroup[0]] = last
                    removeLines.extend(lineGroup[1:])

                lineGroup = [i]
            last = line
        l = numpy.delete(l, removeLines, 0)
        return l

    # 返回fc line
    def _findLikelyLine(self, lines):
        line = lines[0]
        line[0] += self.config.FUNC_LINE[0]
        line[2] += self.config.FUNC_LINE[0]
        line[1] -= 1
        line[3] -= 1
        slope, bias = utils.getSlopeBias(line)
        self.vSlope = slope
        slope = -1 / slope  # 垂线斜率
        self.hSlope = slope
        line[0] += slope * self.config.FUNC_LINE[0]
        return line

    # 寻找最左顶点
    def _locateOrigin(self, img):
        src = self.img
        _, bw = cvthreshold(src, self.config.THRESHOLD, 255.0, THRESH_BINARY)
        # imshow('bw', bw)
        # waitKey()
        if _DEBUG_DRAW_LOCATION:
            debugBuf = img.copy()
        if CANNY_GAUSS > 0:
            bw = utils.toCanny(bw, CANNY_GAUSS)
        if _DEBUG_DRAW_LOCATION and not False:
            imshow('bw', bw)
            # waitKey()
        rho = 1
        threshold = 155
        minL = 600
        maxGap = 36
        # while True:
        lines = HoughLinesP(bw, rho, np_pi / 360, threshold, minLineLength=minL, maxLineGap=maxGap)
        if lines is None: return "miss lines. "
        lines = lines.reshape((lines.shape[0], lines.shape[2]))
        lines = StripTemplate._removeDecline(lines)
        lines = StripTemplate._mergeClosedLines(lines)
        lines = self._findLikelyLine(lines)  # lines [dims=1]
        if _DEBUG_DRAW_LOCATION and not False:
            utils.drawLines(debugBuf, (lines,))
            imshow('lines', debugBuf)
            # waitKey()
            # return False
        # if lines[0][1] < self.config.ORIGIN_Y[0] or lines[0][1] > self.config.ORIGIN_Y[1]:
        print(lines[1])
        if lines[1] < self.config.ORIGIN_Y[0] or lines[1] > self.config.ORIGIN_Y[1]:
            waitKey()
            return "miss point. "
        # h, v = StripTemplate._filterLines(self.img, lines)
        # if v[0] != 0:
        #     self.hkb = h
        #     self.vkb = v
        # else:
        self.origin = (lines[0], lines[1])  # utils.getCross(self.hkb, self.vkb)
        i = self.config.TOTAL
        x1 = lines[0] + 200
        x0 = lines[0] - 60
        y0 = 0.0+lines[1]
        y1 = 0.0 + lines[1] + 260* self.hSlope
        while i > 0:
            i -= 1
            utils.drawLines(debugBuf, ((x0, round(y0),x1,round( y1)),))
            y0 -= self.config.STRIP_INTERVAL
            y1 -= self.config.STRIP_INTERVAL
        utils.drawLines(debugBuf, ((x0, round(y0), x1, round(y1)),))
        imshow('lines', debugBuf)
        waitKey()

        return 'None'

    # 定位膜条区域
    def locateArea(self, src):
        self.img = utils.toGray(src, self.config.RGB_GRAY)
        r = self._locateOrigin(src)
        if not r is None: return r, None

        x = int(self.config.BOARD_AREA[0] + PRE_X_TIMES * self.origin[0])
        y = int(self.config.BOARD_AREA[1] + PRE_Y_TIMES * self.origin[1])
        src = self.src[y:y + self.config.STRIPS_AREA[3], x:x + self.config.STRIPS_AREA[2]]
        if _DEBUG_DRAW_LOCATION:
            i = 2 + self.config.TOTAL * self.config.STRIP_INTERVAL
            while (i >= 0):
                utils.drawDot(src, (8, round(i)), 5)
                i -= self.config.STRIP_INTERVAL
            # imshow('canny', src)
            # waitKey()
            self.gray = utils.toGray(src, 'r')
        # 更新膜条区域
        self.src = src
        return None, src

    def _checkHeaders(self):
        HEADER_WIDTH = 160

        src = self.src

        gray = utils.toGray(src, self.config.RGB_GRAY)
        if False:  # 缩一半,方便调试
            gray = utils.shrink(gray, 2, 2)
            self.config.STRIP_INTERVAL /= 2
            self.config.STRIP_WIDTH >>= 1
            HEADER_WIDTH >>= 1
            self.config.FUNC_LINE[0] >>= 1
            self.config.FUNC_LINE[1] >>= 1
            self.config.FUNC_LINE[2] >>= 1
            self.config.FUNC_LINE[3] >>= 1
        # imshow('1-gray', gray)
        # _, bw = cvthreshold(gray, self.config.THRESHOLD, 255.0, THRESH_BINARY)
        # height = self.hkb[0] * HEADER_WIDTH
        bottom = gray.shape[0]
        # dH = height if height>0 else 0
        i = 0
        strips = [None] * self.config.TOTAL
        flag = False

        y = 0  # +self.config.STRIP_INTERVAL*9
        while (y < bottom):
            # 便利查找header
            listP = utils.derivative(gray, (5, round(y + 3), HEADER_WIDTH, round(self.config.STRIP_INTERVAL + y - 3)),
                                     self.config.STRIP_INTERVAL)
            # if _DEBUG_HEADER:
            #     for line in listP:
            #         for p in line[2]:
            #             utils.drawDot(gray, (p[0],line[1]), 3)
            index, winSize = utils.maxWind(listP, 5, 10, 1)
            if index >= 0:
                flag = True

                fcX = sr.StripRegion.checkFunctionLineX(gray, y, self.config.FUNC_LINE, self.config.STRIP_WIDTH)
                if fcX >= 0:
                    # assert( fcX<self.config.FUNC_LINE[0] or fcX>self.config.FUNC_LINE[2])#找到func line
                    strips[i] = sr.StripRegion(listP, i, index, winSize, self.hkb[0], fcX, y, self.references,
                                               self.config)
                    strips[i].getHeaderMid(listP, index, winSize)
                    strips[i].getFunctionLineY(gray)
                    strips[i].recognise(gray)
                    # break
                    if False:
                        ty = strips[i].midY
                        tx = strips[i].midX[0]
                        cvline(gray, (tx, ty), (gray.shape[0], int((gray.shape[0] - tx) * self.hkb[0]) + ty), 128, 1)
                    # print("true ", end='')
                # for line in listP:
                #     print(",", line[0], end='')
                # print('.')
                # print("line:",i, winSize)
            y += self.config.STRIP_INTERVAL
            i += 1
            # print(i, '# # # # # #i.')

        if False:
            y = 0
            for strip in strips:
                if not strip is None:
                    utils.drawRectBy2P(gray, (strip.fcX, strip.fcY0), (strip.fcX + self.config.STRIP_WIDTH, strip.fcY1))
                y += self.config.STRIP_INTERVAL
        if _DEBUG_HEADER:
            imshow("bg", gray)
            waitKey()
        return (strips, gray) if flag else (None, None)

    # check header, locate
    def recognise(self):
        strips, img = self._checkHeaders()

        if strips is None: return None
        list = []
        for strip in strips:
            if not strip is None:
                list.append(strip.result)
        # for strip in strips:
        #     if not strip is None:
        #         strip.recognise()

        return list, img
