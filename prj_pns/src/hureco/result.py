class Result:

    def __init__(self, index, stripRegion):
        '''

        :param index: 下标
        : param stand: 标准值
        '''
        self.index = index #下标
        self.results = [] # 阳性, 加号
        self.values = [] # 检测值/标准值
        self.stripRegion = stripRegion # 膜条区域
        self.detectiveRegion = [] # 监测区域

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
