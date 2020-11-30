import cv2
import numpy as np


## rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 b, 0x10000 g
#   RGB_GRAY = 0x10000
def toGray(img, rgb_gray):
    if not rgb_gray:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
        g,b,r,_ = cv2.split(gray)
        if False:
            cv2.imshow('1-r', r)
            cv2.imshow('2-g', g)
            cv2.imshow('3-b', b)
        if rgb_gray==0x01:
            gray = r
        elif rgb_gray==0x100:
            gray = b
        else :
            gray = g
        # cv2.imshow('1-r channel-gray.png', r)
        # cv2.imshow('1-g channel-gray.png', g)
        # cv2.imshow('1-b channel-gray.png', b)
        # cv2.waitKey()
    # gray = r
    return gray

# param gaussian canny, 0 canny only, 3, 5
def toCanny(bw, gaussian):
    if gaussian==0 :
        canny = cv2.Canny(bw, 100, 200, 3)
        return canny
    else :
        img1 = cv2.GaussianBlur(bw,(gaussian,gaussian),0)
        cannyGaus = cv2.Canny(img1, 100, 200, 3)
        return cannyGaus

#合并相近平行线
def mergeLine(linesSet, lines, slopes):
    x1,y1,x2,y2=0,0,0,0
    max = 0
    min = lines.shape[0]
    for i in linesSet:
        if i > max : max = i
        if i < min : min = i
        x1+= lines[i][0]
        x2+= lines[i][2]
        y1 += lines[i][1]
        y2 += lines[i][3]
    l = len(linesSet)
    lines[max][0]=round(x1/l)
    lines[max][1]=round(y1/l)
    lines[max][2]=round(x2/l)
    lines[max][3]=round(y2/l)
    if slopes is not None:
        slopes[min] = getSlopeBias(lines[i])

#获取斜率,截距
def getSlopeBias(p1, p2):
    return( (p2[1] - p1[1]) / (p2[0] - p1[0])
        , (p1[0] * p2[1] - p2[0] * p1[1]) / (p1[0] - p2[0]) )

#获取斜率,截距
def getSlopeBias(twoPoints):
    return( (twoPoints[3] - twoPoints[1]) / (twoPoints[2] - twoPoints[0])
        , (twoPoints[0] * twoPoints[3] - twoPoints[2] * twoPoints[1]) / (twoPoints[0] - twoPoints[2]) )

def getXFromLine(line):
    return (line[0],line[2])

def getYFromLine(line):
    return (line[1],line[3])

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

def main():
    pass

if __name__ == '__main__':
    main()