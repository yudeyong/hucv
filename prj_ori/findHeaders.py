import cv2
import numpy as np

import SampleLine as sl
import const
import utils

DEBUG_HEADER = not False
BOARD_DETECT_WIDTH= 200

def checkRectRange(points):
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
    deltaX = maxX - minX
    deltaY = maxY - minY
    # print(deltaX, deltaY, len(points))
    if deltaX < const.STRIP_WIDTH - (const.STRIP_WIDTH >> 3): return None,None
    if deltaX > const.STRIP_WIDTH << 3: return None,None
    if deltaY < const.STRIP_HALF_HEIGHT: return None,None
    if deltaY > const.STRIP_HEIGHT << 1: return None,None

    # print("yes")
    return (minX, minY, maxX, maxY), pLB

def __showDebug(name,img):
    a = utils.shrink(img, 2, 2)
    cv2.imshow(name, a)
    cv2.waitKey()


def findHeader(src, RGB_GRAY, THRESHOLD):
    src = utils.shrink3(src, 2, 2)
    srcDetect = src[:, :BOARD_DETECT_WIDTH]

    gray = utils.toGray(srcDetect, RGB_GRAY)
    # cv2.imshow('1-gray', gray)
    _, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)
    # __showDebug("bw",bw)

    bw = utils.toCanny(bw,5)
    # __showDebug("canny",bw)
    # exit(0)

    if DEBUG_HEADER:
        # __showDebug("header-bw", bw)
        cv2.imshow("header-bw", bw)
    # bw = utils.toCanny(bw, 0)
    # if DEBUG_HEADER:
    #     cv2.imshow("header-canny", bw)
    contours, hierarchy = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    i = len(contours)
    stripHeads = []
    stripPoints = []
    oldp = points = None
    pCount = 0
    while i > 0:
        i -= 1
        cnt = contours[i]
        if hierarchy[0][i][2] != -111 \
                and cnt[0][0][1]<450 :
                # and cnt[0][0][1]>410 :
            stripHeader,points = checkRectRange(cnt)
            # approx = cnt  # cv2.approxPolyDP(cnt, 0.02*cv2.arcLength(cnt,True),True)
            if stripHeader:
                stripHeads.append(stripHeader)
                stripPoints.append(points)
                if DEBUG_HEADER:
                    utils.drawRectBy4P(src, points)
                    # utils.drawRectBy2P(src, stripHeader)
                    # cv2.drawContours(srcDetect, [cnt.reshape(-1, 1, 2)], 0, (250, 0, 25), 2)
                    utils.drawMidLineBy4P(src, points, i)
                    if oldp and sl.SampleLine.isSameRect(points, oldp):
                        #内外圈都识别出来了
                        del stripPoints[pCount]
                        del stripHeads[pCount]
                        pCount -= 1
                        #内外圈均值
                        stripPoints[pCount] = utils.mergeRect(points,oldp)
                pCount += 1
                oldp = points

        # cv2.drawContours(srcDetect, [cnt.reshape(-1, 1, 2)], 0, (250, 0, 255), 1)
    if DEBUG_HEADER:
        for points in stripPoints:
            utils.drawMidLineBy4P(src, points, -5)
        cv2.imshow('header-src', src)
    return stripHeads