import cv2
import numpy as np

BACK_WHITH = 1
THRESHOLD = 205 if (BACK_WHITH==1) else 150
#gauss canny, 0 canny only, 3, 5
GAUSS = 0

HOUGHLINESP = True

# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 b, 0x10000 g
RGB_GRAY = 0x100

BOARD_X= 60
BOARD_Y= 185
BOARD_HEIGHT= 640
BOARD_WIDTH= 520

#膜条左侧基准padding
BASE_LEFT = 60
BASE_MARGIN = 47

BOARD_RIGHT_WIDTH= 50

#膜条宽
STRIP_WIDTH = 18
STRIP_HALF_WIDTH = STRIP_WIDTH>>1

SAMPLING_BORDER=1+STRIP_WIDTH>>3

SAMPLING_WIDTH = 6

SCALABLE_Y=2
#############

def toGray(img):
    if not RGB_GRAY:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        g,b,r,_ = cv2.split(gray)
        if False:
            cv2.imshow('1-r', r)
            cv2.imshow('2-g', g)
            cv2.imshow('3-b', b)
        if RGB_GRAY==0x01:
            gray = r
        elif RGB_GRAY==0x100:
            gray = b
        else :
            gray = r
        # cv2.imshow('1-r channel-gray.png', r)
        # cv2.imshow('1-g channel-gray.png', g)
        # cv2.imshow('1-b channel-gray.png', b)
        # cv2.waitKey()
    # gray = r
    return gray

def toCanny(bw):
    if GAUSS==0 :
        canny = cv2.Canny(bw, 100, 200, 3)
        return canny
    else :
        img1 = cv2.GaussianBlur(bw,(GAUSS,GAUSS),0)
        cannyGaus = cv2.Canny(img1, 100, 200, 3)
        return cannyGaus

#深色only 查找边界
def findBorder(line1, line2):
    counter = 0
    for index, pixel in enumerate(line1):
        if pixel==0 and line2[index]==0:
            counter += 1
            if counter>5 :
                return index-5
        else:
            counter=0
    return index

#深色only 查找左边界
def findLeftBorder(img):
    line1 = img[BOARD_HEIGHT>>3]
    line2 = img[BOARD_HEIGHT-(BOARD_HEIGHT>>3)]
    return findBorder(line1,line2)

#深色only
def findTopBOrder(img):
    line1 = img[:,BOARD_WIDTH>>3]
    line2 = img[:,BOARD_WIDTH-(BOARD_WIDTH>>3)]
    return findBorder(line1, line2)

#合并相近线算法
def mergeLine(linesSet, lines, slopes):
    x1,y1,x2,y2=0,0,0,0
    max = 0
    min = lines.shape[0]
    for i in linesSet:
        if i > max : max = i
        if i < min : min = i
        x1+= lines[i][0]
        y1+= lines[i][1]
        x2+= lines[i][2]
        y2+= lines[i][3]
    l = len(linesSet)
    lines[max][0]=round(x1/l)
    lines[max][1]=round(y1/l)
    lines[max][2]=round(x2/l)
    lines[max][3]=round(y2/l)
    if slopes is not None:
        slopes[min] = getSlopeBias(lines[i])

#获取斜率,截距
def getSlopeBias(twoPoints):
    return( (twoPoints[3] - twoPoints[1]) / (twoPoints[2] - twoPoints[0])
        , (twoPoints[0] * twoPoints[3] - twoPoints[2] * twoPoints[1]) / (twoPoints[0] - twoPoints[2]) )

def getXFromLine(line):
    return (line[0],line[2])

def getYFromLine(line):
    return (line[1],line[3])

#slopes = None时, 按尾部合并检查
def clipLines(lines, slopes, func):
    throshold = STRIP_HALF_WIDTH*SCALABLE_Y if slopes is None else STRIP_HALF_WIDTH
    # 按y1排序
    lines = lines[np.lexsort(lines.T[1, None])]
    i = lines.shape[0] - 1
    y1, y2 = func(lines[i])
    # _, y1, _, y2 = lines[i]
    cleanArray = []
    # cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)
    sameLines = set()
    while (i > 0):
        y = lines[i][1]
        i -= 1
        oldy1 = y1
        oldy2 = y2
        y1, y2 = func(lines[i])
        if (abs(oldy1 - y1) < throshold and abs(oldy2 - y2) < throshold) and (slopes is not None or abs(lines[i][1]-y) < STRIP_HALF_WIDTH):
            sameLines.add(i)
            sameLines.add(i + 1)
            cleanArray.append(i)
            if slopes is not None:
                del slopes[i]
            continue
        elif (len(sameLines) > 0):
            mergeLine(sameLines, lines, slopes)
            sameLines = set()
    if (len(sameLines) > 0):
        mergeLine(sameLines, lines, slopes)
    if len(cleanArray) > 0:  # 删除重复线
        lines = np.delete(lines, cleanArray, 0)
    return lines

