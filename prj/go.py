import cv2
import numpy as np

BACK_WHITH = 0
THRESHOLD = 248 if (BACK_WHITH==1) else 150
GAUSS = 5 #0, 3, 5
HOUGHLINESP = True

RGB_GRAY = 0x1

BOARD_X= 60
BOARD_Y= 185
BOARD_HEIGHT= 640
BOARD_WIDTH= 500

BASE_LEFT = 30

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
            gray = g
        # cv2.imshow('1-r channel-gray.png', gray)
    # gray = r
    cv2.imshow('1-gray', gray)
    return gray

def toCanny(bw):
    if GAUSS==0 :
        canny = cv2.Canny(bw, 100, 200, 3)
        return canny
    else :
        img1 = cv2.GaussianBlur(bw,(GAUSS,GAUSS),0)
        cannyGaus = cv2.Canny(img1, 100, 200, 3)
        return cannyGaus

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

def findLeftBorder(img):
    line1 = img[BOARD_HEIGHT>>3]
    line2 = img[BOARD_HEIGHT-(BOARD_HEIGHT>>3)]
    return findBorder(line1,line2)

def findTopBOrder(img):
    line1 = img[:,BOARD_WIDTH>>3]
    line2 = img[:,BOARD_WIDTH-(BOARD_WIDTH>>3)]
    return findBorder(line1, line2)

def recognition(file):
    src = cv2.imread(file)
    ###cut borad from image
    cut_img = src[BOARD_Y:BOARD_Y + BOARD_HEIGHT, BOARD_X:BOARD_X + BOARD_WIDTH]
    src=cut_img

    gray =  toGray(src)
    retval, bw = cv2.threshold(gray, THRESHOLD, 255.0, cv2.THRESH_BINARY)

    x = findLeftBorder(bw)
    y = findTopBOrder(bw)

    cv2.imshow('2-bw.png', bw)
    bw = bw[y:,x:]
    cv2.imshow('2-bw.cut', bw)
    src = src[y:,x:]
    # bw=gray

    # range = cv2.inRange(src, (0, 0, 0), (100, 100, 100))
    # cv2.imshow('3-range.png', range)

    # invert = cv2.bitwise_not(range)
    # cv2.imshow('4-invert.png', invert)

    canny = toCanny(bw)
    cv2.imshow('canny', canny)

    if HOUGHLINESP:
        lines1 = cv2.HoughLinesP(canny, 1.2, np.pi / 240, 160, minLineLength=100, maxLineGap=60)
        if lines1 is not None:
            lines2 = lines1[:, 0, :]
            i = lines2.shape[0];
            w = canny.shape[1]-1;
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

                slope = (y2-y1)/(x2-x1)
                b = (x1*y2-x2*y1)/(x1-x2)
                slopes[i]=(slope,b)
                # cv2.line(src, (x1, y1), (x2, y2), (0, 0, 255), 1)

                #扩展线到整个膜条
                x1 = BASE_LEFT
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
            _, y1, _, y2 = lines2[i]
            cleanArray = []
            cv2.line(src, (x1, y1), (x2, y2), (255, 0, 0), 1)
            while (i>0):
                i -= 1
                oldy1 = y1
                oldy2 = y2
                _,y1,_,y2 = lines2[i]
                if (oldy1-y1<10 and oldy2-y2<10):
                    # 2端都检查, 避免相近2膜条异侧边
                    #todo 优化删除哪条线
                    cleanArray.append(i)
                    continue
                cv2.line(src, (x1, y1), (x2, y2), (255, 0, 0), 1)
            if len(cleanArray)>0: #删除重复线
                lines2 = np.delete(lines2, cleanArray,0)
            print(lines2.shape[0])

    else:
        lines = cv2.HoughLines(canny, 2, np.pi / 150, 160)
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

    cv2.line(src, (BASE_LEFT, 0), (BASE_LEFT, BOARD_HEIGHT), (255, 0, 0), 2)
    cv2.line(bw, (BASE_LEFT, 0), (BASE_LEFT, BOARD_HEIGHT), (255, 0, 0), 2)
    cv2.imshow('result', src)

    cv2.imshow('2-bw.cut', bw)

def main():
    i=0x30
    while i<0x36:
        i+=1
        recognition('sample'+chr(i)+'.jpg')
        cv2.waitKey(0)


if __name__ == '__main__':
    main()