from hureco_pns import config
from hureco_pns import utils
import cv2


#############
def _loadTemplate(category):
    return config.getDictFromFile(category)


def shink(img, w, h):
    utils.shrink(img, w, h)


def recognization(file, dict):
    '''
    识别一张图片
    :param file: 图片文件名
    :param dict: 配置字典
    :return:  str: 错误信息
    '''
    # imshow('src', src)
    if dict is None:
        return "Miss config file.", None
    template = config.getConfigFromDict(dict)
    err, src = template.getImg(file)
    # imshow('origin', src)
    # waitKey()
    if err: return err, None
    err, src = template.locateArea(src)
    if not err is None:
        return "Recognize Failed " + err + file, None
    ###cut borad from image
    list, _ = template.recognise()

    # sr.StripRegion.recognise(gray, strips)

    # cv2.imshow('src', src)
    # imshow('result', gray)
    # cv2.waitKey()
    debugImg(file, list, template)
    if list is None or len(list) == 0:
        return "None result." + file, None
    results = config.Dict()
    setattr(results, 'resultList', list)
    setattr(results, 'stripOffset', template.origin)
    # setattr(results, 'stripImg', img)

    return None, results


import cv2
import numpy


def debugImg(file, list, tmpl):
    src = cv2.imdecode(numpy.fromfile(file, dtype=numpy.uint8), -1)
    if src is None: return "file not found " + file, None
    # imshow('ori',src)
    # 识别区域
    # cv2.imshow('img', src)
    for result in list:
        # todo 膜条换算完成, 样本换算to be continue
        img = src[tmpl.top - result.stripRegion[1]:tmpl.top - result.stripRegion[0],
              tmpl.right:tmpl.left]
        # cv2.imshow('1-strip', img)
        # cv2.waitKey()

        region = [None] * 4
        for r in result.detectiveRegion:
            region[0] = tmpl.left - r[0]
            region[2] = tmpl.left - r[2]
            region[1] = tmpl.top - r[3]
            region[3] = tmpl.top - r[1]
            # print(region)
            utils.drawPolygonBy4P(src, region)
            # break
        # cv2.imshow( 'debugImg',img)
        # cv2.waitKey()
    cv2.imshow('debugImg ori', src)
    cv2.waitKey()
    # img = src[src.shape[0] - config.BOARD_AREA[1] - config.BOARD_AREA[3]
    #           :src.shape[0] - config.BOARD_AREA[1],
    #       config.BOARD_AREA[0]:config.BOARD_AREA[0] + config.BOARD_AREA[2]]
    # if ZOOMOUT_FIRST:
    #     src = utils.shrink3(src, PRE_X_TIMES, PRE_Y_TIMES)
    return None, src


def debugreco(jpgfile, config):
    print(jpgfile)
    msg, results = recognization(jpgfile,
                                 config)
    if msg:
        print(msg)
    else:
        for r in results.resultList:
            print(r.index, r.results, r.values)
            pass


def main():
    # debugreco('../samples/14/14-2102.jpg',_loadTemplate("../../config/stripAGL6.json"))
    # return
    lotLenth = (4 + 0x30, 5 + 0x30, 3 + 0x30)
    lots = ('14/14-2105', '14/14-2102', '11/11-2103')
    lot = 0
    i = 1
    count = 9
    end = i = i + 0x30
    end += count
    config = lots[lot][:2]
    config = "PNS" + config + (lots[lot][-5:] if config == '14' else '')
    config_json = _loadTemplate("../../config/strip" + config + ".json")
    print("File *********", chr(i), config)
    while i < end:  # HEX
        if i == 0x3A:
            i = 0x41
            end += 7

        debugreco(('../samples/' + lots[lot] + '-') + chr(i) + '.jpg', config_json)
        i += 1
        if i > lotLenth[lot]:
            i -= lotLenth[lot]
            end -= i
            i += 0x30
            lot += 1
            if lot >= len(lots): break
            config = "PNS" + lots[lot][:2] + lots[lot][-5:]
            config_json = _loadTemplate("../../config/strip" + config + ".json")
    # waitKey(0)


if __name__ == '__main__':
    main()
