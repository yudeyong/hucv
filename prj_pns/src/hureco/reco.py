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
    :return:  str: 错误信息
    '''
    # imshow('src', src)
    if dict is None:
        return "Miss config file."+file, None
    template = config.getConfigFromDict(dict)
    err, src = template.getImg(file)
    # imshow('origin', src)
    # waitKey()
    if err: return err, None
    err, src = template.locateArea(src)
    if not err is None:
        return "Recognize Failed " + err + file, None
    ###cut borad from image
    list, img = template.recognise()

    # sr.StripRegion.recognise(gray, strips)

    # imshow('bw',bw)
    # imshow('src', src)
    # imshow('result', gray)
    # waitKey()
    if list is None or len(list) == 0:
        return "Zero result."+ file, None
    results = config.Dict()
    setattr(results, 'resultList', list)
    setattr(results, 'stripOffset', template.origin)
    setattr(results, 'stripImg', img)

    return None, results


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
    config = "PNS" + config + (lots[lot][-5:] if config=='14' else  '')
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
            config = "PNS"+lots[lot][:2]+lots[lot][-5:]
            config_json = _loadTemplate("../../config/strip" + config + ".json")
    # waitKey(0)


if __name__ == '__main__':
    main()
