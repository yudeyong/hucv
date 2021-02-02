import json

from hureco.agi import StripTemplate


class Dict(dict):
    def __init__(self, obj):
        self.__dict__.update(obj)


def getConfigFromDict(dict):
    return StripTemplate.StripTemplate(_dict_to_object(dict))


def _dict_to_object(dict_obj):
    return Dict(dict_obj)

def getDictFromFile(file):
    '''

    :param file:
    :return: dict object
    '''
    try:
        with open(file, 'r') as load_f:
            loadDict = json.load(load_f)
        # print(loadDict)
    except IOError:
        return None
    # load_dict['line'] = [8200,{1:[['Python',81],['shirt',300]]}]
    return loadDict

