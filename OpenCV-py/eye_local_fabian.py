import operator
import numpy as np
import math
import cv2
import imutils

kGradientThreshold = 10.0
kWeightBlurSize = 5
maxEyeSize=8

def computeGradient(img):
    out = np.zeros((img.shape[0],img.shape[1]),dtype=np.float32) #create a receiver array
    if img.shape[0] < 2 or img.shape[1] < 2: # TODO I'm not sure that secure out of range
        print("EYES too small")
        return out
    for y in range(0,out.shape[0]):
        out[y][0]=img[y][1]-img[y][0]
        for x in range(1,out.shape[1]-1):
            out[y][x]=(img[y][x+1]-img[y][x-1])/2.0
        out[y][out.shape[1]-1]=img[y][out.shape[1]-1]-img[y][out.shape[1]-2]
    return out



def testPossibleCentersFormula(x, y, weight, gx, gy, out):
    for cy in range(0,out.shape[0]):
        for cx in range(0,out.shape[1]):
            if x==cx and y==cy :
                continue
            dx= x-cx
            dy= y-cy
            magnitude= math.sqrt(dx*dx+dy*dy)
            dx=dx/magnitude
            dy=dy/magnitude
            dotProduct=dx*gx+dy*gy
            dotProduct=max(0.0, dotProduct)
            out[cy][cx]+=dotProduct*dotProduct*weight[cy][cx]


def findEyeCenter(eyeImg, offset):
    # frame = cv2.imread("Eye.jpg")
    # #frame = imutils.resize(frame, width=450)
    # eyeImg = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    # eyeImg = eyeImg.astype(np.float32)
    #eyeImg=eyeImage
    scaleValue=1.0
    if(eyeImg.shape[0]>maxEyeSize or eyeImg.shape[0]>maxEyeSize ):
        scaleValue=max(maxEyeSize/float(eyeImg.shape[0]),maxEyeSize/float(eyeImg.shape[1]))
        eyeImg=cv2.resize(eyeImg,None, fx=scaleValue,fy= scaleValue, interpolation = cv2.INTER_AREA)

    gradientX= computeGradient(eyeImg)
    gradientY= np.transpose(computeGradient(np.transpose(eyeImg)))
    gradientMatrix=matrixMagnitude(gradientX, gradientY)

    gradientThreshold=computeDynamicThreshold(gradientMatrix,kGradientThreshold)
    #Normalisation
    for y in range(0,eyeImg.shape[0]):  #Iterate through rows
        for x in range(0,eyeImg.shape[1]):  #Iterate through columns
            if(gradientMatrix[y][x]>gradientThreshold):
                gradientX[y][x]=gradientX[y][x]/gradientMatrix[y][x]
                gradientY[y][x]=gradientY[y][x]/gradientMatrix[y][x]
            else:
                gradientX[y][x]=0.0
                gradientY[y][x]=0.0

    #Invert and blur befor algo
    weight = cv2.GaussianBlur(eyeImg,(kWeightBlurSize,kWeightBlurSize),0)
    for y in range(0,weight.shape[0]):  #Iterate through rows
        for x in range(0,weight.shape[1]):  #Iterate through columns
            weight[y][x]=255-weight[y][x]

    outSum = np.zeros((eyeImg.shape[0],eyeImg.shape[1]),dtype=np.float32) #create a receiver array
    for y in range(0,outSum.shape[0]):  #Iterate through rows
        for x in range(0,outSum.shape[1]):  #Iterate through columns
            if(gradientX[y][x]==0.0 and gradientY[y][x]==0.0):
                continue
            testPossibleCentersFormula(x, y, weight, gradientX[y][x], gradientY[y][x], outSum)

    #scale all the values down, basically averaging them
    numGradients = (weight.shape[0]*weight.shape[1])
    out= np.divide(outSum, numGradients*10)
    #cv2.imshow("eyeGradient", out)
    #cv2.circle(eyeImg, (81, 34), 1, (0, 0, 255), -1)
    #cv2.imshow("frame", eyeImg)
    #find maxPoint
    (minval, maxval,mincoord,maxcoord) = cv2.minMaxLoc(out)
    maxcoord=(int(maxcoord[0]/scaleValue),int(maxcoord[1]/scaleValue))
    #return tuple(map(operator.add, maxcoord, offset))
    #print(maxcoord)
    return maxcoord



def matrixMagnitude(gradX,gradY):
    mags = np.zeros((gradX.shape[0],gradX.shape[1]),dtype=np.float32) #create a receiver array
    for y in range(0,mags.shape[0]):
        for x in range(0,mags.shape[1]):
            gx=gradX[y][x]
            gy=gradY[y][x]
            magnitude=math.sqrt(gx*gx+gy*gy)
            mags[y][x]=magnitude
    return mags


def computeDynamicThreshold(gradientMatrix,DevFactor ):
    (meanMagnGrad, meanMagnGrad) = cv2.meanStdDev(gradientMatrix)
    stdDev=meanMagnGrad[0]/math.sqrt(gradientMatrix.shape[0]*gradientMatrix.shape[1])
    return DevFactor*stdDev+meanMagnGrad[0]



