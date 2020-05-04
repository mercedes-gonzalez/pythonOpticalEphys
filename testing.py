import cv2
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import tifffile as tiff
from os import listdir
from os.path import isfile, join
linewidth = 3
import numpy as np
# http://layer0.authentise.com/detecting-circular-shapes-using-contours.html
# mypath = "C:/Users/mgonzalez91/Dropbox (GaTech)/Research/All Things Emory !/pythonOpticalEphys repo/repo/pythonOpticalEphys"
# file_list = [f for f in listdir(mypath) if isfile(join(mypath, f)) & f.endswith(".tif")]

# for filename in file_list:
# Read image, normalize to [0,1], get size
raw_image = np.array(Image.open("1.tif").convert('L'))
norm_image = raw_image/np.max(raw_image)
contour_image = raw_image/np.max(raw_image)
row,col = norm_image.shape

# Box plotting for visual aid
# print(row)
# print(col)
# fig = plt.figure(1)
# ax = fig.add_subplot(111)
# bp = ax.boxplot(norm_image.reshape((row*col,1)))

# filter to preserve edges, threshold above 97 percentile 'fluorescence', use 2.4% of size for filter size
bilateral_filtered_image = cv2.bilateralFilter(norm_image.astype('float32'), int(.019*row), int(.019*row), int(.019*row))
ret, masked_image = cv2.threshold(bilateral_filtered_image,np.quantile(norm_image,.97),1,cv2.THRESH_BINARY)

# find contours from masked image  
contours, hierarchy = cv2.findContours(masked_image.astype('uint8'),cv2.RETR_LIST,cv2.CHAIN_APPROX_NONE)
# cv2.drawContours(raw_image, contours, -1, (255,255,255), 2)

centroids = list()
for cnt in contours:
    (x,y),radius = cv2.minEnclosingCircle(cnt)
    rect_area = cv2.minAreaRect(cnt)
    box = np.int0(cv2.boxPoints(rect_area))
    print(box)
    cv2.drawContours(contour_image,[box],-1,(0,0,255),1)
    # print('x = ',x)
    # print('y = ',y)
    # print('radius = ',radius)

    # if contour size is between .05% and 1% of field of view, count as cell
    # also check if min enclosing circle is significantly bigger than contourArea to measure roundness
    if cv2.contourArea(cnt) < .01*row*col and cv2.contourArea(cnt) > .0005*row*col and cv2.contourArea(cnt) > (radius*radius*3.1415*.5):
        # print("Cell Detected")
        cv2.drawContours(contour_image, cnt, -1, (100,140,204), linewidth)
        M = cv2.moments(cnt)
        cx = int(M['m10']/M['m00'])
        cy = int(M['m01']/M['m00'])
        centroids.append([cx, cy])
# cv2.imshow('Contours', norm_image) 
# cv2.waitKey(0) 
# cv2.destroyAllWindows()
print('Num Centroids =', len(centroids))

# show image
titles = ['Raw','Normalized','Bilateral','Masked','Contour']
images = [raw_image,norm_image,bilateral_filtered_image,masked_image,contour_image]
plt.figure(figsize=(8,8))
for i in range(5):
    plt.subplot(2,3,i+1)
    plt.imshow(images[i],interpolation='nearest')
    plt.title(titles[i])
    plt.xticks([])
    plt.yticks([])
plt.show()