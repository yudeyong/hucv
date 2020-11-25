import cv2
import numpy as np

# read image
# img = cv2.imread('IMG_3271.JPG')
img = cv2.imread('scene.jpg')
# filter it
img = cv2.GaussianBlur(img, (11, 11), 0)
gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
cv2.imshow('gaussian', gray_img)

# get edges using laplacian
laplacian_val = cv2.Laplacian(gray_img, cv2.CV_32F)
cv2.imshow('laplacian', laplacian_val)

# lap_img = np.zeros_like(laplacian_val, dtype=np.float32)
# cv2.normalize(laplacian_val, lap_img, 1, 255, cv2.NORM_MINMAX)
# cv2.imwrite('laplacian_val.jpg', lap_img)

# apply threshold to edges
ret, laplacian_th = cv2.threshold(laplacian_val, thresh=2, maxval=255, type=cv2.THRESH_BINARY)
cv2.imshow('laplacian_th', laplacian_th)
# filter out salt and pepper noise
laplacian_med = cv2.medianBlur(laplacian_th, 5)
cv2.imshow('laplacian_blur', laplacian_med)
# cv2.imwrite('laplacian_blur.jpg', laplacian_med)
laplacian_fin = np.array(laplacian_med, dtype=np.uint8)
cv2.imshow('laplacian_fin', laplacian_fin)

# get lines in the filtered laplacian using Hough lines
lines = cv2.HoughLines(laplacian_fin,1,np.pi/135,480)

for i in range(len(lines)):
    for rho,theta in lines[i]:
        a = np.cos(theta)
        b = np.sin(theta)
        x0 = a*rho
        y0 = b*rho
        x1 = int(x0 + 1000*(-b))
        y1 = int(y0 + 1000*(a))
        x2 = int(x0 - 1000*(-b))
        y2 = int(y0 - 1000*(a))
        # overlay line on original image
        cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)

# cv2.imwrite('processed.jpg', img)
cv2.imshow('Window', img)
cv2.waitKey(0)
