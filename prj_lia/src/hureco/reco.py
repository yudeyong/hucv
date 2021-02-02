import cv2

from hureco import config


#############
def _loadTemplate(category):
    return config.getDictFromFile(category)

def recognization(file, dict):
    '''
    识别一张图片
    :param file: 图片文件名
    :param dict: 配置字典
    :return:  str: 错误信息
    '''
    # cv2.imshow('src', src)
    if dict is None:
        return "未找到配置文件:"
    template = config.getConfigFromDict(dict)
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
    i = 0
    count = 18
    if i + count > 18: count = 18 - i
    if i > 10: i += 7
    end = i = i + 0x30
    end += count
    while i < end:
        if i == 0x3A:
            i = 0x41
            end += 7
        config = "AGIM9" if i <= 0x30 else ("AGIG8" if i > 0x46 else "AGIGM6")
        print("File *********", chr(i), config)

        msg = recognization(('./samples/AGL') + chr(i) + '.jpg', _loadTemplate("./config/strip" + config + ".json"))
        if msg:
            print(msg)

        i += 1
    cv2.waitKey(0)


if __name__ == '__main__':
    main()
