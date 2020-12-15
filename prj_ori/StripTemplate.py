import findHeaders
import utils
import cv2
import StripRegion

DEBUG = not False

#tail line
# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
# RGB_GRAY = 0x10000

ZOOMOUT_FIRST = not True

PRE_X_TIMES = 2
PRE_Y_TIMES = 2

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

    def findHeader(self, src):
        srcDetect = src
        if not ZOOMOUT_FIRST:
            srcDetect = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
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
