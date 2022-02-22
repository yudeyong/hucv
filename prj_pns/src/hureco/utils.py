import math

import \
    cv2  # import split, COLOR_BGR2GRAY, COLOR_BGR2BGRA, cvtColor, Canny, GaussianBlur, fitLine, DIST_L2, line as cvline, imshow, waitKey
import numpy as np


## rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 b, 0x10000 g
#   RGB_GRAY = 0x10000
def toGray(img, rgb_gray):
    if not rgb_gray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        b, g, r, _ = cv2.split(gray)
        if False:
            cv2.imshow('1-r', r)
            cv2.imshow('2-g', g)
            cv2.imshow('3-b', b)
            cv2.waitKey()
        if rgb_gray == "r":
            gray = r
        elif rgb_gray == "b":
            gray = b
        else:
            gray = g
    # gray = r
    return gray


# param gaussian canny, 0 canny only, 3, 5
def toCanny(bw, gaussian):
    if gaussian == 0:
        canny = cv2.Canny(bw, 200, 230, 3)
        return canny
    else:
        img1 = cv2.GaussianBlur(bw, (gaussian, gaussian), 0)
        cannyGaus = cv2.Canny(img1, 10, 30, 453)
        return cannyGaus


def drawLines(src, lines):
    color = ((255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255), (255, 0, 255))
    i = 0
    for line in lines:
        cv2.line(src, (line[0], line[1]), (line[2], line[3]), color[i], 2)
        i += 1
        if i >= len(color): i = 0


# 获取斜率,截距
def getSlopeBiasBy2P(p1, p2):
    return ((p2[1] - p1[1]) / (p2[0] - p1[0])
            , (p1[0] * p2[1] - p2[0] * p1[1]) / (p1[0] - p2[0]))


def getCosReciprocalBy2P(p1, p2):
    x = p2[0] - p1[0]
    y = p1[1] - p2[1]
    return math.sqrt(x * x + y * y) / x


def getSlopeBias(twoPoints):
    '''
        获取斜率,截距
    :param twoPoints: (x0,y0,x1,y1)
    :return:
    '''
    if twoPoints[2] != twoPoints[0]:
        slope = (twoPoints[3] - twoPoints[1]) / (twoPoints[2] - twoPoints[0])
        bias = (twoPoints[0] * twoPoints[3] - twoPoints[2] * twoPoints[1]) / (twoPoints[0] - twoPoints[2])
    else:
        slope = float("inf")
        bias = twoPoints[0]
    return (slope, bias)


def getXFromLine(line):
    return (line[0], line[2])


def getYFromLine(line):
    return (line[1], line[3])


def shrink(img, xTimes, yTimes):
    '''
    shrink gray scale
    :param img:
    :param xTimes:
    :param yTimes:
    :return:
    '''
    (h, w) = img.shape
    tW = math.ceil(w / xTimes)
    tH = math.ceil(h / yTimes)

    # 1维寻址快
    tImg = np.empty([tH, tW], dtype='uint8')
    sBuf = img.reshape((-1))
    tBuf = tImg.reshape((-1))
    tCur = tW * tH
    sCur = w * h

    while (tCur > 0):
        tX = tW
        lineCur = sCur
        if (xTimes > 1):
            # undebug
            while (tX > 0):
                tCur -= 1
                sCur -= xTimes
                tBuf[tCur] = sBuf[sCur]
                tX -= 1
            # tCur = lineCur - tW * yTimes
            sCur = lineCur - w * yTimes
        else:
            tBuf[tCur - tW:tCur] = sBuf[sCur - tW:sCur]
            sCur -= tW * yTimes
            tCur -= tW
    return tImg


