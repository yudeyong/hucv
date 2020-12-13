import cv2
import numpy as np
import utils
import SampleLine as sl
import const
import SlidingWindow as sw
import StripTemplate as st
import math

DEBUG_SR = not False
DEBUG_LINE =  False

DEBUG_STRIP = not False



class StripRegion:
    FIRST_LINE_WIDTH = 3
    FIRST_LINE_THRESHOLD = ((FIRST_LINE_WIDTH+1)>>2)*sl.SAMPLING_LINES*0xff

    SAMPLING_WIDTH = const.SAMPLING_WIDTH * st.X_TIMES
    STRIP_HEIGHT = const.STRIP_HEIGHT * st.Y_TIMES
    def __init__(self, header, template):
        self.header = header
        self.midHeader = utils.mid2PBy4P(header)

        self.slope,self.bias = utils.getSlopeBiasBy2P(self.midHeader[0],self.midHeader[1])
        self.cosReciprocal =  utils.getCosReciprocalBy2P(self.midHeader[0],self.midHeader[1])
        self.template = template
        self.samples = []
        self.valueAndPosi = []
        self.funcLine = None
        self.midFuncLine = None
        self.validPos = 0
        self.scale = 1.0

    @staticmethod
    def recognise(gray, regions):
        if DEBUG_STRIP:
            i = 0
        for region in regions:
            if not region.funcLine :
                continue
            region.searchCutOff(gray)
            if DEBUG_STRIP:
                region.drawFullLineDebug()
                i += 1
                # region.__drawAllDebug()
                # if i != 2: continue

    def __getDeltaMax( self, data, left, right ):
        i = right
        maxD = 0
        maxI = left
        while i>left:
            i -= 1
            if data[i]>maxD:
                maxD = data[i]
                maxI = i
        return (maxD, maxI)

    def __getDeltaMin(self , data, left, right):
        i = left
        minD = 0
        minI = right
        while i<right :
            if data[i]<minD:
                minD = data[i]
                minI = i
            i+=1
        return (minD, minI)


    def searchCutOff(self, gray):
        #init img
        self.img = gray
        # self.__getBkColor()
        # cv2.imshow("bg", gray)
        rect = self.__getTestRegion(2)
        # listP[n]:[leftX, rightX, y]
        listP, rangeP = self.__derivative( rect)
        if None is listP: return None, "miss out cut off"
        mid = len(rangeP) >> 1
        self.cutoff = sl.SampleLine.getValue(gray, listP[1:-1],rangeP[mid])
        print("cutoff,",self.cutoff)
        mid = (listP[1][0]+listP[-1][0])>>1



        x = rect[0]
        x1 = rect[2]
        img = gray[rect[1]:rect[3], x:x1]
        # img[listP[-1][2]:listP[0][2], x:x1] = 0
        # cv2.imshow("bb", img)
        # cv2.waitKey()
        return self.lastRegion

    def __findMargin(self, img, fY0):
        '''
        扫描灰度图, 查找采样线
        :param img:
        :param fY0: y轴
        :return: x,width
        '''
        length = i = img.shape[1] - 1

        fY = fY0
        top = img.shape[0]
        #一阶导数
        delta = [0] * i
        minD = maxD = 0
        minI = maxI = 0
        i -= 2
        while i>1:
            fY -= self.slope
            y = round(fY)
            if (y>=top) :
                break
            delta[i] = (int(img[y][i+1])-img[y][i])
            if delta[i]>maxD:
                tmpD = (int(img[y][i-1])-img[y][i])
                if ( delta[i+1]>=0 ) or ((-delta[i+1])<<1)<=delta[i] or tmpD<0 or ((tmpD)<<1)<=delta[i] :
                    maxD = delta[i]
                    maxI = i
                    maxY = y
            elif delta[i]<=minD:
                tmpD = (int(img[y][i-1])-img[y][i])
                if ( delta[i+1]>=0 ) or (delta[i+1]<<1)>=delta[i] or tmpD<0 or (tmpD<<1)<=delta[i] :
                    minD = delta[i]
                    minI = i
                    minY = y
                # delt = delta
                # delt[i] <<= 3
                # if (delt[i]>255) : delt[i] = 255
                # delt[i] = 255 - delt[i]
                # img[y+10][i] = delt[i]
            #跳过0不检测
            i -= 1

        if (maxI < minI):
            maxTmp, maxTmpI = self.__getDeltaMax(delta, minI, length)
            minTmp, minTmpI = self.__getDeltaMin(delta, 0, maxI)
            if maxD - maxTmp > minD - minTmp:
                maxY = round(fY0 + (maxTmpI - maxI) * self.slope)
                maxI = maxTmpI
            else:
                minY = round(fY0 + (minTmpI - minI) * self.slope)
                minI = minTmpI
        elif maxI+minI==0:
            return None, None
        # print(delta)
        # print(minI, maxI)
        # cv2.line(img, (minI,minY),(maxI,maxY),0xff,2)
        # utils.drawRectBy2P(img, (minI,minY-(StripRegion.STRIP_HEIGHT>>2),maxI, maxY+(StripRegion.STRIP_HEIGHT>>2)))
        return minI, maxI

    # def findMarge(self, ):
    def __derivative(self, rect):
        gray = self.img
        x = rect[0]
        x1 = rect[2]
        img = gray[rect[1]:rect[3], x:x1]
        # _, bw = cv2.threshold(img, self.bgColor, 255.0, cv2.THRESH_BINARY)
        # canny = utils.toCanny(bw, 5)
        # cv2.imshow("bg", canny)
        # cv2.waitKey()


        x = rect[3]-rect[1] # assert x == StripRegion.STRIP_HEIGHT*2
        # length = i = x1-x-1
        fY = x-1#x1 * self.slope + self.bias + (StripRegion.STRIP_HEIGHT>>1)
        x1 = StripRegion.STRIP_HEIGHT>>3

        listP = []
        i = 0
        rangeP = []
        leftP = np.zeros((16),dtype=int)
        l = StripRegion.SAMPLING_WIDTH - (const.SAMPLING_WIDTH >> 1)
        r = StripRegion.SAMPLING_WIDTH + (const.SAMPLING_WIDTH>>1)
        j = 0
        while x>0:
            left,right =  self.__findMargin(img, fY)
            width = right-left
            x -= x1
            if not left:
                fY -= x1
                continue
            listP.append([ left, right, fY])
            if width<=r and width>=l:
                leftP[j] = left
                j += 1
                rangeP.append(i)
            i += 1
            fY -= x1

        leftP = StripRegion.__filteringAnomaly(leftP[:j], rangeP)
        StripRegion.__filteringAnomaly(leftP, rangeP)
        StripRegion.__findMaxWin(rangeP, 9)
        if l>=3:
            listP = np.asanyarray( listP[rangeP[0]:rangeP[-1]+1] )
            i = len(rangeP)
            x1 = rangeP[0]
            while i>0:
                i -= 1
                x = rangeP[i] - x1
                rangeP[i] = x
                j = listP[x]
                # cv2.line(img, (j[0], int(j[2])), (j[1] , int(j[2])), (0, 0, 0), 2)
                # print("lines,",i[0],i[1],i[2])
            listP[:,0] += rect[0]+1
            listP[:,1] += rect[0]-1
            listP[:,2] += rect[1]
            # print("ran,",rangeP)
            return listP, rangeP

        else: return None,None

    @staticmethod
    def __findMaxWin(data, size):
        i = j = len(data)-1
        if data[j] - data[0]<size: return j
        maxLen = 1
        maxPos = i

        while i>0:
            while data[j]-data[i]<size:
                if i>0:
                    i -= 1
                else:
                    i = -1
                    break
            if data[j]-data[i+1]<size :
                dist = j-i
                # 跨度(Y轴)相同时, 越紧密越优先
                if dist>maxLen or (dist==maxLen and minDelta>data[j])-data[i+1]:
                    maxLen = dist
                    maxPos = i + 1
                    minDelta = data[j]-data[maxPos]
                j -= 1

        del data[maxPos+maxLen:]
        del data[:maxPos]
        return maxLen

    @staticmethod
    def __filteringAnomaly( data, list):
        index = StripRegion.__two_sigma(data)
        data = np.delete(data, index)
        i = len(index)
        while i>0:
            i -= 1
            del list[index[i]]
        return data

    # 定义3σ法则识别异常值函数
    @staticmethod
    def __two_sigma(Ser1):
        '''
        Ser1：表示传入DataFrame的某一列。
        '''
        rule = (Ser1.mean() -  2 * Ser1.std() > Ser1) | (Ser1.mean() + 2 * Ser1.std() < Ser1)
        index = np.arange(Ser1.shape[0])[rule]
        return index

    def __getTestRegion(self, index):
        x2 = self.midHeader[0][0]+self.scale * self.template.references[index+1][0] - StripRegion.SAMPLING_WIDTH
        x1 = self.lastRegion[1][0]+ StripRegion.SAMPLING_WIDTH
        y2 = x2 * self.slope + self.bias
        y1 = self.lastRegion[1][1]
        y1 = min(y1, y2-StripRegion.STRIP_HEIGHT)
        if y1<0: y1 = 0
        y2 = max(self.lastRegion[3][1], y2+StripRegion.STRIP_HEIGHT)
        return (x1,int(y1),int(x2),int(y2))

    def __drawAllDebug(self):
        for p in self.template.references :
            x = self.midHeader[0][0]+self.scale * p[0]
            y = round(x * self.slope + self.bias)
            self.__setSymbleDebug(round(x), round(self.midHeader[0][0]+self.scale*p[1]), y)

    def __setFuncLine(self, f):
        self.funcLine = f
        self.midFuncLine = utils.mid2PBy4P(f)
        self.scale = self.template.getScale( 0, 1, self.midFuncLine[1][0] - self.midHeader[0][0] + 1 )
        self.lastRegion = f
        self.lastMid = self.midFuncLine

        #assert(scale between 9.42, 8.8)
        # print(self.scale)

    def matchFuncLine(self, funcLines):
        i = len(funcLines)
        x = self.midFuncLine[0] if self.midFuncLine else 0x7fff
        while i > 0:
            i -= 1
            f = funcLines[i]
            if f[0][0] >= x: continue
            y = f[0][0] * self.slope + self.bias
            if y>f[0][1] and y<f[2][1]:
                self.__setFuncLine( f )
                del funcLines[i]
                return True
        return self.midFuncLine!=None

    def __sampling(self, i, data, lastSample):
        # t1 = t+b-(b*t)/0xff
        b = self.bgColor
        # threshold = sl.WHITE_THRESHOLD#+self.bgColor
        threshold = round(sl.WHITE_THRESHOLD_BASE + b - b* sl.WHITE_THRESHOLD_BASE/0xff)*sl.SAMPLING_LINES
        total = np.sum(data)
        if (total < threshold):
            if lastSample[0] != i - 1:
                sample = sl.SampleLine(data, i)
                self.samples.insert(0,sample)
            else:
                self.samples[0].add(data, i)
            lastSample[0] = i

    def __getBkColor(self):
        gray = self.img
        colors = [[0,0]  for i in range(16)]

        x = max(self.header[1][0],self.header[3][0])
        x1 = min(self.funcLine[0][0], self.funcLine[2][0])
        y = max(self.header[1][1],self.funcLine[0][1])-1
        y1 = min(self.header[3][1], self.funcLine[2][1])+1
        while y<y1:
            while x<x1:
                d = gray[y][x]
                r = colors[d>>4]
                r[0] += 1
                r[1] += d
                x += 1
            y+=1

        maxColorIndex = colors.index(max(colors, key=lambda x: x[0]))
        self.bgColor = round(colors[maxColorIndex][1] / colors[maxColorIndex][0])
        print("bgColor:",self.bgColor)
        # gray[max(self.header[1][1],self.funcLine[0][1]):y1, max(self.header[1][0],self.header[3][0]):x1] = 0

    def drawFullLineDebug(self):
        if self.midFuncLine :
            k, b = utils.getSlopeBiasBy2P(self.midHeader[0], self.midFuncLine[1])
            # utils.drawFullLine(self.img, self.midHeader[0], k, b, 0)
            pass
        # self.getValuesByPostion(gray)

        return

    def __setSymbleDebug(self, x1, x2, y):
        self.img[y:y + 6, x1:x2+1] = 0
        self.img[y + 2:y + 3, x1:x2+1] = 0xff

    ############  deprecated  ###########
    # counter = 0

    def getValuesByPostion(self, img):
        percent = self.template.setPercentage(1, 0)
        # cv2.line(gray, (self.left, self.top), (self.right, self.bottom), (0,0,255), 1)
        # cv2.line(gray, (self.left, self.bottom), (self.right, self.top), (0,0,255), 1)
        # self.firstLine = self.left +15

        # StripRegion.counter+=1
        # if (StripRegion.counter!=3) :return

        win = sw.SlidingWindgow(const.SAMPLING_WIDTH)
        length = self.right - self.left

        i = 0
        for p in percent:
            if DEBUG_LINE:
                i += 1
                if (i>2 and i!=13 and i!=14) : pass#continue
                elif i>2:
                    i=i
            x = self.firstLine + p[0]*length -const.SAMPLING_WIDTH
            y = int(x*self.slope + self.bias)
            x = round(x)
            colorValue,offsetx = sl.SampleLine.getValue(img[y-const.SAMPLING_MINUS_Y_OFFSET:y+const.SAMPLING_Y_OFFSET,
                                x:x+(const.SAMPLING_WIDTH<<2) ], win)
            offsetx += x
            self.__setSymbleDebug(img,int(x), x+(const.SAMPLING_WIDTH<<2), y-12 )
            self.__setSymbleDebug(img,int(offsetx),int(offsetx+const.SAMPLING_WIDTH), y )
            colorValue = self.__removeBgColor(colorValue)
            self.valueAndPosi.append([colorValue, 0.0, 0,offsetx])

        if not DEBUG_LINE:
            if (len(self.valueAndPosi)<len(percent)):
                return -1
        print('************ new strip *************')
        self.__setProcessValue()
        # cv2.imshow("bb", img)
        # cv2.waitKey()

    def __setProcessValue(self):
        cutOff = 0xff-self.valueAndPosi[1][0]
        if cutOff==0:
            return -2
        for v in self.valueAndPosi:
            v[1] = StripRegion.__funcValue((0xff-v[0]) / cutOff)
            v[2] = StripRegion.__setQualitative(v[1])
            if DEBUG_SR :
                print("{:.2f}".format(v[1]), ',', end='')
        if DEBUG_SR :
            print()
            for v in self.valueAndPosi:
                print(v[2], ',', end='')
            print()

    @staticmethod
    def __setQualitative(v):
        # v = math.sqrt(v)
        if False:
            if v<0.2 : return -2
            if v<0.8 : return -1
            if v<1.15 : return 0
            if v<2.5 : return 1
            if v<4 : return 2
            return 3
        else:
            if v<0.2 : return ''
            if v<0.8 : return '-'
            if v<1.15 : return 'o'
            if v<2.5 : return '+'
            if v<4 : return '++'
            return '+++'

    @staticmethod
    def __funcValue(v):
        return v
        return math.sqrt(v) if not DEBUG_LINE  else v
