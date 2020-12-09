import cv2
import numpy as np
import utils
import const

DEBUG_TAIL =   False
#gauss canny, 0 canny only, 3, 5
GAUSS = 0

#膜条左侧基准padding
BASE_LEFT = 60
BASE_MARGIN = 47

BOARD_RIGHT_WIDTH= 50

SCALABLE_Y=3
#############

#slopes = None时, 按尾部合并检查
def clipLines(lines, func):
    # throshold = const.STRIP_HALF_WIDTH#*SCALABLE_Y
    # 按y1排序
    lines = lines[np.lexsort(lines.T[1, None])]
    i = lines.shape[0] - 1
    target1, target2 = func(lines[i])
    # _, target1, _, target2 = lines[i]
    cleanArray = []
    # cv2.line(src, (x1, y1), (x2, target2), (0, 0, 255), 1)
    sameLines = set()
    while (i > 0):
        y0 = lines[i][1]
        y1 = lines[i][3]
        i -= 1
        old1 = target1
        old2 = target2
        target1, target2 = func(lines[i])
        #if (abs(old1 - target1) < throshold and abs(old2 - target2) < throshold) and\
        if        ( abs(lines[i][1]-y0) < const.STRIP_HALF_HEIGHT or abs(lines[i][3]-y1) < const.STRIP_HALF_HEIGHT):
            cleanArray.append(i)
            if abs(lines[i][1]-y0) >= const.STRIP_HALF_WIDTH and abs(lines[i][3]-y1) < const.STRIP_HALF_WIDTH:
                # 连接线
                lines[i+1][1]=lines[i][1]
                lines[i+1][0]= round((lines[i][0]+lines[i+1][0])/2)
                lines[i + 1][2] = round((lines[i][2] + lines[i + 1][2]) / 2)
                print("concat")
                continue
            sameLines.add(i)
            sameLines.add(i + 1)
            continue
        elif (len(sameLines) > 0):
            utils.mergeLine(sameLines, lines)
            sameLines = set()
    if (len(sameLines) > 0):
        utils.mergeLine(sameLines, lines)
    # return lines
    if len(cleanArray) > 0:  # 删除重复线
        lines = np.delete(lines, cleanArray, 0)
    return lines

#整体过滤线, 竖线, 相近线合并
# def clipStripLines(lines, src):
#     lines = clipLines(lines, utils.getYFromLine)
#     # debug only {{
#     w = src.shape[1] - 1;
#     for line in lines:
#         _, y1, _, y2 = line
#         cv2.line(src, (BASE_LEFT, y1), (w, y2), (0, 0, 255), 1)
#
#     # print(lines.shape[0])
#     i = lines.shape[0]
#     while (i > 1):
#         i -= 1
#         y1 = lines[i][1] - lines[i - 1][1]
#         y2 = lines[i][3] - lines[i - 1][3]
#         # print(y1, y2)
#         i -= 1
#     # }}
#     return lines

# #生成轮廓线
# def getLines(img, src) :
#     lines1 = cv2.HoughLinesP(img, 1.2, np.pi / 240, 70, minLineLength=100, maxLineGap=20)
#     if lines1 is not None:
#         lines2 = lines1[:, 0, :]
#         i = lines2.shape[0];
#         w = src.shape[1]-1;
#         cleanArray = []
#         slopes = [None,None]*i
#         while (i>0):
#             i -= 1
#             x1, y1, x2, y2 = lines2[i]
#
#             if abs(x1-x2)<=abs(y1-y2) :
#                 #过滤竖线
#                 cleanArray.append(i)
#                 del slopes[i]
#                 continue
#
#             slope,b=utils.getSlopeBias((x1,y1,x2,y2))
#             # slope = (y2-y1)/(x2-x1)
#             # b = (x1*y2-x2*y1)/(x1-x2)
#             slopes[i]=(slope,b)
#             # cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)
#
#             #扩展线到整个膜条
#             y1 = round(slope*BASE_LEFT+b)
#             y2 = round(slope*w+b)
#             lines2[i] = (BASE_LEFT,y1, w, y2)
#             # break
#         if len(cleanArray)>0: #删除竖线
#             lines2 = np.delete(lines2, cleanArray,0)
#             # lines2 = np.column_stack((lines1[:], slope))
#         return clipStripLines(lines2, src ,slopes )
#     else :
#         return None
#
#     return lines

