import json
import StripTemplate

class Dict(dict):
    def __init__(self, obj):
        self.__dict__.update(obj)

def _loadFromFile( code ):
    try:
        with open("./config/strip"+code+".json",'r') as load_f:
            loadDict = json.load(load_f)
        # print(loadDict)
    except IOError:
        return None
    # load_dict['line'] = [8200,{1:[['Python',81],['shirt',300]]}]
    config = _dict_to_object(loadDict)
    return StripTemplate.StripTemplate(config)



def _dict_to_object(dict_obj):
    res = Dict(dict_obj)
    return res

def loadTemplate(category):
    return _loadFromFile(category)
