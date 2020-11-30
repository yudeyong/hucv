import utils

class StripRegion:
    def __init__(self, points):
        self.points = points
        self.slopes = [2]*2
        self.slopes[0] = utils.getSlopeBias(points[0], points[1])
        self.slopes[1] = utils.getSlopeBias(points[2], points[3])

    def