import numpy as np

class SlidingWindgow:
    def __init__(self, width):
        self.width = width
        self.summary = np.zeros([width])

    def initData(self, data):
        self.data = data.copy()
        i = data.shape[0]
        assert(i,self.width)
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