import cv2
import const
import StripRegion as sr
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
    # cv2.imshow('src', src)
    template = config.loadTemplate(category)
    if not template :
        return "未找到配置文件"
    src, err = template.getImg(file)
    # cv2.imshow('origin', src)
    # cv2.waitKey()
    if err :
        return err
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
            regions[i] = sr.StripRegion(((rect[2], rect[3]),(line[2], line[3]),(rect[2], rect[1]),(line[0], line[1])),template)
            regions[i].findFuncLine(bw)
            if DEBUG_OUTLINE:
                cv2.line(src, (rect[0], rect[3]), (line[2], line[3]), (255, 0, 0), 2)
                cv2.line(src, (rect[0], rect[1]), (line[0], line[1]), (255, 0, 0), 2)
            # cv2.line(src, (rect[0], rect[3]), (rect[2], rect[1]), (255, 0, 0), 2)

        sr.StripRegion.recognise(gray, regions)
    else:
        #todo
        print(file,"header:",i,"tails:",tailsLines.shape[0])
    # cv2.imshow('bw',bw)
    # cv2.imshow('src', src)
    # cv2.imshow('result', gray)
    cv2.waitKey()
    return


def main():
    i=0x31
    while i<0x32:
        msg = recognition( ('./samples/samplew' ) +chr(i)+'.jpg', "ITC92000")
        if msg :
            print(msg)
        cv2.waitKey(0)
        i+=1


if __name__ == '__main__':
    main()