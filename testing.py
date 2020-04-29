import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import tifffile as tiff

# http://layer0.authentise.com/detecting-circular-shapes-using-contours.html

raw_image = tiff.imread("temp_img.tif")
norm_image = raw_image/np.max(raw_image)
# row,col = norm_image.shape
# fig = plt.figure(1)
# ax = fig.add_subplot(111)
# bp = ax.boxplot(norm_image.reshape((row*col,1)))

# raw_image = cv2.imread('temp_img.tif')
# cv2.imshow('Original Image', raw_image/np.max(raw_image))
# cv2.waitKey(0)

bilateral_filtered_image = cv2.bilateralFilter(norm_image.astype('float32'), 25, 400, 400)
# cv2.imshow('Bilateral', bilateral_filtered_image)
# cv2.waitKey(0)

# edge_detected_image = cv2.Canny(bilateral_filtered_image, 75, 200)
# cv2.imshow('Edge', edge_detected_image)
# cv2.waitKey(0)

ret, masked_image = cv2.threshold(bilateral_filtered_image,np.quantile(norm_image,.97),1,cv2.THRESH_BINARY)
# cv2.imshow('Masked Image', masked_image)
# cv2.waitKey(0)
titles = ['Raw','Normalized','Bilateral','Masked']
images = [raw_image,norm_image,bilateral_filtered_image,masked_image]
plt.figure(figsize=(8,8))
for i in range(4):
    plt.subplot(2,2,i+1)
    plt.imshow(images[i],interpolation='nearest')
    plt.title(titles[i])
    plt.xticks([])
    plt.yticks([])
plt.show()

contours, hierarchy = cv2.findContours(masked_image.astype('uint8'),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
cv2.drawContours(raw_image, contours, -1, (255,255,255), 2)

centroids = list()
for cnt in contours:
    (x,y),radius = cv2.minEnclosingCircle(cnt)
    if cv2.contourArea(cnt) < 8000 and cv2.contourArea(cnt) > 1000 and cv2.contourArea(cnt) > (3.14*radius*radius*0.5):
        print("Cell Detected")
        cv2.drawContours(norm_image, cnt, -1, (100,140,204), 3)
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        centroids.append([cx, cy])
cv2.imshow('Contours', norm_image) 
cv2.waitKey(0) 
cv2.destroyAllWindows()
print('Num Centroids =', len(centroids))
