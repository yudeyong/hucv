import cv2
import numpy as np

src = cv2.imread('WechatIMG19.jpeg')
# src = cv2.imread('scene.jpg')

gray = cv2.cvtColor(src, cv2.COLOR_RGB2GRAY)
cv2.imshow('1-grey.png', gray)

retval, bw = cv2.threshold(gray, 80.0, 255.0, cv2.THRESH_BINARY)
cv2.imshow('2-bw.png', bw)

range = cv2.inRange(src, (0, 0, 0), (100, 100, 100))
cv2.imshow('3-range.png', range)

invert = cv2.bitwise_not(range)
cv2.imshow('4-invert.png', invert)

canny = cv2.Canny(src, 100, 200, 3)
cv2.imshow('canny', canny)

lines = cv2.HoughLines(canny, 1, np.pi / 180, 100)

for line in lines:
     print(line)
     for rho,theta in line:
         a = np.cos(theta)
         b = np.sin(theta)
         x0 = a*rho
         y0 = b*rho
         x1 = int(x0 + 100*(-b))
         y1 = int(y0 + 100*(a))
         x2 = int(x0 - 100*(-b))
         y2 = int(y0 - 100*(a))

         cv2.line(src,(x1,y1),(x2,y2),(0,0,255),2)

cv2.imshow('result', src)
cv2.waitKey()
