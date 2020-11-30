import cv2
import numpy as np
import utils
import findHeaders as header

#gauss canny, 0 canny only, 3, 5
GAUSS = 0

HOUGHLINESP = False

#膜条左侧基准padding
BASE_LEFT = 60
BASE_MARGIN = 47
#############


def recognition(file):
    src = cv2.imread(file)
    src = src[header.BOARD_Y:header.BOARD_Y + header.BOARD_HEIGHT, header.BOARD_X:header.BOARD_X + header.BOARD_WIDTH]
    ###cut borad from image
    header.findHeader(src)

    cv2.imshow('result', src)
    cv2.waitKey()
    return


def main():
    i=0x30
    while i<0x31:
        i+=1
        recognition( ('samplew' ) +chr(i)+'.jpg')
        cv2.waitKey(0)


if __name__ == '__main__':
    main()