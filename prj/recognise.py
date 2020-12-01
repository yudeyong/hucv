import const
import utils

def checkShape(shape):
    return shape[0]<const.VALID_MAX_Y and shape[0]>const.VALID_MIN_Y and shape[1]<const.VALID_MAX_X and shape[1]>const.VALID_MIN_X

def recognise( gray, bw, regions):
    for region in regions:
        region.readStrip(gray, bw )