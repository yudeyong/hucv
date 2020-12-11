import cv2
import numpy as np

import SampleLine as sl
import const
import utils

DEBUG_HEADER = not False
BOARD_DETECT_WIDTH= 130

#None 不使用canny, 0, 5效果比较好
CANNY_GAUSS = 5

#
HEADER_LEFT = 26
HEADER_RIGHT = 48
MIN_FUNC_LINE = HEADER_RIGHT
MAX_FUNC_LINE = MIN_FUNC_LINE+(const.SAMPLING_WIDTH<<5)

def __checkRectRange(points):
    if points.shape[0] <= 3: return None,None
    pp = points[:,0,:]
    minX, minY = 0x7fff, 0x7fff
    maxX, maxY = 0, 0
    mostLT = 0x7fff
    mostRT = -10000
    mostLB = 0x7fff
    mostRB = -10000
    pLB = [[0,0]]*4
    for p in pp:
        if p[0] > maxX: maxX = p[0]
        if p[0] < minX: minX = p[0]
        if p[1] > maxY: maxY = p[1]
        if p[1] < minY: minY = p[1]
        v = p[0]+p[1]
        if v < mostLT:
            pLB[0] = p
            mostLT = v
        if v > mostRB:
            pLB[3] = p
            mostRB = v
        v = p[0]-p[1]
        if v > mostRT:
            pLB[1] = p
            mostRT = v
        if v < mostLB:
            pLB[2] = p
            mostLB = v
    deltaX = (maxX - minX)
    deltaY = (maxY - minY)

    return (deltaX,deltaY), pLB

def __checkHeader(point, x):
    deltaX, deltaY = point
    # print(deltaX, deltaY, len(points))
    if deltaX < const.STRIP_WIDTH - (const.STRIP_WIDTH >> 3): return None
    if deltaX > const.STRIP_WIDTH << 3: return None
    if deltaY <= const.STRIP_HALF_HEIGHT: return None
    if deltaY > const.STRIP_HEIGHT << 1: return None

    if x<HEADER_LEFT : return None
    if x>HEADER_RIGHT : return None
    # print("yes")
    return True

def __checkFuncLine(point, x):
    if not sl.SampleLine.isLineSize(point): return None
    if x<MIN_FUNC_LINE : return None
    if x>MAX_FUNC_LINE : return None
    # print("yes")
    return True

def __showDebug(name,img):
    a = utils.shrink(img, 2, 2)
    cv2.imshow(name, a)
    cv2.waitKey()


def findHeader(src, RGB_GRAY, THRESHOLD):
    srcDetect = src[:, :BOARD_DETECT_WIDTH]

    gray = utils.toGray(srcDetect, RGB_GRAY)
    # cv2.imshow('1-gray', gray)
    _, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)
    # __showDebug("bw",bw)

    if CANNY_GAUSS:
        bw = utils.toCanny(bw,CANNY_GAUSS)
    # __showDebug("canny",bw)
    # exit(0)

    if DEBUG_HEADER:
        # __showDebug("header-bw", bw)
        # cv2.imshow("header-bw", bw)
        pass
    # bw = utils.toCanny(bw, 0)
    # if DEBUG_HEADER:
    #     cv2.imshow("header-canny", bw)
    contours, hierarchy = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    i = len(contours)
    # stripHeads = []
    stripPoints = []
    funcLines = []
    oldp = None
    pCount = 0
    fcCount = 0
    while i > 0:
        i -= 1
        cnt = contours[i]
        if cnt[0][0][1]<110 \
                and cnt[0][0][1]>80 :
            # todo : 上面条件debug only
            #header \
            delta, points = __checkRectRange(cnt)
            # approx = cnt  # cv2.approxPolyDP(cnt, 0.02*cv2.arcLength(cnt,True),True)
            if points :
                if __checkHeader(delta, points[0][0]):
                    # if DEBUG_HEADER:
                        # utils.drawRectBy4P(src, points)
                        # utils.drawRectBy2P(src, header)
                        # cv2.drawContours(srcDetect, [cnt.reshape(-1, 1, 2)], 0, (250, 0, 25), 2)
                        # utils.drawMidLineBy4P(src, points, i)
                        # utils.drawMidLineBy2P(src, header, i)
                    if CANNY_GAUSS:
                        if oldp and sl.SampleLine.isSameRect(points, oldp):
                            #仅当canny时, 需要处理内外圈都识别出来了
                            # del stripPoints[pCount]
                            # del stripHeads[pCount]
                            # pCount -= 1
                            #内外圈均值
                            stripPoints[pCount-1] = utils.mergeRect(points,oldp)
                            # stripHeads[pCount-1] = utils.mergePoints(header, oldh)
                        else:
                            # stripHeads.append(header)
                            stripPoints.append(points)
                            pCount += 1
                elif __checkFuncLine(delta, points[0][0]):
                    # if DEBUG_HEADER:
                    #     utils.drawRectBy4P(src, points)
                    if oldp and sl.SampleLine.isSameRect(points, oldp):
                        funcLines[fcCount - 1] = utils.mergeRect(points, oldp)
                    else:
                        funcLines.append(points)
                        fcCount += 1
                oldp = points
                # oldh = header
        # cv2.drawContours(srcDetect, [cnt.reshape(-1, 1, 2)], 0, (250, 0, 255), 1)
        # cv2.imshow('header-srcDetect', srcDetect)
    if DEBUG_HEADER:
        if CANNY_GAUSS:
            # for header in stripHeads:
            #     utils.drawMidLineBy2P(src, header, -5)
            # for points in funcLines:
            #     utils.drawRectBy4P(src, points)
            # for points in stripPoints:
            #     utils.drawMidLineBy4P(src, points, -5)
            pass
        # cv2.imshow('header-src', src)
    return stripPoints, funcLines #stripHeads