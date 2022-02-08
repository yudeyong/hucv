class Result:

    def __init__(self, stripRegion, detetiveRegion, value, index, strpRegion):
        '''

        :param index: 下标
        : param stand: 标准值
        '''
        self.index = index
        self.results = []
        self.values = []
        self.stripRegion = strpRegion
        self.detectiveRegion = []

    STAND = 38
    def appendValue(self, value, detectiveRegion):
        v = value / Result.STAND
        self.values.append(v)
        self.results.append(Result._setQualitative(v))
        self.detectiveRegion.append(detectiveRegion)
        # print(" ,v=",round(v,2) ,end='')

    @staticmethod
    def _setQualitative(v):
        # v = math.sqrt(v)
        if False:
            if v < 0.2: return -2
            if v < 0.8: return -1
            if v < 1.15: return 0
            if v < 2.5: return 1
            if v < 4: return 2
            return 3
        else:
            if v < 0.4: return ''
            if v < 0.8: return '-'
            if v < 1.0: return 'o'
            if v < 1.9: return '+'
            if v < 2.99: return '++'
            return '+++'
