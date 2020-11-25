import cv2
import numpy as np

img = cv2.imread('scene.jpg')
gray= cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

sift = cv2.xfeatures2d.SIFT_create()
kp = sift.detect(gray,None)

img=cv2.drawKeypoints(gray,kp,img)

cv2.imshow('sift', img)
if cv2.waitKey(0) & 0xff == 27:
    cv2.destroyAllWindows()