def shrink3(img, xTimes, yTimes):
    '''
    shrink RGB
    :param img:
    :param xTimes:
    :param yTimes:
    :return:
    '''
    (h, w, _) = img.shape
    tW = math.ceil(w / xTimes)
    tH = math.ceil(h / yTimes)

    # 1维寻址快
    tImg = np.empty([tH, tW, 3], dtype='uint8')
    sBuf = img.reshape((-1, 3))
    tBuf = tImg.reshape((-1, 3))
    tCur = tW * tH
    sCur = w * h

    while (tCur > 0):
        tX = tW
        lineCur = sCur
        if (xTimes > 1):
            # undebug
            while (tX > 0):
                tCur -= 1
                sCur -= xTimes
                tBuf[tCur, :] = sBuf[sCur, :]
                tX -= 1
            # tCur = lineCur - tW * yTimes
            sCur = lineCur - w * yTimes
        else:
            tBuf[tCur - tW:tCur, :] = sBuf[sCur - tW:sCur, :]
            sCur -= tW * yTimes
            tCur -= tW
    return tImg


def enlarge(img, xTimes, yTimes):
    # todo 未调试
    if xTimes > 1:
        img = np.repeat(img, xTimes, axis=0)
    if yTimes > 1:
        img = np.repeat(img, yTimes, axis=1)
    return img


def drawRectBy2P(src, p0, p1):
    cv2.rectangle(src, p0,p1,(0,0,0),1)
    # return
    # p = ((p0[0], p0[1]), (p1[0], p0[1]), (p0[0], p1[1]), (p1[0], p1[1]))
    # drawRectBy4P(src, p)


def drawPolygonBy4P(src, p):
    # cv2.rectangle(src, p[0],p[3],(0,0,0),1)
    # return
    cv2.line(src, (p[0], p[1]), (p[2], p[1]), (0, 0, 255), 1)
    cv2.line(src, (p[2], p[1]), (p[2], p[3]), (0, 0, 0), 1)
    cv2.line(src, (p[0], p[1]), (p[0], p[3]), (0, 255, 0), 1)
    cv2.line(src, (p[0], p[3]), (p[2], p[3]), (255, 0, 0), 1)


def drawMidLineBy2P(src, p, i):
    p = ((p[0], p[1]), (p[2], p[1]), (p[0], p[3]), (p[2], p[3]))
    drawMidLineBy4P(src, p, i)


def mid2PBy4P(p):
    '''
    4坐标点取中点
    :param p:
    :return:
    '''
    p1 = [(p[0][0] + p[2][0]) >> 1, (p[0][1] + p[2][1]) >> 1]
    return p1, [(p[1][0] + p[3][0]) >> 1, (p[1][1] + p[3][1]) >> 1]


def drawFullLine(src, x0, k, b, i):
    '''

    :param src:
    :param x0: 点x
    :param k: 斜率
    :param b: 截距
    :param i: 颜色参数
    :return:
    '''
    if k != float("inf"):
        x2 = src.shape[1]
        y2 = round(k * x2 + b)
        x1 = x0
        y1 = round(x0 * k + b)
    else:
        x1 = round(b)
        y1 = 0
        x2 = round(b)
        y2 = src.shape[1]

    if i < 0:
        c = (255 * (i & 1), 255 * (i & 2), 255 * (i & 4))
    elif i == 0:
        c = 0
    else:
        c = (0xff, 0, 0xff * (i & 1))

    cv2.line(src, (x1, y1), (x2, y2), c, 2 - (i < 0) * 1)


def drawMidLineBy4P(src, p, i):
    p1, p2 = mid2PBy4P(p)
    k, b = getSlopeBiasBy2P(p1, p2)
    # p1 = ((p[0][0] + p[2][0]) >> 1, (p[0][1] + p[2][1]) >> 1 )
    drawFullLine(src, (p[0][0] + p[2][0]) >> 1, k, b, i)


def mergePoints(p1, p2):
    return ((p1[0] + p2[0]) >> 1, (p1[1] + p2[1]) >> 1,
            (p1[2] + p2[2]) >> 1, (p1[3] + p2[3]) >> 1)


def mergeRect(p1, p2):
    return [[(p1[0][0] + p2[0][0]) >> 1, (p1[0][1] + p2[0][1]) >> 1],
            [(p1[1][0] + p2[1][0]) >> 1, (p1[1][1] + p2[1][1]) >> 1],
            [(p1[2][0] + p2[2][0]) >> 1, (p1[2][1] + p2[2][1]) >> 1],
            [(p1[3][0] + p2[3][0]) >> 1, (p1[3][1] + p2[3][1]) >> 1]]


