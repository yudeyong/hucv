import cv2
import numpy as np
import const
import utils

THRESHOLD = 130

# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
RGB_GRAY = 0

BOARD_X= 240
BOARD_Y= 195
BOARD_HEIGHT= 640
BOARD_WIDTH= 520

BOARD_DETECT_WIDTH= 100

def checkRectRange(points):
    if points.shape[0] < 3: return None
    minX, minY = BOARD_WIDTH, BOARD_HEIGHT
    maxX, maxY = 0, 0
    for p in points:
        if p[0][0] > maxX: maxX = p[0][0]
        if p[0][0] < minX: minX = p[0][0]
        if p[0][1] > maxY: maxY = p[0][1]
        if p[0][1] < minY: minY = p[0][1]
    deltaX = maxX - minX
    deltaY = maxY - minY
    print(deltaX, deltaY, len(points))
    if deltaX < const.STRIP_WIDTH - (const.STRIP_WIDTH >> 3): return None
    if deltaX > const.STRIP_WIDTH << 3: return None
    if deltaY < const.STRIP_HALF_HEIGHT: return None
    if deltaY > const.STRIP_HEIGHT << 1: return None
    # print("yes")
    return (minX, minY, maxX, maxY)

def findHeader(src):
    srcDetect = src[:, :BOARD_DETECT_WIDTH]

    gray = utils.toGray(srcDetect, RGB_GRAY)
    # cv2.imshow('1-gray', gray)
    _, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)

    cv2.imshow('2-bw', bw)
    contours, hierarchy = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    i = len(contours)
    stripHeads = []
    while i > 0:
        i -= 1
        cnt = contours[i]
        if hierarchy[0][i][2] == -1:
            stripHeader = checkRectRange(cnt)
            approx = cnt  # cv2.approxPolyDP(cnt, 0.02*cv2.arcLength(cnt,True),True)
            if stripHeader:
                stripHeads.append(stripHeader)
                cv2.drawContours(srcDetect, [approx.reshape(-1, 1, 2)], 0, (250, 0, 0), 2)
    cv2.imshow('1-gray', src)