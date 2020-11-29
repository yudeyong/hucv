import cv2
import numpy as np
####试图通过识别表头矩形延展获得膜条边界尝试
# 误差太大失败 #
THRESHOLD = 200
#gauss canny, 0 canny only, 3, 5
GAUSS = 0

HOUGHLINESP = False

# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
RGB_GRAY = 0

BOARD_X= 56
BOARD_Y= 195
BOARD_HEIGHT= 640
BOARD_WIDTH= 520

BOARD_DETECT_WIDTH= 100
#膜条左侧基准padding
BASE_LEFT = 60
BASE_MARGIN = 47
#膜条宽
STRIP_HEIGHT = 18
STRIP_HALF_HEIGHT = STRIP_HEIGHT>>1
STRIP_WIDTH = STRIP_HEIGHT
#############

def toGray(img):
    if not RGB_GRAY:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        b,g,r,_ = cv2.split(gray)
        if False:
            cv2.imshow('1-r', r)
            cv2.imshow('2-g', g)
            cv2.imshow('3-b', b)
        if RGB_GRAY==0x01:
            gray = r
        elif RGB_GRAY==0x100:
            gray = b
        else :
            gray = g
        # cv2.imshow('1-r channel-gray.png', gray)
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

def getLines(img, offset, src) :
    if HOUGHLINESP:
        lines1 = cv2.HoughLinesP(img, 1.2, np.pi / 240, 10, minLineLength=6, maxLineGap=3)
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

                x1 += offset[0]
                y1 += offset[1]
                x2 += offset[0]
                y2 += offset[1]
                slope = (y2-y1)/(x2-x1)
                b = (x1*y2-x2*y1)/(x1-x2)
                slopes[i]=(slope,b)
                # cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)

                #扩展线到整个膜条
                x1 = offset[0]
                y1 = round(slope*x1+b)
                x2 = w
                y2 = round(slope*x2+b)
                lines2[i] = (x1,y1, x2, y2)
                # break
            if len(cleanArray)>0: #删除竖线
                lines2 = np.delete(lines2, cleanArray,0)
                # lines2 = np.column_stack((lines1[:], slope))
            #排序
            lines2 = lines2[np.lexsort(lines2.T[1,None])]
            i = lines2.shape[0]-1
            if i<=0:
                return None
            _, y1, _, y2 = lines2[i]
            cleanArray = []
            cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)
            while (i>0):
                i -= 1
                oldy1 = y1
                oldy2 = y2
                _,y1,_,y2 = lines2[i]
                if (oldy1-y1<STRIP_HALF_HEIGHT and oldy2-y2<STRIP_HALF_HEIGHT):
                    # 2端都检查, 避免相近2膜条异侧边
                    #todo 优化删除哪条线深色背景only
                    #todo 检查线之间是黑色还是白色, 深色背景only

                    cleanArray.append(i)
                    del slopes[i]
                    continue
                cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)
            if len(cleanArray)>0: #删除重复线
                lines2 = np.delete(lines2, cleanArray,0)
            # debug only {{
            print(lines2.shape[0])
            i=lines2.shape[0]
            while(i>1):
                i -= 1
                y1=lines2[i][1]-lines2[i-1][1]
                y2=lines2[i][3]-lines2[i-1][3]
                print(y1,y2)
                i -= 1
            #}}
        else :
            return None
    else:
        lines = cv2.HoughLines(img, 2, np.pi / 150, 40)
        if (lines is not None):
            for line in lines:
                for rho, theta in line:
                    a = np.cos(theta)
                    b = np.sin(theta)
                    x0 = a * rho
                    y0 = b * rho
                    x1 = int(x0 + 100 * (-b))
                    y1 = int(y0 + 100 * (a))
                    # x2 = int(x0 - 100 * (-b))
                    # y2 = int(y0 - 100 * (a))
                    x2 = int(x0 - src.shape[0] * (-b))
                    y2 = int(y0 - src.shape[0] * (a))

                    cv2.line(src, (x1+offset[0], y1+offset[1]), (x2+offset[0], y2+offset[1]), (0, 0, 255), 2)
        return lines
    return lines2

#######
def checkRectRange(points):
    if points.shape[0]<3: return None
    minX,minY=BOARD_WIDTH,BOARD_HEIGHT
    maxX,maxY=0,0
    for p in points:
        if p[0][0]>maxX: maxX = p[0][0]
        if p[0][0]<minX: minX = p[0][0]
        if p[0][1]>maxY: maxY = p[0][1]
        if p[0][1]<minY: minY = p[0][1]
    deltaX = maxX - minX
    deltaY = maxY - minY
    print(deltaX, deltaY,len(points))
    if deltaX<STRIP_WIDTH-(STRIP_WIDTH>>3): return None
    if deltaX>STRIP_WIDTH<<3: return None
    if deltaY<STRIP_HALF_HEIGHT: return None
    if deltaY>STRIP_HEIGHT<<1: return None
    # print("yes")
    return (minX,minY, maxX, maxY)

def recognition(file):
    src = cv2.imread(file)
    src = src[BOARD_Y:BOARD_Y + BOARD_HEIGHT, BOARD_X:BOARD_X + BOARD_WIDTH]
    ###cut borad from image
    srcDetect = src[:, BOARD_X:BOARD_X + BOARD_DETECT_WIDTH]

    gray =  toGray(srcDetect)
    # cv2.imshow('1-gray', gray)
    _, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)

    cv2.imshow('2-bw', bw)
    contours, hierarchy = cv2.findContours(bw, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE )

    i=len(contours)
    stripHeads = []
    while i>0:
        i-=1
        cnt = contours[i]
        if hierarchy[0][i][2]==-1 :
            stripHeader = checkRectRange(cnt)
            approx = cnt#cv2.approxPolyDP(cnt, 0.02*cv2.arcLength(cnt,True),True)
            if stripHeader:
                stripHeads.append(stripHeader)
                cv2.drawContours(srcDetect,[approx.reshape(-1,1,2)],0,(250,0,0),1)
    cv2.imshow('1-gray', srcDetect)

    for stripHeader in stripHeads:
        headImg = srcDetect[stripHeader[1]:stripHeader[3], stripHeader[0]:stripHeader[2]]
        canny = toCanny(headImg)
        lines = getLines(canny, stripHeader, src)
    cv2.imshow('result', src)
    cv2.waitKey()
    return
    # bw=gray

    # range = cv2.inRange(srcDetect, (0, 0, 0), (100, 100, 100))
    # cv2.imshow('3-range.png', range)

    # invert = cv2.bitwise_not(range)
    # cv2.imshow('4-invert.png', invert)

    canny = toCanny(bw)
    # cv2.imshow('canny', canny)
    lines = getLines(canny, src)

    # cv2.line(srcDetect, (BASE_LEFT, 0), (BASE_LEFT, BOARD_HEIGHT), (255, 0, 0), 2)
    # cv2.line(bw, (BASE_LEFT, 0), (BASE_LEFT, BOARD_HEIGHT), (255, 0, 0), 2)
    cv2.imshow('result', src)

def main():
    i=0x30
    while i<0x31:
        i+=1
        recognition( ('samplew' ) +chr(i)+'.jpg')
        cv2.waitKey(0)


if __name__ == '__main__':
    main()