# def getCross(hkb, vkb):
#     if vkb[0] == float("inf"):
#         if abs(hkb[0]) <= 0.1:
#             return (round(vkb[1]), round(hkb[1]))
#     elif abs(vkb[0] * hkb[0] + 1) < 0.3:
#         x = (hkb[1] - vkb[1]) / (vkb[0] - hkb[0])
#         return (round(x), round(vkb[0] * x + vkb[1]))
#     return None


def drawDot(src, p, i=3):
    '''
        i>0 cross
        i<0 rect
    '''
    f = i
    if i == 0: f = 3
    p1 = (round(p[0] + f), round(p[1] + f))
    p2 = (round(p[0]) - f, round(p[1] - f))
    if (i > 0):
        cv2.line(src, p1, p2, 0, 1)
        cv2.line(src, (p1[0], p2[1]), (p2[0], p1[1]), 0, 1)
    else:
        drawRectBy2P(src, p1, p2)


def showDebug(name, img):
    a = shrink(img, 2, 2)
    cv2.imshow(name, a)
    cv2.waitKey()


def derivative(img, posi, axis, axis_dirt, deri_dirt):
    """
    针对区域'求导', 确定采样线边界
    :param posi: 坐标
    :param axis: 0:x方向, 1:y方向
    :param axis_dirt: 坐标方向 1增量, -1减量
    :param deri_dirt: 求导方向 1正增量, -1负赠量
    :return: 有效区域数组, 数组中有效线
    """
    axis = 1 - axis
    if img.shape[axis] <= 2: return [], ()
    i = posi
    if axis_dirt == 1:
        i1 = img.shape[axis] - 1
    else:
        i1 = 0
    i1 += axis_dirt
    if axis == 1: img = img.T
    value0 = np.sum(img[i])
    list = []
    top = 0
    x = i
    while True:
        i += axis_dirt
        if (i == i1): break
        value1 = np.sum(img[i])
        delta = int(value1) - value0
        if (top - delta) * deri_dirt < 0:
            x = i
            top = delta
        value0 = value1
        list.append(delta)
    return list, x, top


def maxWind(array, size, threshold, faultTolerant):
    '''
    查找array[0]中是否存在>=threshold宽度为size的窗口,允许出现faultTolerant个不满足值, 边界值不算
    :param array:
    :param size:
    :param threshold:
    :param faultTolerant:
    :return: 开始下标, size of win
    '''
    # todo faultTolerant>1未调试
    cursor = [None] * faultTolerant
    fIndex = 0
    i = len(array)
    j = 0
    length = 0
    while i > 0:
        i -= 1
        if array[i][0] >= threshold:
            # 满足
            if j == 0:
                # 第一个值
                j = i
                fIndex = 0
                length = 1
            else:
                # 已经有值, 累计长度
                length += 1
        elif j > 0:
            if length >= size:
                # 考虑容错,这里不该直接返回,可以继续按容错查找,先忽略
                return i + 1, length
            # 已经有值
            if fIndex < faultTolerant:
                # 可容错
                cursor[fIndex] = i
                fIndex += 1
            else:
                # 到达容错上限
                if cursor[0] == i + faultTolerant:
                    # 连续空,重置
                    j = 0
                    length = 0
                    fIndex = 0
                else:
                    delta = 1
                    while delta < faultTolerant and cursor[delta] == cursor[delta - 1]: delta += 1
                    # 跳过连续的0
                    fIndex -= delta
                    k = delta - 1
                    j = cursor[k] - 1
                    length = j - cursor[k]
                    for k in range(0, fIndex):
                        cursor[k] = cursor[k + delta]
                j = 0
    return -1, 0


def getFitLine(points):
    p = np.asanyarray(points)
    out = cv2.fitLine(p, cv2.DIST_L2, 0, 0.01, 0.01)
    k = out[1] / out[0]
    b = out[3] - k * out[2]
    # self.midHeader[0][0] = round((self.midHeader[0][1] - b[0] )/k[0])
    return k[0], b[0]


if __name__ == '__main__':
    pass
