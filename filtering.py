import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import tifffile as tiff

raw_image = tiff.imread("4.tif")
norm_image = raw_image/np.max(raw_image)
row,col = norm_image.shape
plt.imshow(norm_image)

sigmaColors = [10,15,20]
sigmaSpaces = [10,15,20]

count = 0
plt.figure(figsize=(8,8))
for i in range(3):
    for j in range(3):
        bilateral_filtered_image = cv2.bilateralFilter(norm_image.astype('float32'), int(.024*row), sigmaColors[i], sigmaSpaces[j])
        ret, masked_image = cv2.threshold(bilateral_filtered_image,np.quantile(norm_image,.97),1,cv2.THRESH_BINARY)
        contours, hierarchy = cv2.findContours(masked_image.astype('uint8'),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
        
        # centroids = list()
        for cnt in contours:
            (x,y),radius = cv2.minEnclosingCircle(cnt)
            if cv2.contourArea(cnt) < 8000 and cv2.contourArea(cnt) > 1000 and cv2.contourArea(cnt) > (3.14*radius*radius*0.5):
                print("Cell Detected")
                cv2.drawContours(norm_image, cnt, -1, (100,140,204), 3)
                M = cv2.moments(cnt)
                cx = int(M['m10']/M['m00'])
                cy = int(M['m01']/M['m00'])
                # centroids.append([cx, cy])

        plt.subplot(3,3,count+1)
        plt.imshow(norm_image,interpolation='nearest')
        title_string = 'C=' + str(sigmaColors[i]) + ' S=' + str(sigmaSpaces[j])
        plt.title(title_string)
        plt.xticks([])
        plt.yticks([])
        count = count + 1
plt.show()