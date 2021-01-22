import numpy as np

class SlidingWindow:
    def __init__(self, width):
        self.setWidth(width)

    def setWidth(self, width):
        if not hasattr(self, "width") or self.width!=width:
            self.summary = np.zeros([width])
        self.width = width


    def initData(self, data, rotate):
        '''
        初始化数据 安装init中设置的width
        :param data:
        :param rotate: 是否旋转
        :return: 无
        '''
        if rotate:
            data = data[:,:self.width]
            data = np.swapaxes(data, 0, 1)
        else: data = data[:self.width,:]
        self.data = data.copy()
        i = data.shape[0]
        while i>0:
            i -= 1
            self.summary[i] = np.sum(data[i])
        self.total = np.sum(self.summary)

    def append(self, dataLine):
        self.data[:self.width-1] = self.data[1:]
        self.data[self.width-1] = dataLine

        total = self.total - self.summary[0]
        self.summary[:self.width-1] = self.summary[1:]

        sum = np.sum(dataLine)
        self.summary[self.width-1] = sum
        self.total = total + sum
        return self.total