def getTailLines(img, src) :
    lines1 = cv2.HoughLinesP(img, 0.8, np.pi / 200, 40, minLineLength=10, maxLineGap=7)
    if lines1 is not None:
        lines2 = lines1[:, 0, :]
        i = lines2.shape[0];
        cleanArray = []
        while (i > 0):
            i -= 1
            x1, y1, x2, y2 = lines2[i]

            if abs(x1 - x2) >= abs(y1 - y2):
                # 过滤横线
                cleanArray.append(i)
                continue
            else:
                y1 = round(y1/SCALABLE_Y)
                y2 = round(y2/SCALABLE_Y)
                if (y1<=y2):
                    lines2[i][1] = y1
                    lines2[i][3] = y2
                else:
                    lines2[i][1] = y2
                    lines2[i][3] = y1

        if len(cleanArray)>0: #删除横线
            lines2 = np.delete(lines2, cleanArray,0)
        # return lines2
        if lines2.shape[0]>0:
            return clipLines(lines2, utils.getXFromLine)
    return None

def resize(img, xTimes, yTimes):
    (h,w) = img.shape
    nW = xTimes * w
    nH = yTimes * h

    # 1维寻址快
    nImg = np.empty([nH,nW],dtype='uint8')
    buf = img.reshape((-1))
    nBuf = nImg.reshape((-1))
    nCur = nW*nH
    cur = w*h
    tmpBuf = buf if (xTimes == 1) else nBuf

    while(cur>0):
        i = w
        if (xTimes > 1):
            #undebug
            lineCur = nCur
            while (i>0):
                cur -= 1
                i-=1
                nBuf[nCur-xTimes: nCur] = buf[cur]
                nCur-=xTimes
        else:
            lineCur = cur
        j = yTimes
        while j>0:
            j -= 1
            nBuf[nCur-nW:nCur] = tmpBuf[lineCur-nW:lineCur]
            nCur -=nW
        cur -= w
    return nImg

def getTails(tailImg):
    canny = utils.toCanny(tailImg, GAUSS)
    # cv2.imshow('canny', canny)
    lines = getTailLines(canny, tailImg)
    # cv2.imshow('tail', rightImg)
    return lines

def findTails(src, THRESHOLD):
    gray =  utils.toGray(src, None)
    if DEBUG_TAIL:
        cv2.imshow('1-gray', gray)
    _, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)

    #cv2.imshow('tail', bw)

    tailImg = resize(bw[:, -BOARD_RIGHT_WIDTH:], 1, SCALABLE_Y)
    if DEBUG_TAIL:
        COLORS = [(0xff,0,0),(0,0xff,0),(0,0,0xff), (0xff,0,0xff),(0,0xff,0xff),(0xff,0xff,0)]
        colorValue = 1
        cv2.imshow('2-bw', tailImg)
        i=0

    # canny = utils.toCanny(bw, GAUSS)
    # lines = getLines(canny, src)

    lines = getTails(tailImg)
    if lines is not None:
        x = src.shape[1]-BOARD_RIGHT_WIDTH
        # print("tail:",len(lines))
        for line in lines:
            line[0] += x
            line[2] += x
            if DEBUG_TAIL:
                i+=1
                if i>=-10 and i<=11:
                    colorValue += 1
                    if colorValue>=5: colorValue = 0

                    cv2.line(src, (line[0], line[1]-10 ), (line[2], line[3]+10 ), COLORS[colorValue], 2)
    if DEBUG_TAIL:
        cv2.imshow('tail-result', src)
    return lines, gray, bw

def __debugRecognition(file):
    src = cv2.imread(file)
    ###cut borad from image
    src = src[const.BOARD_Y:const.BOARD_Y + const.BOARD_HEIGHT, const.BOARD_X:const.BOARD_X + const.BOARD_WIDTH]

    findTails(src)

def main():
    i=0x30
    while i<0x31:
        i+=1
        __debugRecognition( ('samplew') +chr(i)+'.jpg')
        cv2.waitKey(0)


if __name__ == '__main__':
    main()