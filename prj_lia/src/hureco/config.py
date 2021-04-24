from json import load

from agi import StripTemplate


class Dict(dict):
    @staticmethod
    def getDict(obj):
        dict = Dict()
        dict.__dict__.update(obj)
        return dict

    def __init__(self):
        pass

def getConfigFromDict(dict):
    return StripTemplate.StripTemplate(_dict_to_object(dict))


def _dict_to_object(dict_obj):
    return Dict.getDict(dict_obj)


def getDictFromFile(file):
    '''

    :param file:
    :return: dict object
    '''
    try:
        with open(file, 'r') as load_f:
            loadDict = load(load_f)
        # print(loadDict)
    except IOError:
        return None
    # load_dict['line'] = [8200,{1:[['Python',81],['shirt',300]]}]
    return loadDict
