import cv2
import numpy as np
import imutils
from sys import argv

script, filename = argv

def fillContours(image, contour, ratio):
    # multiply the contour (x, y)-coordinates by the resize ratio,
    # then draw the contours and the name of the shape on the image
    contour = contour.astype("float")
    contour *= ratio
    contour = contour.astype("int")
    cv2.drawContours(image, [contour], -1, (255, 255, 255), cv2.FILLED)


def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype = "float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect

def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
    	[0, 0],
    	[maxWidth - 1, 0],
    	[maxWidth - 1, maxHeight - 1],
    	[0, maxHeight - 1]], dtype = "float32")

    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))

    # return the warped image
    return warped

image = cv2.imread(filename)
height, width, channel = image.shape
resized = imutils.resize(image, width=300)
ratio = image.shape[0] / float(resized.shape[0])

# convert the resized image to grayscale, blur it slightly,
# and threshold it
gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(resized,100,200)
print(edges.shape)

# cv2.imshow('dsd2', edges)
# cv2.waitKey(0)


cnts = cv2.findContours(edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

#cv2.imshow("contours", cnts[0])
#cv2.waitKey(0)

cnts = cnts[0] if imutils.is_cv2() else cnts[1]

canvas = np.zeros((height, width, 1), np.uint8)

# print(cnts)

# loop over the contours
for c in cnts:
    # compute the center of the contour, then detect the name of the
    # shape using only the contour
    M = cv2.moments(c)

    if M["m00"] == 0 : continue

    cX = int((M["m10"] / M["m00"]) * ratio)
    cY = int((M["m01"] / M["m00"]) * ratio)

    fillContours(canvas, c, ratio)

    #show the output image
    #cv2.imshow("Image", canvas)
    #cv2.waitKey(0)
#cv2.imshow("result",canvas)
#cv2.waitKey(0)

# dilate
kernel = np.ones((10, 10), np.uint8)
dilated = cv2.dilate(canvas, kernel)

# cv2.imshow("dilate", dilated)
# cv2.waitKey(0)

# find contours again
#bw = cv2.cvtColor(dilated, cv2.COLOR_BGR2GRAY)
cnts = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
cnts = cnts[0] if imutils.is_cv2() else cnts[1]

def getTestValue(image, posx):
    height, width = image.shape
    y = int(height / 2) - 2;
    x = int(width * posx)

    for i in range(5):
        y = y + i


    value = image[y, x]
    return value

def getTestFlag(value, std):
    if(value < std):
        flag = "+"
    else:
        flag = "-"
    return flag


# find bounding box
n = 1
for c in cnts:
    rect = cv2.minAreaRect(c)
    box = cv2.boxPoints(rect)
    box = np.int0(box)
    cv2.drawContours(image, [box], 0, (0, 0, 255), 2)

    # perspective correction
    warped = four_point_transform(image, box)
    gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)

    # calculate test value
    mark1 = getTestValue(gray, 0.132)
    mark2 = getTestValue(gray, 0.185)

    test1 = getTestValue(gray, 0.235)
    test2 = getTestValue(gray, 0.288)
    test3 = getTestValue(gray, 0.341)
    test4 = getTestValue(gray, 0.393)
    test5 = getTestValue(gray, 0.439)
    test6 = getTestValue(gray, 0.498)

    flag1 = getTestFlag(test1, mark2);
    flag2 = getTestFlag(test2, mark2);
    flag3 = getTestFlag(test3, mark2);
    flag4 = getTestFlag(test4, mark2);
    flag5 = getTestFlag(test5, mark2);
    flag6 = getTestFlag(test6, mark2);

    print(mark1, mark2, test1, test2, test3, test4, test5, test6)
    print(flag1, flag2, flag3, flag4, flag5, flag6)

    # show image
    cv2.imshow("warped", warped)
    cv2.imwrite(str(n) + ".png", warped)
    cv2.waitKey(0)
    n = n + 1


# cv2.imshow("box", image)
# cv2.waitKey(0)


# approxy polygon
#epsilon = 0.1 * cv2.arcLength(cnts, True)
#approx = cv2.approxPolyDP(cnts, epsilon, True)
#
#for c in approx:
#    fillContours(image2, c, ratio)

# cv2.imshow("dilate", image2)
# cv2.waitKey(0)

