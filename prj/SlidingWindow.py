import numpy as np

class SlidingWindgow:
    def __init__(self, width, data):
        self.width = width
        self.data = data
        i = data.shape[0]
        assert(i,width)
        self.summary = np.empty([i])
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
        self.total += sum
