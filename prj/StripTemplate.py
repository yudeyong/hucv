import findHeaders as header
import findTails as tail

THRESHOLD = 130

# rgb to gray value: None or R,G,B to gray value: 0x1 r, 0x100 g, 0x10000 b
RGB_GRAY = 0x10000

class StripTemplate:

    def __init__(self, jsonDic):
        self.name = jsonDic['name']
        self.references = []
        self.titles = []
        self.RGB_GRAY = jsonDic['RGB_GRAY']
        self.THRESHOLD = jsonDic['THRESHOLD']
        array = jsonDic['lines']
        posi = 0
        for line in array:
            if line[0]!='blank':
                self.references.append( (posi, posi+line[1]) )
                self.titles.append(line[0])
            posi += line[1]
        self.references.append((posi, posi))
        self.titles.append("tail")
        self.persentage = [0.0] * len(self.references)

    # side offset 0:起点 1:终点
    def setPercentage(self, fromIndex, side):
        offset = self.references[fromIndex][side]
        length = self.references[len(self.references)-1][1] - offset
        # 先乘2, 循环时就可以少除1个2了
        # length <<= 1
        i = len(self.references)
        fromIndex += side
        while (i>fromIndex):
            i -= 1
            self.persentage[i] = ( (self.references[i][0]-offset)/length, (self.references[i][1]-offset)/length)
        # while i>0:
        #     i -= 1
        #     self.persentage[i] = (0.0,0.0)

        return self.persentage[i:-1]

    def findHeader(self, src):
        return header.findHeader(src, self.RGB_GRAY, self.THRESHOLD)

    def findTails(self, src):
        THRESHOLD = 205
        return tail.findTails(src, THRESHOLD)
