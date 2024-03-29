from hureco import config
from hureco import utils

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
    :return:  str: 错误信息, result: result list
    str == None Xor result == None
    '''
    # imshow('src', src)
    if dict is None:
        return "Miss config file.", None
    template = config.getConfigFromDict(dict)
    err, src = template.getImg(file)
    # imshow('origin', src)
    # waitKey()
    if err:
        return err, None
    if template.locateArea(src) is None:
        return "Recognize Failed", None
    ###cut borad from image
    list, img = template.recognise()

    # sr.StripRegion.recognise(gray, strips)

    # imshow('bw',bw)
    # imshow('src', src)
    # imshow('result', gray)
    # waitKey()
    if list is None or len(list) == 0:
        return "Zero result.", None
    results = config.Dict()
    setattr(results, 'resultList', list)
    setattr(results, 'stripOffset', template.origin)
    setattr(results, 'stripImg', img)

    return None, results

def debugreco(jpgfile, config):
    msg, results = recognization(jpgfile,
                                 config)
    if msg:
        print(msg)
    else:
        for r in results.resultList:
            print(r.index, r.results, r.values)
            pass


def main():
    debugreco('../../samples/unreco.jpg',_loadTemplate("../../config/stripAGL6.json"))
    return
    # todo 68bch
    i = 15
    count = 1
    if i + count > 18: count = 18 - i
    if i > 10: i += 7
    end = i = i + 0x30
    end += count
    while i < end:
        if i == 0x3A:
            i = 0x41
            end += 7
        config = "AGL9" if i <= 0x30 else ("AGL8" if i > 0x46 else "AGL6")
        print("File *********", chr(i), config)

        debugreco(('../../samples/AGL') + chr(i) + '.jpg',
                                     _loadTemplate("../../config/strip" + config + ".json"))
        i += 1
    # waitKey(0)


if __name__ == '__main__':
    main()
