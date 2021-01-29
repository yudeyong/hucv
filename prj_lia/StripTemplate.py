import math

import cv2
import numpy as np

import StripRegion as sr
import utils

DEBUG = not False
DEBUG_DRAW_LOCATION = not False and DEBUG
# tail line
# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
# RGB_GRAY = 0x10000
DEBUG_HEADER = not False and DEBUG
# None 不使用canny, 0, 5效果比较好
CANNY_GAUSS = 7

ZOOMOUT_FIRST = True

PRE_X_TIMES = 4
PRE_Y_TIMES = 4

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
        for line in config.lines:
            if not flag:
                if line[0] != 'Functional Control':
                    continue
                else:
                    flag = True
            if line[0] != 'blank':
                self.references.append([posi, posi + line[1]])
                self.titles.append(line[0])
            posi += line[1]
        unitStrip = self.config.STRIP_AREA_WIDTH / (self.references[2][0] - self.references[1][0])
        for line in self.references:
            line[0] = line[0] * unitStrip
            line[1] = line[1] * unitStrip
        # self.references.append((posi, posi))

    def _checkShape(self, shape):
        return shape[0] < self.config.VALID_XY[3] and shape[0] > self.config.VALID_XY[2] \
               and shape[1] < self.config.VALID_XY[1] and shape[1] > self.config.VALID_XY[0]

    def getImg(self, file):
        src = self.src = cv2.imread(file)
        if src is None: return None, "file not found " + file
        if not self._checkShape(src.shape):
            return None, "invalid size."
        src = src[self.config.BOARD_AREA[1]:self.config.BOARD_AREA[1] + self.config.BOARD_AREA[3],
              self.config.BOARD_AREA[0]:self.config.BOARD_AREA[0] + self.config.BOARD_AREA[2]]
        if ZOOMOUT_FIRST:
            src = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
        return src, None

    # 找最顶线,最左线
    @staticmethod
    def _filterLines(src, lines):
        '''

        :param src: debug only
        :param lines:
        :return:  h(slope, bias),v(slope,bias)
        '''
        v2ndBias = h2ndBias = vMinBias = hMinBias = 0x7fff
        vSlope = hSlope = 0.0
        v2ndSlope = hSlopeSetting = 0.05
        h2ndSlope = vSlopeSetting = 20
        # for l in lines:
        #     line = l[0]
        #     cv2.line(self.src, (line[[0]], line[1]), (line[2], line[3]), (0, 0, 0 ), 1)
        # cv2.imshow('canny', self.img)
        # cv2.waitKey()
        for l in lines:
            line = l[0]
            # cv2.line(src, (line[[0]], line[1]), (line[2], line[3]), (255, 0, 255 ), 1)
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
        if DEBUG_DRAW_LOCATION:
            utils.drawFullLine(src, 0, hSlope, hMinBias, -2)
            utils.drawFullLine(src, 0, vSlope, vMinBias, -2)
            # cv2.imshow('canny', src)
            # cv2.waitKey()
        return (hSlope, hMinBias), (vSlope, vMinBias)

    def _findTopLine(src, lines):
        '''

        :param src: debug only
        :param lines:
        :return:  h(slope, bias),v(slope,bias)
        '''
        h2ndBias = hMinBias = 0x7fff
        hSlope = 0.0
        hSlopeSetting = 0.05
        h2ndSlope = 20
        # for l in lines:
        #     line = l[0]
        #     cv2.line(self.src, (line[[0]], line[1]), (line[2], line[3]), (0, 0, 0 ), 1)
        # cv2.imshow('canny', self.src)
        # cv2.waitKey()
        for l in lines:
            line = l[0]
            # cv2.line(src, (line[[0]], line[1]), (line[2], line[3]), (255, 0, 255 ), 1)
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
        if DEBUG_DRAW_LOCATION:
            utils.drawFullLine(src, 0, hSlope, hMinBias, -2)
            # cv2.imshow('canny', src)
            # cv2.waitKey()
        # print("len:",len(lines))
        return (hSlope, hMinBias)

    # 映射到膜条区域左顶点
    def _mapOrigin(self):
        X_OFFSET = self.config.STRIPS_AREA[0]
        Y_OFFSET = self.config.STRIPS_AREA[1]
        x = self.origin[0]
        y = self.origin[1]
        if self.vkb[0] != float("inf"):
            tg = (self.vkb[0])
            sin = math.sqrt(abs(tg / (1 + tg)))
            tg = abs(self.hkb[0])
            cos = math.sqrt(1 / abs(1 + tg))
            deltaX = X_OFFSET * cos
            deltaY = Y_OFFSET * sin
        else:
            deltaX = X_OFFSET
            deltaY = Y_OFFSET
        self.origin = [x + deltaX, y + deltaY]

    # 寻找最左顶点
    def _locateOrigin(self):
        src = self.img
        _, bw = cv2.threshold(src, self.config.THRESHOLD, 255.0, cv2.THRESH_BINARY)
        # cv2.imshow('bw',bw)
        # cv2.waitKey()

        if CANNY_GAUSS > 0:
            bw = utils.toCanny(bw, CANNY_GAUSS)
        # cv2.imshow('bw',bw)
        # cv2.waitKey()
        lines = cv2.HoughLinesP(bw, 1, np.pi / 180, 116, minLineLength=120, maxLineGap=30)
        h, v = StripTemplate._filterLines(self.img, lines)
        if v[0] != 0:
            self.hkb = h
            self.vkb = v
        else:
            return False
        self.origin = utils.getCross(self.hkb, self.vkb)
        if self.origin is None:
            return False
        if DEBUG_DRAW_LOCATION: utils.drawDot(src, self.origin, 5)
        self._mapOrigin()
        x = int(self.origin[0])
        y = int(self.origin[1] - self.config.STRIP_DECTCT_BUF / PRE_Y_TIMES)
        bw = bw[y:y + int(self.config.STRIP_INTERVAL * 2 / PRE_Y_TIMES),
             x:x + int(self.config.STRIPS_AREA[2] / PRE_Y_TIMES)]
        lines = cv2.HoughLinesP(bw, 1, np.pi / 180, 58, minLineLength=73, maxLineGap=20)
        # cv2.imshow('bw1',bw)
        # cv2.waitKey()
        h = StripTemplate._findTopLine(self.img, lines)
        self.origin[1] = y + round(h[0] * self.origin[0] + h[1])
        if DEBUG_DRAW_LOCATION:
            utils.drawDot(src, self.origin, 15)
            # origin = self.origin
            # i = 20 * self.config.STRIP_INTERVAL
            # while (i>=0):
            #     utils.drawDot(src, (origin[0],origin[1]+round(i)), 5)
            #     i -= self.config.STRIP_INTERVAL

        if DEBUG_DRAW_LOCATION:
            # cv2.imshow('canny', src)
            # cv2.waitKey()
            pass
        return True

    # 定位膜条区域
    def locatArea(self, src):
        self.img = utils.toGray(src, self.config.RGB_GRAY)
        if not self._locateOrigin():
            return

        x = int(self.config.BOARD_AREA[0] + PRE_X_TIMES * self.origin[0])
        y = int(self.config.BOARD_AREA[1] + PRE_Y_TIMES * self.origin[1])
        src = self.src[y:y + self.config.STRIPS_AREA[3], x:x + self.config.STRIPS_AREA[2]]
        if DEBUG_DRAW_LOCATION:
            i = 2 + self.config.TOTAL * self.config.STRIP_INTERVAL
            while (i >= 0):
                utils.drawDot(src, (8, round(i)), 15)
                i -= self.config.STRIP_INTERVAL
            # cv2.imshow('canny', src)
            # cv2.waitKey()
            self.gray = utils.toGray(src, 'r')
        # 更新膜条区域
        self.src = src
        return src

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
        # cv2.imshow('1-gray', gray)
        # _, bw = cv2.threshold(gray, self.config.THRESHOLD, 255.0, cv2.THRESH_BINARY)
        height = self.hkb[0] * HEADER_WIDTH
        bottom = gray.shape[0]
        # dH = height if height>0 else 0
        i = 0
        strips = [None] * self.config.TOTAL
        flag = False

        y = 0  # +self.config.STRIP_INTERVAL*15
        while (y < bottom):
            # 便利查找header
            listP = utils.derivative(gray, (5, round(y + 3), HEADER_WIDTH, round(self.config.STRIP_INTERVAL + y - 3)),
                                     self.config.STRIP_INTERVAL)
            # if DEBUG_HEADER:
            #     for line in listP:
            #         for p in line[2]:
            #             utils.drawDot(gray, (p[0],line[1]), 3)
            index, winSize = utils.maxWind(listP, 5, 10, 1)
            if index >= 0:
                flag = True

                fcX = sr.StripRegion.checkFunctionLineX(gray, y, self.config.FUNC_LINE, self.config.STRIP_WIDTH)
                if fcX >= 0:
                    # assert( fcX<self.config.FUNC_LINE[0] or fcX>self.config.FUNC_LINE[2])#找到func line
                    strips[i] = sr.StripRegion(listP, index, winSize, self.hkb[0], fcX, y, self.references, self.config)
                    strips[i].getHeaderMid(listP, index, winSize)
                    strips[i].getFunctionLineY(gray)
                    strips[i].recognise(gray)
                    # break
                    if False:
                        ty = strips[i].midY
                        tx = strips[i].midX[0]
                        cv2.line(gray, (tx, ty), (gray.shape[0], int((gray.shape[0] - tx) * self.hkb[0]) + ty), 128, 1)

                # for line in listP:
                #     print(",", line[0], end='')
                # print('.')
                # print("line:",i, winSize)
            y += self.config.STRIP_INTERVAL
            i += 1
            print('# # # # # #i.', i)

        if False:
            y = 0
            for strip in strips:
                if not strip is None:
                    utils.drawRectBy2P(gray, (strip.fcX, strip.fcY0, strip.fcX + self.config.STRIP_WIDTH, strip.fcY1))
                y += self.config.STRIP_INTERVAL
        if DEBUG_HEADER:
            cv2.imshow("bg", gray)
            cv2.waitKey()
        return strips if flag else None

    # check header, locate
    def recognise(self):
        strips = self._checkHeaders()

        if strips is None: return None
        # for strip in strips:
        #     if not strip is None:
        #         strip.recognise()

        return strips
