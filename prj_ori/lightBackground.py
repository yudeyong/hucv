import cv2
import const
import StripRegion as sr
import StripTemplate as st
import config
import utils

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
    strips = template.findHeader(src)

    gray = utils.toGray(src, None)
    for s in strips:
        s.readStrip(gray)

    # cv2.imshow('bw',bw)
    # cv2.imshow('src', src)
    cv2.imshow('result', gray)
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