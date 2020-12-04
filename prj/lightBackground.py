import cv2
import const
import recognise
import StripRegion
import StripTemplate as st
import config

DEBUG_OUTLINE = False
#gauss canny, 0 canny only, 3, 5
GAUSS = 0

HOUGHLINESP = False

#膜条左侧基准padding
BASE_LEFT = 60
BASE_MARGIN = 47
#############

def recognition(file, category):
    src = cv2.imread(file)
    # cv2.imshow('src', src)
    if not recognise.checkShape( src.shape):
        print("invalid size.")
        return
    template = config.loadTemplate(category)
    if not template :
        return "未找到配置文件"
    src = src[const.BOARD_Y:const.BOARD_Y + const.BOARD_HEIGHT, const.BOARD_X:const.BOARD_X + const.BOARD_WIDTH]
    ###cut borad from image
    stripHeads = template.findHeader(src)
    tailsLines, gray, bw = template.findTails(src)
    i = len(stripHeads)
    if i == tailsLines.shape[0]:


        # i 个区域,4个顶点,(x,y)
        regions = [None]*i
        while i>0:
            i -= 1
            rect = stripHeads[i]
            line = tailsLines[i]
            regions[i] = StripRegion.StripRegion(((rect[2], rect[3]),(line[2], line[3]),(rect[2], rect[1]),(line[0], line[1])),template)
            regions[i].findFuncLine(bw)
            if DEBUG_OUTLINE:
                cv2.line(src, (rect[0], rect[3]), (line[2], line[3]), (255, 0, 0), 2)
                cv2.line(src, (rect[0], rect[1]), (line[0], line[1]), (255, 0, 0), 2)
            # cv2.line(src, (rect[0], rect[3]), (rect[2], rect[1]), (255, 0, 0), 2)

        recognise.recognise(gray, regions)
    else:
        #todo
        print(file,"header:",i,"tails:",tailsLines.shape[0])
    # cv2.imshow('bw',bw)
    cv2.imshow('src', src)
    # cv2.imshow('result', gray)
    cv2.waitKey()
    return


def main():
    i=0x30
    while i<0x32:
        i+=1
        recognition( ('samplew' ) +chr(i)+'.jpg', "ITC92000")
        cv2.waitKey(0)


if __name__ == '__main__':
    main()