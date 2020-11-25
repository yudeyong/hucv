import cv2
import numpy as np

src = cv2.imread('sample1.jpg')
# src = cv2.imread('IMG_327.jpeg')
gray = cv2.cvtColor(src, cv2.COLOR_BGR2BGRA) #COLOR_BGR2GRAY
_,_,redGray,_ = cv2.split(gray)
cv2.imshow('1-r channel-gray.png', redGray)
# cv2.imshow('4-gray.png', gray)
# cv2.waitKey()

retval, bw = cv2.threshold(redGray, 80.0, 255.0, cv2.THRESH_BINARY)
cv2.imshow('2-bw.png', bw)

# range = cv2.inRange(src, (0, 0, 0), (100, 100, 100))
# cv2.imshow('3-range.png', range)

# invert = cv2.bitwise_not(range)
# cv2.imshow('4-invert.png', invert)

# canny = cv2.Canny(r, 100, 200, 3)
# cv2.imshow('canny', canny)
img1 = cv2.GaussianBlur(redGray,(5,5),0)
cannyGaus = cv2.Canny(img1, 100, 200, 3)
cv2.imshow('cannyGaus', cannyGaus)


lines = cv2.HoughLines(cannyGaus, 1, np.pi / 180, 260)

for line in lines:
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