#整体过滤线, 竖线, 相近线合并
def clipStripLines(lines, src, slopes):
    lines = clipLines(lines, slopes, getYFromLine)
    # debug only {{
    w = src.shape[1] - 1;
    for line in lines:
        _, y1, _, y2 = line
        cv2.line(src, (BASE_LEFT, y1), (w, y2), (0, 0, 255), 1)

    print(lines.shape[0])
    i = lines.shape[0]
    while (i > 1):
        i -= 1
        y1 = lines[i][1] - lines[i - 1][1]
        y2 = lines[i][3] - lines[i - 1][3]
        print(y1, y2)
        i -= 1
    # }}
    return lines

#生成轮廓线
def getLines(img, src) :
    if HOUGHLINESP:
        lines1 = cv2.HoughLinesP(img, 1.2, np.pi / 240, 70, minLineLength=100, maxLineGap=20)
        if lines1 is not None:
            lines2 = lines1[:, 0, :]
            i = lines2.shape[0];
            w = src.shape[1]-1;
            cleanArray = []
            slopes = [None,None]*i
            while (i>0):
                i -= 1
                x1, y1, x2, y2 = lines2[i]

                if abs(x1-x2)<=abs(y1-y2) :
                    #过滤竖线
                    cleanArray.append(i)
                    del slopes[i]
                    continue

                slope,b=getSlopeBias((x1,y1,x2,y2))
                # slope = (y2-y1)/(x2-x1)
                # b = (x1*y2-x2*y1)/(x1-x2)
                slopes[i]=(slope,b)
                # cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)

                #扩展线到整个膜条
                y1 = round(slope*BASE_LEFT+b)
                y2 = round(slope*w+b)
                lines2[i] = (BASE_LEFT,y1, w, y2)
                # break
            if len(cleanArray)>0: #删除竖线
                lines2 = np.delete(lines2, cleanArray,0)
                # lines2 = np.column_stack((lines1[:], slope))
            return clipStripLines(lines2, src ,slopes )
        else :
            return None
    else:
        lines = cv2.HoughLines(img, 2, np.pi / 150, 160)
        for line in lines:
            for rho, theta in line:
                a = np.cos(theta)
                b = np.sin(theta)
                x0 = a * rho
                y0 = b * rho
                x1 = int(x0 + 100 * (-b))
                y1 = int(y0 + 100 * (a))
                x2 = int(x0 - 100 * (-b))
                y2 = int(y0 - 100 * (a))

                cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 2)
    return lines

def getTailLines(img, src) :
    lines1 = cv2.HoughLinesP(img, 1, np.pi / 240, 22, minLineLength=20, maxLineGap=1)
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
                lines2[i][1] = round(y1/SCALABLE_Y)
                lines2[i][3] = round(y2/SCALABLE_Y)
        if len(cleanArray)>0: #删除竖线
            lines2 = np.delete(lines2, cleanArray,0)
        return clipLines(lines2, None, getXFromLine)
    else:
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

def recognition(file):
    src = cv2.imread(file)
    ###cut borad from image
    src = src[BOARD_Y:BOARD_Y + BOARD_HEIGHT, BOARD_X:BOARD_X + BOARD_WIDTH]

    gray =  toGray(src)
    cv2.imshow('1-gray', gray)
    _, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)

    if BACK_WHITH==0:
        x1 = findLeftBorder(bw)
        y1 = findTopBOrder(bw)
        x2 = BASE_MARGIN - x1 if x1 < BASE_MARGIN else 0
        # cv2.imshow('2-bw.png', bw)
        bw = bw[y1:,x1:-x2]
        # cv2.imshow('2-bw.cut', bw)
        src = src[y1:,x1:-x2]
        gray = gray[y1:,x1:-x2]
    else:
        rightImg = resize(bw[:, -BOARD_RIGHT_WIDTH:], 1, SCALABLE_Y)
        tailImg = rightImg
        cv2.imshow('2-bw', tailImg)

    canny = toCanny(bw)
    # cv2.imshow('canny', canny)
    lines = getLines(canny, src)

    canny = toCanny(tailImg)
    # cv2.imshow('canny', canny)
    lines = getTailLines(canny, rightImg)
    x = src.shape[1]-BOARD_RIGHT_WIDTH
    for line in lines:
        cv2.line(src, (line[0]+x, line[1] ), (line[2]+x, line[3] ), (255, 0, 0), 2)
    # cv2.imshow('tail', rightImg)
    cv2.imshow('result', src)
    if BACK_WHITH == 0:
        cv2.imshow('2-bw.cut', bw)
    # else:
        # cv2.imshow('1-right', tail)

def main():
    i=0x30
    while i<0x36:
        i+=1
        recognition( ('samplew' if BACK_WHITH>0 else 'sample') +chr(i)+'.jpg')
        cv2.waitKey(0)


if __name__ == '__main__':
    main()