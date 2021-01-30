import cv2

from src.hureco import config


#############

def recognition(file, category):
    # cv2.imshow('src', src)
    template = config.loadTemplate(category)
    if not template:
        return "未找到配置文件"
    src, err = template.getImg(file)
    # cv2.imshow('origin', src)
    # cv2.waitKey()
    if err:
        return err
    if template.locatArea(src) is None:
        return "识别失败"
    ###cut borad from image
    strips = template.recognise()

    # sr.StripRegion.recognise(gray, strips)

    # cv2.imshow('bw',bw)
    # cv2.imshow('src', src)
    # cv2.imshow('result', gray)
    # cv2.waitKey()
    return


def main():
    # todo 68bch
    i = 1
    count = 18
    if i + count > 18: count = 18 - i
    if i > 10: i += 7
    end = i = i + 0x30
    end += count
    while i < end:
        if i == 0x3A:
            i = 0x41
            end += 7
        print("File *********", chr(i))
        config = "AGIG8" if i <= 0x32 else ("AGIM9" if i == 0x33 else "AGIGM6")
        msg = recognition(('./samples/AGL') + chr(i) + '.jpg', "./config/strip" + config + ".json")
        if msg:
            print(msg)

        i += 1
    cv2.waitKey(0)


if __name__ == '__main__':
    main()
