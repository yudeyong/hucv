import numpy as np
import cv2
from matplotlib import pyplot as plt

img = cv2.imread('scene.jpg',0)

# Initiate FAST object with default values
fast = cv2.FastFeatureDetector_create()

# find and draw the keypoints
kp = fast.detect(img,None)
img2 = cv2.drawKeypoints(img, kp, img, color=(255,0,0))

# print(all default params
# print("Threshold: ", fast.getInt('threshold'))
# print("nonmaxSuppression: ", fast.getBool('nonmaxSuppression'))
# print("neighborhood: ", fast.getInt('type'))
# print("Total Keypoints with nonmaxSuppression: ", len(kp))

cv2.imshow('fast_true.png',img2)
if cv2.waitKey(0) & 0xff == 27:
    cv2.destroyAllWindows()

# Disable nonmaxSuppression
fast.setBool('nonmaxSuppression',0)
kp = fast.detect(img,None)

print("Total Keypoints without nonmaxSuppression: ", len(kp))

img3 = cv2.drawKeypoints(img, kp, color=(255,0,0))

cv2.imshow('fast_false',img3)
if cv2.waitKey(0) & 0xff == 27:
    cv2.destroyAllWindows()
