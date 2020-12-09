import json
import StripTemplate

def __loadFromFile( code ):
    try:
        with open("./config/strip"+code+".json",'r') as load_f:
            loadDict = json.load(load_f)
        # print(loadDict)
    except IOError:
        return None
    # load_dict['line'] = [8200,{1:[['Python',81],['shirt',300]]}]
    return StripTemplate.StripTemplate(loadDict)

def loadTemplate(category):
    return __loadFromFile(category)
