import cv2
import numpy as np
import utils
import SampleLine as sl
import const
import SlidingWindow as sw
import StripTemplate as st
import math

DEBUG_SR = not False
DEBUG_LINE = not False

DEBUG_STRIP =  False and DEBUG_SR
DEBUG_DRAW_ALL =  False and DEBUG_SR


class StripRegion:
    FIRST_LINE_WIDTH = 3
    FIRST_LINE_THRESHOLD = ((FIRST_LINE_WIDTH+1)>>2)*sl.SAMPLING_LINES*0xff

    SAMPLING_WIDTH = const.SAMPLING_WIDTH * st.X_TIMES
    STRIP_HEIGHT = const.STRIP_HEIGHT * st.Y_TIMES
    def __init__(self, listP, index, size, slope, fcX, y, INTERVAL, STRIP_WIDTH, LINES, STRIP_AREA_WIDTH):
        #找中点
        index = index + (size >> 1)
        if size&1==0:
            #下标大的
            self.midX = listP[index][2][0] if listP[index][1] >= listP[index + 1][1] else listP[index+1][2][0]
            #均值
            self.midY = (listP[index][1] + listP[index + 1][1] )>>1
        else:
            self.midX = listP[index][2][0]
            self.midY = listP[index][1]
        self.slope = slope
        self.fcX = fcX
        self.top = fcX*slope+y
        self.INTERVAL = INTERVAL
        self.STRIP_WIDTH = STRIP_WIDTH
        self.lines = LINES
        self.STRIP_AREA_WIDTH = STRIP_AREA_WIDTH
        self.samples = []

    @staticmethod
    def checkFunctionLineX( img, y, FUNC_LINE,STRIP_WIDTH):
        y = int(y)
        STRIP_WIDTH = STRIP_WIDTH-1-(STRIP_WIDTH>>2)
        # utils.drawRectBy2P(src, (FUNC_LINE[0], y+FUNC_LINE[1], FUNC_LINE[2], y+FUNC_LINE[3]))
        src = img[y+FUNC_LINE[1]:y+FUNC_LINE[3], FUNC_LINE[0]:FUNC_LINE[2]]

        minValue = STRIP_WIDTH*src.shape[0]*255
        win = sw.SlidingWindow(STRIP_WIDTH)

        win.initData(src, True)
        i = STRIP_WIDTH
        x = i
        i1 = src.shape[1]
        while True:
            if minValue>win.total:
                minValue = win.total
                x = i
            if i >= i1: break;
            win.append(src[:, i])
            i += 1

        if minValue/(STRIP_WIDTH*src.shape[0])<200.0: return x+FUNC_LINE[0]-STRIP_WIDTH-1
        else: return -1
        # print(minValue/(STRIP_WIDTH*src.shape[0]))
        return x

    def getFunctionLineY(self, img):

        #开始处理Y
        #检测窗口高度
        HEIGHT = 9
        marginTop = int(self.top) - HEIGHT
        if marginTop<0: marginTop = 0

        marginBottom = int(self.top+self.INTERVAL)+HEIGHT
        if marginBottom>=img.shape[0] : marginBottom = img.shape[0]

        data = img[marginTop:marginBottom,self.fcX+3:self.fcX+self.STRIP_WIDTH-3]
        # data[:,:] = 0
        # assert data.shape[0]>HEIGHT
        win = sw.SlidingWindow(HEIGHT)

        win.initData(data, False)

        i1 = data.shape[0]
        oldValue = [0]*HEIGHT
        minValue = maxValue = 0
        minX = maxX = i = HEIGHT-1
        maxBorder = ((i1+i)>>1)
        minBorder = maxBorder
        maxBorder += 3
        oldValue[0] = win.total
        recordCursor = 0
        while recordCursor<HEIGHT:
            oldValue[recordCursor] = win.total
            recordCursor += 1
            i += 1
            win.append(data[i])
        recordCursor = 0
        while True:
            delta = win.total-oldValue[recordCursor]
            if i<minBorder and minValue > delta:
                minValue = delta
                minX = i
            if i>maxBorder and maxValue < delta:
                maxValue = delta
                maxX = i
            i += 1
            if i >= i1: break;
            oldValue[recordCursor] = win.total
            recordCursor += 1
            if recordCursor>=HEIGHT:
                recordCursor = 0
            win.append(data[i])
        if  True:
            self.fcY1 = maxX-HEIGHT+marginTop
            self.fcY0 = minX-HEIGHT+marginTop
        else:
            self.fcY0 = marginTop
            self.fcY1 = y+FUNC_LINE[3]+HEIGHT
        # img[self.fcY0:self.fcY1, self.fcX:self.fcX+STRIP_WIDTH]=0
        return

    def recognise(self, gray):

        if DEBUG_STRIP:
            i = 0
        for line in self.lines:
            x = self.fcX+line[0]
            deltaY = x*self.slope
            utils.drawRectBy2P(gray, (int(x), int(self.fcY0+deltaY),
                                      int(self.fcX + line[1]), int(self.fcY1+deltaY)))

    @staticmethod
    def __getDeltaMax( data, left, right ):
        i = right
        maxD = 0
        maxI = left
        while i>left:
            i -= 1
            if data[i]>maxD:
                maxD = data[i]
                maxI = i
        return (maxD, maxI)

    @staticmethod
    def __getDeltaMin( data, left, right):
        i = left
        minD = 0
        minI = right
        while i<right :
            if data[i]<minD:
                minD = data[i]
                minI = i
            i+=1
        return (minD, minI)

    def __analysis(self, img):
        #init img
        self.img = img
        err = self.searchCutOff()
        if DEBUG_LINE: self.drawFullLineDebug()
        if err:
            return err
        for i in range(len(self.template.sampleRef)) :
            self.searchSampleLine(i)


    def searchSampleLine(self,i):
        ref = self.template.sampleRef[i]
        rect = self.__getTestRegion(self.scale *ref[0]-StripRegion.SAMPLING_WIDTH,self.scale * ref[1]+StripRegion.SAMPLING_WIDTH)
        listP, rangeP = self.__derivative(rect)
        if None is listP: return None


        self.values[i] = 0xff-sl.SampleLine.getValue(self.img, listP,rangeP)
        print(i,"v:",(self.values[i])/(self.cutoff), self.cutoff,self.values[i])

        self.__updateSlopeBias(listP, self.values[i])

    def __updateSlopeBias(self, listP, v):
        if v*2<self.cutoff :return
        if DEBUG_DRAW_ALL:
            self.__drawAllDebug()
            cv2.imshow("bb", self.img)
            cv2.waitKey()
            pass
        if len(listP)==9 and (listP[0][1]-listP[0][0])==(listP[-1][1]-listP[-1][0]):
            #精确定位
            line = ((listP[0][1],listP[0][2]),(listP[-1][1],listP[-1][2]))
            mid = (line[0][0]+line[1][0])>>1,(line[0][1]+line[1][1])>>1
            # self.scale = self.template.getScale(0, 2, mid[0] - self.midHeader[0][0] + 1)
            self.points.append(mid)
            self.points.append(mid)
            self.__getFitLine()
            # self.slope,self.bias = utils.getSlopeBiasBy2P(self.midHeader[0], mid)
            if DEBUG_DRAW_ALL: self.__drawAllDebug()

            if DEBUG_STRIP: print("perfect cutline & scale:", self.scale)
        else:
            # index = StripRegion.__two_sigma(listP[:,1])
            # listP = np.delete(listP, index,axis=1)
            mid = listP[0][2]-listP[-1][2]
            if mid<=32 and mid>=28:
                line = ((listP[0][1], listP[0][2]), (listP[-1][1], listP[-1][2]))
                x = line[0][0]+line[1][0]>>1
                y = self.slope*(x)+self.bias
                y1 = y-((line[0][1]+line[1][1])>>1)
                if abs(y1)>0.5 :
                    y1 = 0.5 if y1>0 else -0.5
                y1 += y
                mid =  x,y1
                self.slope,self.bias = utils.getSlopeBiasBy2P(self.midHeader[0], mid)
                if DEBUG_DRAW_ALL: self.__drawAllDebug()

            if DEBUG_STRIP:
                print("cutline",len(listP),(listP[0][1]-listP[0][0],(listP[-1][1]-listP[-1][0])))
                pass
        if DEBUG_LINE: self.drawFullLineDebug()
        cv2.imshow("bb", self.img)
        cv2.waitKey()


    def searchCutOff(self):

        rect = self.__getTestRegion(self.funcLine[1][0]-self.midHeader[0][0]+ StripRegion.SAMPLING_WIDTH,self.scale * self.template.references[2+1][0] - StripRegion.SAMPLING_WIDTH)
        # listP[n]:[leftX, rightX, y]
        listP, rangeP = self.__derivative( rect)
        if None is listP: return "miss out cut off"

        self.cutoff = 0xff-sl.SampleLine.getValue(self.img, listP,rangeP)
        if DEBUG_STRIP:print("cutoff,",self.cutoff)

        self.__updateSlopeBias(listP, self.cutoff)

        x = rect[0]
        x1 = rect[2]
        # img = gray[rect[1]:rect[3], x:x1]
        # img[listP[-1][2]:listP[0][2], x:x1] = 0
        # cv2.imshow("bb", self.img)
        # cv2.waitKey()
        return None

    def __findMargin( img, fY0 ,slope):
        '''
        扫描灰度图, 查找采样线
        :param img:
        :param fY0: y轴
        :return: x0, x1
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
            fY -= slope
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
            maxTmp, maxTmpI = StripRegion.__getDeltaMax(delta, minI, length)
            minTmp, minTmpI = StripRegion.__getDeltaMin(delta, 0, maxI)
            if maxD - maxTmp > minD - minTmp:
                maxY = round(fY0 + (maxTmpI - maxI) * slope)
                maxI = maxTmpI
            else:
                minY = round(fY0 + (minTmpI - minI) * slope)
                minI = minTmpI
        elif maxI+minI==0:
            return None, None
        # print(delta)
        # print(minI, maxI)
        # cv2.line(img, (minI,minY),(maxI,maxY),0xff,2)
        # utils.drawRectBy2P(img, (minI,minY-(StripRegion.STRIP_HEIGHT>>2),maxI, maxY+(StripRegion.STRIP_HEIGHT>>2)))
        return minI, maxI
    @staticmethod
    def derivative(gray, rect,slope, bias, stripHeight,stripWidth):
        '''
        针对区域'求导', 确定采样线边界
        :param rect: 监测区域
        :return: 有效区域数组, 数组中有效线
        '''
        stripHeight = int(stripHeight)
        x1 = rect[0]
        x2 = rect[2]
        #clip 处理区域
        img = gray[rect[1]:rect[3], x1:x2]
        # _, bw = cv2.threshold(img, self.bgColor, 255.0, cv2.THRESH_BINARY)
        # canny = utils.toCanny(bw, 5)
        cv2.imshow("bg", img)
        # cv2.waitKey()

        y = rect[3]-rect[1] # assert y == StripRegion.STRIP_HEIGHT*2
        fY = round(x2 * slope + bias - rect[1])
        fY1 = fY - stripHeight+(stripHeight>>4)
        fY += (stripHeight)-(stripHeight>>4)
        yy = fY
        #扫描间距
        x1 = stripHeight>>3

        listP = []
        rangeP = []
        i = 0
        leftP = np.zeros((16),dtype=int)
        l = stripWidth - (stripWidth >> 2)
        r = stripWidth + (stripWidth>>2)
        j = 0
        while fY>fY1:
            left,right =  StripRegion.__findMargin(img, fY, slope)
            if left:
                width = right-left
                y -= x1
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

        if len(rangeP)<5: return None,None
        leftP = StripRegion.__filteringAnomaly(leftP[:j], rangeP, StripRegion.__modeCheck)

        leftP = StripRegion.__filteringAnomaly(leftP, rangeP, StripRegion.__two_sigma)
        if len(rangeP)<5: return None,None
        StripRegion.__filteringAnomaly(leftP, rangeP, StripRegion.__two_sigma)
        if len(rangeP)<5: return None,None
        StripRegion.__findMaxWin(rangeP, 9)
        if len(rangeP)>=5:
            listP = np.asanyarray( listP[rangeP[0]:rangeP[-1]+1] )
            i = len(rangeP)
            x1 = rangeP[0]
            while i>0:
                i -= 1
                # x = rangeP[i] - x1
                rangeP[i] -= x1

                #debug only
                j = listP[rangeP[i]]
                # cv2.line(img, (j[0], int(j[2])), (j[1] , int(j[2])), (0, 0, 0), 2)
                # print("lines,",i[0],i[1],i[2])
            cv2.line(img, (listP[rangeP[0]][0], yy), (listP[rangeP[0]][0], fY1), 0, 1)
            # cv2.line(img, (listP[rangeP[0]][0], yyy), (listP[rangeP[0]][1], yyy), 0, 3)
            listP[:,0] += rect[0]+1
            listP[:,1] += rect[0]-1
            listP[:,2] += rect[1]
            # print("ran,",rangeP)
            return listP, rangeP

        else: return None,None

    @staticmethod
    def __findMaxWin(data, size):
        '''
        查找<=size的连续最大窗口
        相同跨度时,紧凑优先
        多个结果时忽略后续
        :param data:
        :param size:
        :return:
        '''
        i = j = len(data)-1
        if data[j] - data[0]<size: return j
        maxLen = 1
        maxPos = i
        minDelta = 0x7fff

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
    def __filteringAnomaly( data, list, func):
        '''
        过滤噪点, 异常值
        :param data:
        :param list:
        :return:
        '''
        if data.max()-data.min()<=2: return data
        index = func(data)
        data = np.delete(data, index)
        i = len(index)
        while i>0:
            i -= 1
            del list[index[i]]
        return data

    @staticmethod
    def __modeCheck(Ser1):
        c = np.bincount(Ser1)
        # 返回众数
        i = np.argmax(c)
        rule = (i-StripRegion.SAMPLING_WIDTH > Ser1) | (i+StripRegion.SAMPLING_WIDTH < Ser1)
        index = np.arange(Ser1.shape[0])[rule]
        return index

    # 定义3σ法则(实际使用的更严格的2σ,也许多次3σ更好,需要试)识别异常值函数
    @staticmethod
    def __two_sigma(Ser1):
        '''
        Ser1：表示传入DataFrame的某一列。
        '''
        rule = (Ser1.mean() -  2 * Ser1.std() > Ser1) | (Ser1.mean() + 2 * Ser1.std() < Ser1)
        index = np.arange(Ser1.shape[0])[rule]
        return index

    def __getTestRegion(self, x1, x2):
        x2 += self.midHeader[0][0]
        x1 += self.midHeader[0][0]
        y2 = x2 * self.slope + self.bias
        y1 = self.funcLine[1][1]
        y1 = int(min(y1, y2-StripRegion.STRIP_HEIGHT))
        if y1<0: y1 = 0
        y2 = int(max(self.funcLine[3][1], y2+StripRegion.STRIP_HEIGHT))
        # self.img[y1:y2, int(x1):int(x2)] = 0
        # cv2.imshow("bb", self.img[y1:y2,int(x1):int(x2)])
        # cv2.waitKey()
        return (int(x1) ,int(y1),int(x2),int(y2))

    def __drawAllDebug(self):
        for p in self.template.references :
            x = self.midHeader[0][0]+self.scale * p[0]
            y = round(x * self.slope + self.bias)
            self.__setSymbleDebug(round(x), round(self.midHeader[0][0]+self.scale*p[1]), y)

    def __getFitLine(self):
        p = np.asanyarray(self.points)
        out = cv2.fitLine(p, cv2.DIST_L2, 0, 0.01, 0.01)
        k = out[1]/out[0]
        b = out[3] - k * out[2]
        # self.midHeader[0][0] = round((self.midHeader[0][1] - b[0] )/k[0])
        self.slope = k[0]
        self.bias = b[0]

    def __setFuncLine(self, f):
        self.funcLine = f
        self.midFuncLine = utils.mid2PBy4P(f)
        # self.scale = self.template.getScale( 0, 1, self.midFuncLine[1][0] - self.midHeader[0][0] + 1 )
        self.lastMid = self.midFuncLine
        self.points.append(self.midFuncLine[0])
        self.points.append(self.midFuncLine[1])
        self.__getFitLine()

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
            k, b = self.slope, self.bias
            utils.drawFullLine(self.img, (self.midHeader[0][0],self.midHeader[0][1]-StripRegion.STRIP_HEIGHT+5), k, b-StripRegion.STRIP_HEIGHT+5, 0)
            pass
        # self.getValuesByPostion(gray)

        return

    def __setSymbleDebug(self, x1, x2, y):
        self.img[y:y + 6, x1:x2+1] = 0
        self.img[y + 2:y + 3, x1:x2+1] = 0xff

    ############  deprecated  ###########
    # counter = 0

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
