import numpy as np

import findHeaders
import utils
import cv2
import StripRegion

DEBUG = not False

#tail line
# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
# RGB_GRAY = 0x10000

ZOOMOUT_FIRST = True

PRE_X_TIMES = 4
PRE_Y_TIMES = 4

X_TIMES = 1 if ZOOMOUT_FIRST else PRE_X_TIMES
Y_TIMES = 1 if ZOOMOUT_FIRST else PRE_Y_TIMES


class StripTemplate:


    def __init__(self, jsonDic):
        self.name = jsonDic['name']
        self.references = []
        self.titles = []
        self.RGB_GRAY = jsonDic['RGB_GRAY']
        self.THRESHOLD = jsonDic['THRESHOLD']
        self.VALID_XY = jsonDic['VALID_XY']
        self.BOARD_AREA = jsonDic["BOARD_AREA"]
        lines = jsonDic['lines']
        posi = 0
        for line in lines:
            if line[0]!='blank':
                self.references.append( (posi, posi+line[1]) )
                self.titles.append(line[0])
            posi += line[1]
        self.references.append((posi, posi))
        self.sampleRef = self.references[3:-1]
        self.persentage = [[0.0,0.0]] * len(self.references)
        self.titles.append("tail")
        findHeaders.headerFinder.setWH(X_TIMES,Y_TIMES)

    def __checkShape(self, shape):
        return shape[0] < self.VALID_XY[3] and shape[0] > self.VALID_XY[2] \
               and shape[1] < self.VALID_XY[1] and shape[1] > self.VALID_XY[0]

    def getImg(self, file):
        src = cv2.imread(file)
        if src is None: return None,"file not found " + file
        if not self.__checkShape(src.shape):
            return None,"invalid size."
        src = src[self.BOARD_AREA[1]:self.BOARD_AREA[1] + self.BOARD_AREA[3], self.BOARD_AREA[0]:self.BOARD_AREA[0] + self.BOARD_AREA[2]]
        if ZOOMOUT_FIRST:
            src = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
        return src, None

    def getScale(self, l1, l2, length):
        '''
        返回比例
        :param l1: 第一线坐标
        :param l2: 第二线坐标
        :param length: 实测距离
        :return: scale
        '''
        return length / (self.references[l2][1] - self.references[l1][0])

    # side offset 0:起点 1:终点
    def setPercentage(self, fromIndex, side):
        offset = self.references[fromIndex][side]
        length = self.references[len(self.references)-1][1] - offset
        # 先乘2, 循环时就可以少除1个2了
        # length <<= 1
        i = len(self.references)
        fromIndex += side
        while (i>fromIndex):
            i -= 1
            self.persentage[i] = ( (self.references[i][0]-offset)/length, (self.references[i][1]-offset)/length)
        # while i>0:
        #     i -= 1
        #     self.persentage[i] = (0.0,0.0)
        # return self.persentage
        return self.persentage[i:-1]

    def filterLines(self, lines):
        v2ndBias = h2ndBias = vMinBias = hMinBias = 0x7fff
        vSlope = hSlope = 0.0
        v2ndSlope = hSlopeSetting = 0.05
        h2ndSlope = vSlopeSetting = 20
        for l in lines:
            line = l[0]
            slope, bias = utils.getSlopeBias(line)
            if abs(slope)>vSlopeSetting:
                aBias = abs(bias)
                if aBias<abs(v2ndBias):
                    if aBias<abs(vMinBias):
                        v2ndBias = vMinBias
                        v2ndSlope = vSlope
                        vMinBias = bias
                        vSlope = slope
                    else:
                        v2ndBias = bias
                        v2ndSlope = slope
            elif abs(slope)<hSlopeSetting:
                aBias = abs(bias)
                if aBias<abs(h2ndBias):
                    if aBias<abs(hMinBias):
                        h2ndBias = hMinBias
                        h2ndSlope = hSlope
                        hMinBias = bias
                        hSlope = slope
                    else:
                        h2ndBias = bias
                        h2ndSlope = slope
        utils.drawFullLine(self.img,(0,round(hMinBias)), hSlope, hMinBias, -2)
        utils.drawFullLine(self.img,(0,round(h2ndBias)), hSlope, h2ndBias, -3)
        utils.drawFullLine(self.img,(0,round(vMinBias)), vSlope, vMinBias, -2)
        utils.drawFullLine(self.img,(0,round(v2ndBias)), vSlope, v2ndBias, -3)
        if abs(h2ndSlope-hSlope) < 0.02 and abs(h2ndBias-hMinBias)<4:
            hSlope = (hSlope+h2ndSlope)/2
            hMinBias = (hMinBias+h2ndBias)/2
            utils.drawFullLine(self.img,(0,round(hMinBias)), hSlope, hMinBias, 8)
        if (v2ndSlope==vSlope and abs(v2ndBias-vMinBias)<4) or (abs(v2ndSlope-vSlope) < 0.051 and abs(v2ndBias-vMinBias)<4*abs(vSlope)):
            vSlope = (vSlope+v2ndSlope)/2
            vMinBias = (vMinBias+v2ndBias)/2
            utils.drawFullLine(self.img,(0,round(vMinBias)), vSlope, vMinBias, 8)
        cv2.imshow('canny', self.img)
        cv2.waitKey()
        return (hSlope,hMinBias),(vSlope,vMinBias)

    def locateOrigin(self):
        src = self.img
        _, bw = cv2.threshold(src, self.THRESHOLD, 255.0, cv2.THRESH_BINARY)
        # __showDebug("bw",bw)

        # if findHeaders.CANNY_GAUSS:
        bw = utils.toCanny(bw, findHeaders.CANNY_GAUSS)
        lines = cv2.HoughLinesP(bw, 1, np.pi / 180, 160, minLineLength=200, maxLineGap=30)
        hkb,vkb = self.filterLines(lines)
        if False and not lines is None:
            color = 0
            for l in lines:
                line = l[0]
                if abs(line[0]-line[2])>abs(line[1]-line[3]): continue
                slope, bias = utils.getSlopeBias(line)
                # print(bias)
                color = 255 - color
                cv2.line(src, (line[[0]], line[1]), (line[2], line[3]), (255, color, 255-color), 1)
        cv2.imshow('canny', src)
        cv2.waitKey()

    def findHeader(self, src):
        self.img = src
        self.locateOrigin()
        return
        srcDetect = src
        # if not ZOOMOUT_FIRST:
        #     srcDetect = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
        header, funcLines = findHeaders.findHeader(srcDetect, self.RGB_GRAY, self.THRESHOLD)
        i = len(header)
        strips =[None]*i

        if not ZOOMOUT_FIRST:
            for h in funcLines:
                for p in h:
                    p[0] = p[0] * X_TIMES
                    p[1] = p[1] * Y_TIMES
        if DEBUG :
            for h in funcLines:
                if DEBUG:
                    # utils.drawRectBy4P(src, h)
                    # p = utils.mid2PBy4P(h)
                    # cv2.line(src, (p[0][0], p[0][1]), (p[1][0], p[1][1]), (0, 255, 0), 2)
                    pass
            # for header in stripHeads:
            #     utils.drawMidLineBy2P(src, header, -5)
            # for points in funcLines:
            #     utils.drawRectBy4P(src, points)
            # for points in stripPoints:
            #     utils.drawMidLineBy4P(src, points, -5)
            pass
        # cv2.imshow('header-src', src)

        for h in header:
            i -= 1
            if not ZOOMOUT_FIRST:
                for p in h:
                    p[0] = p[0]*X_TIMES
                    p[1] = p[1]*Y_TIMES
            if DEBUG :
                p = utils.mid2PBy4P(h)
                cv2.line(src, (p[0][0], p[0][1]), (p[1][0], p[1][1]), (0, 255, 0), 2)
                # utils.drawRectBy4P(srcDetect, h)

            strips[i] = StripRegion.StripRegion(h,self)
            strips[i].matchFuncLine(funcLines)
        src = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
        cv2.imshow('tmpl-src', src)
        print("head,fc:",len(header), len(funcLines))
        return strips
