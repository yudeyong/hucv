import cv2
import numpy as np
import imutils
from pyimagesearch.shapedetector import ShapeDetector

image = cv2.imread('scene.jpg')
resized = imutils.resize(image, width=300)
ratio = image.shape[0] / float(resized.shape[0])

# convert the resized image to grayscale, blur it slightly,
# and threshold it
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(resized,100,200)
cv2.imshow('dsd2', edges)
cnts = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL,
    cv2.CHAIN_APPROX_NONE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]
sd = ShapeDetector()

print(cnts)

# loop over the contours
for c in cnts:
    # compute the center of the contour, then detect the name of the
    # shape using only the contour
    M = cv2.moments(c)
    cX = int((M["m10"] / M["m00"]) * ratio)
    cY = int((M["m01"] / M["m00"]) * ratio)


    # multiply the contour (x, y)-coordinates by the resize ratio,
    # then draw the contours and the name of the shape on the image
    c = c.astype("float")
    c *= ratio
    c = c.astype("int")
    cv2.drawContours(image, [c], -1, (0, 255, 0), 2)
    #show the output image
    #cv2.imshow("Image", image)
    #cv2.waitKey(0)
cv2.imshow("result",image)
cv2.waitKey(0)
