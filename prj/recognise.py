import const

DEBUG_STRIP = False

def checkShape(shape):
    return shape[0]<const.VALID_MAX_Y and shape[0]>const.VALID_MIN_Y and shape[1]<const.VALID_MAX_X and shape[1]>const.VALID_MIN_X

def recognise( gray, regions):
    if DEBUG_STRIP:
        i=0
    for region in regions:
        if DEBUG_STRIP:
            i+=1
            if i!=2 : continue
        region.readStrip(gray )