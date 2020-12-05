import cv2
import numpy as np
import const

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
            cv2.waitKey()
        if rgb_gray==0x01:
            gray = r
        elif rgb_gray==0x100:
            gray = b
        else :
            gray = g
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
def mergeLine(linesSet, lines):
    x1,y1,x2,y2=0,0,0,0
    avg = 0
    maxV = 0
    # minV = lines.shape[0]
    l = len(linesSet)

    #引入平均值, 过滤标准差较大点
    if l>2:
        minSet = min(linesSet)
        maxSet = max(linesSet)
        avg = lines[minSet:maxSet+1,0].mean()
    for i in linesSet:
        if i > maxV : maxV = i
        # if i < minV : minV = i
        if l>2 and abs(lines[i][0]-avg)>(const.SAMPLING_WIDTH<<2):
            l -= 1
            continue
        x1+= lines[i][0]
        x2+= lines[i][2]
        y1 += lines[i][1]
        y2 += lines[i][3]
    lines[maxV][0]=round(x1/l) if x1!=0 else avg
    lines[maxV][1]=round(y1/l)
    lines[maxV][2]=round(x2/l) if x1!=0 else avg
    lines[maxV][3]=round(y2/l)

#获取斜率,截距
def getSlopeBiasByPoints(p1, p2):
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