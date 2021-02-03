class Result:

    def __init__(self, index):
        '''

        :param index: 下标
        : param stand: 标准值
        '''
        self.index = index
        self.results = []
        self.values = []

    def appendValue(self, value, stand):
        v = (255 - value) / stand
        self.values.append(v)
        self.results.append(Result._setQualitative(v))
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
            if v < 0.2: return ''
            if v < 0.8: return '-'
            if v < 1.15: return 'o'
            if v < 2.5: return '+'
            if v < 4: return '++'
            return '+++'
