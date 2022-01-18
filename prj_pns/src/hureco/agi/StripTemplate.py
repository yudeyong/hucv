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
    def _findLeftestPointLine(lines):
        # 找最左端点线
        min = 0x7ffff
        i = len(lines)
        left = 0
        while i > 0:
            i -= 1
            line = lines[i]
            # <10 太左边了, 忽略
            if line[2] < line[0]:
                p = line[2]
                line[2] = line[0]
                line[0] = p
            if line[0] < min:
                min = line[0]
                left = i
        return lines[left]

    @staticmethod
    def _removeVertical(lines):
        # 去掉竖线
        i = len(lines)
        removeLines = []
        while i > 0:
            i -= 1
            line = lines[i]
            horizontal = abs(line[0] - line[2])

            if (horizontal >> 2) < abs(line[1] - line[3]):
                removeLines.append(i)
        return numpy.delete(lines, removeLines, 0)

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
    def _mergeLines(lines, vertical=0):
        if lines.shape[0] == 1: return
        result = numpy.zeros(4)
        min = 0x7fff
        max = 0
        for line in lines:
            result[0+vertical] += line[0+vertical]
            result[2+vertical] += line[2+vertical]
            if min > line[3-vertical]: min = line[3-vertical]
            if min > line[1-vertical]: min = line[1-vertical]
            if max < line[1-vertical]: max = line[1-vertical]
            if max < line[3-vertical]: max = line[3-vertical]
        l = lines.shape[0]
        result[0+vertical] = round(result[0+vertical] / l)
        result[2+vertical] = round(result[2+vertical] / l)
        result[3-vertical] = min
        result[1-vertical] = max
        return result

    @staticmethod
    def _mergeClosedLines(lines, distance=8, vertical=0):
        l = lines[numpy.lexsort(lines[:, ::-1].T)] if vertical==0 else lines[numpy.lexsort(lines[:, :2].T)]
        i = len(l) - 1
        last = l[i]
        lineGroup = [i]
        removeLines = []
        while i > 0:
            i -= 1
            line = l[i]
            flag = (i == 0)
            if last[0+vertical] - line[0+vertical] + last[2+vertical] - line[2+vertical] <= distance:
                lineGroup.append(i)
            else:
                flag = True
            if flag:
                last = StripTemplate._mergeLines(l[lineGroup], vertical)  # 临时用下last
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
        # 固定间隔 FUNC_LINE[0]
        line[0] += self.config.FUNC_LINE[0]
        line[2] += self.config.FUNC_LINE[0]
        line[1] -= PRE_Y_TIMES
        line[3] -= PRE_Y_TIMES
        slope, bias = utils.getSlopeBias(line)
        self.vSlope = slope
        slope = -1 / slope  # 垂线斜率
        self.hSlope = slope
        line[0] += slope * self.config.FUNC_LINE[0]
        return line

    # 寻找最左顶点
    def _locateOrigin(self, colorImg):
        src = self.img
        _, bw = cvthreshold(src, self.config.THRESHOLD, 255.0, THRESH_BINARY)
        # imshow('bw', bw)
        # waitKey()
        if _DEBUG_DRAW_LOCATION:
            debugBuf = colorImg.copy()
        if CANNY_GAUSS > 0:
            bw = utils.toCanny(bw, CANNY_GAUSS)
        if False and _DEBUG_DRAW_LOCATION:
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
        if  False and _DEBUG_DRAW_LOCATION:
            utils.drawLines(debugBuf, (lines))
            imshow('lines', debugBuf)
            waitKey()
        lines = StripTemplate._mergeClosedLines(lines)
        lines = self._findLikelyLine(lines)  # lines [dims=1]
        print(lines)
        if False and _DEBUG_DRAW_LOCATION:
            utils.drawLines(debugBuf, (lines,))
            imshow('lines', debugBuf)
            waitKey()
            # return False
        # if lines[0][1] < self.config.ORIGIN_Y[0] or lines[0][1] > self.config.ORIGIN_Y[1]:

        self.origin = lines  # utils.getCross(self.hkb, self.vkb)
        if  False and _DEBUG_DRAW_LOCATION:  # 调试间距
            i = self.config.TOTAL
            x1 = lines[0] + 200
            x0 = lines[0] - 60
            y0 = 0.0 + lines[1]
            y1 = 0.0 + lines[1] + 260 * self.hSlope
            while i > 0:
                i -= 1
                utils.drawLines(debugBuf, ((x0, round(y0), x1, round(y1)),))
                y0 -= self.config.STRIP_INTERVAL
                y1 -= self.config.STRIP_INTERVAL
            utils.drawLines(debugBuf, ((x0, round(y0), x1, round(y1)),))
            imshow('lines', debugBuf)
            waitKey()

        return None

    countline = 0

    # 校验调整原点
    def _valideLocation(self):

        src = self.src[
              self.src.shape[0] - self.config.BOARD_AREA[1] - self.config.BOARD_AREA[3] + self.config.VALID_BOARD_AREA[
                  0]
              :self.src.shape[0] - self.config.BOARD_AREA[1] - self.config.BOARD_AREA[3] + self.config.VALID_BOARD_AREA[
                  1],
              self.config.BOARD_AREA[0] + self.origin[0] - self.config.FUNC_LINE[0]
              :self.config.BOARD_AREA[0] + self.origin[0] - self.config.FUNC_LINE[0] + self.config.VALID_BOARD_AREA[3]]
        _, bw = cvthreshold(src, self.config.THRESHOLD_VALID, 255.0, THRESH_BINARY)
        # imshow('bw', src)
        # waitKey()
        if _DEBUG_DRAW_LOCATION:
            debugBuf = src.copy()
        CANNY_GAUSS = 1
        if CANNY_GAUSS > 0:
            bw = utils.toCanny(bw, CANNY_GAUSS)
        if False and _DEBUG_DRAW_LOCATION:
            imshow('bw', bw)
            # waitKey()
        rho = 1
        threshold = 60
        minL = 75
        maxGap = 10
        # while True:
        lines = HoughLinesP(bw, rho, np_pi / 360, threshold, minLineLength=minL, maxLineGap=maxGap)
        if lines is None: return "miss lines. "
        lines = lines.reshape((lines.shape[0], lines.shape[2]))
        lines = StripTemplate._removeVertical(lines)
        print(len(lines))
        lines = StripTemplate._mergeClosedLines(lines, vertical=1)
        StripTemplate.countline += len(lines)
        # print(len(lines), StripTemplate.countline)
        lines = StripTemplate._findLeftestPointLine(lines)
        if not False and _DEBUG_DRAW_LOCATION:
            utils.drawLines(debugBuf, (lines,))
            imshow('lines', debugBuf)
            waitKey()
        # todo 校验最左边是否合理
        print(lines)
        return "debug"

    # 定位膜条区域
    def locateArea(self, src):
        self.img = utils.toGray(src, self.config.RGB_GRAY)
        r = self._locateOrigin(src)
        if not r is None: return r, None
        r = self._valideLocation()
        if not r is None: return r, None
        src = self.src
        x = int(self.config.BOARD_AREA[0] + PRE_X_TIMES * min(self.origin[0], self.origin[2]))
        y = int(src.shape[0] - self.config.BOARD_AREA[1] - self.config.BOARD_AREA[3] + PRE_Y_TIMES * self.origin[1])
        src = self.src[y - PRE_Y_TIMES * round(self.config.STRIP_INTERVAL + 0.5) * self.config.TOTAL:y,
              x:x + self.config.STRIPS_WIDTH]
        if False and _DEBUG_DRAW_LOCATION:
            # i = 2 + self.config.TOTAL * self.config.STRIP_INTERVAL
            # while (i >= 0):
            #     utils.drawDot(src, (8, round(i)), 5)
            #     i -= self.config.STRIP_INTERVAL
            self.gray = utils.toGray(src, 'r')
            img = utils.shrink(self.gray, PRE_X_TIMES, PRE_Y_TIMES)
            imshow('canny', img)
            waitKey()
            return "debg", None
        # 更新膜条区域
        self.src = src
        return None, src

    def _checkHeaders(self):
        HEADER_WIDTH = 160

        src = self.src

        gray = utils.toGray(src, self.config.RGB_GRAY)
        if not False:  # 缩一半,方便调试
            gray = utils.shrink(gray, PRE_X_TIMES, PRE_Y_TIMES)
            # self.config.STRIP_INTERVAL /= PRE_X_TIMES
            # self.config.STRIP_WIDTH >>= 1
            # HEADER_WIDTH >>= 1
            # self.config.FUNC_LINE[0] >>= 1
        imshow('1-gray', gray)
        # _, bw = cvthreshold(gray, self.config.THRESHOLD, 255.0, THRESH_BINARY)
        # height = self.hkb[0] * HEADER_WIDTH
        bottom = gray.shape[0]
        # dH = height if height>0 else 0
        i = 0
        strips = [None] * self.config.TOTAL
        flag = False

        top = bottom - self.config.TOTAL * self.config.STRIP_INTERVAL
        y = bottom  # +self.config.STRIP_INTERVAL*9
        while (y > top):
            y -= self.config.STRIP_INTERVAL
            imshow('1-strip', gray[round(y):round(bottom), :])
            waitKey()
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
            i += 1
            bottom -= self.config.STRIP_INTERVAL
            # print(i, '# # # # # #i.')

        if False:
            y = 0
            for strip in strips:
                if not strip is None:
                    utils.drawRectBy2P(gray, (strip.fcX, strip.fcY0), (strip.fcX + self.config.STRIP_WIDTH, strip.fcY1))
                y += self.config.STRIP_INTERVAL
        if _DEBUG_HEADER and False:
            imshow("bg", gray)
            waitKey()
        return (strips, gray) if flag else (None, None)

    # check header, locate
    def recognise(self):
        strips, img = self._checkHeaders()

        if strips is None: return None, None
        list = []
        for strip in strips:
            if not strip is None:
                list.append(strip.result)
        # for strip in strips:
        #     if not strip is None:
        #         strip.recognise()

        return list, img
