# find cell contours

import cv2 
import numpy as np 

raw_image = cv2.imread('temp_img.png',0)
threshold_coefficient = 0.5
while threshold_coefficient < 30:
    # th3 = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,cv.THRESH_BINARY,11,2)
    # np.mean(raw_image)*threshold_coefficient, 
    thresholded = cv2.adaptiveThreshold(raw_image,255,cv2.ADAPTIVE_THRESH_MEAN_C,cv2.THRESH_BINARY,99,5)
    cv2.imshow("After Threshold Template", thresholded)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    #Gaussian Blur
    thresholded = cv2.GaussianBlur(thresholded,(25,25),0)
    cv2.imshow("Blur", thresholded)        
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    contours, hierarchy = cv2.findContours(thresholded,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    print(contours)
    print(hierarchy)
    cv2.drawContours(raw_image, contours, -1, (255,255,255), 2)

    for cnt in contours:
        (x,y),radius = cv2.minEnclosingCircle(cnt)
        if cv2.contourArea(cnt) < 8000 and cv2.contourArea(cnt) > 2500 and cv2.contourArea(cnt) > (3.14*radius*radius*0.6):
            print("Cell Detected")
            cv2.drawContours(raw_image, cnt, -1, (255,255,255), 3)
            M = cv2.moments(cnt)
            cx = int(M['m10']/M['m00'])
            cy = int(M['m01']/M['m00'])
            centroids.append([cx, cy])
            cv2.circle(raw_image, (cx, cy), 1, (200,200,200), thickness = 2)

    cv2.imshow("Contours Threshold at %f"%(threshold_coefficient), raw_image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    threshold_coefficient = threshold_coefficient + 1
    # print(centroids)

# if len(centroids) == 0:
#     print("No Cell Detected")
#     self.sig.emit()

# org = copy.deepcopy(overlay)
# for [cx, cy] in centroids:
#     cv2.circle(overlay, (cx, cy), 1, (250,250,250), thickness = 2)
# cv2.imwrite("%s Overlay.png" % (self.detection_time), overlay)
# cv2.imshow("Contours with centroids", overlay)
# cv2.waitKey(0)
# cv2.destroyAllWindows()

    # # Hierarchy Clustering
    # max_distance = float(50.0)
    # flat_cluster = fcluster(linkage(centroids), max_distance, criterion = 'distance')
    # global cluster_centroids

    # minimum_centroid_number = 5
    # clusterIndex = 1

    # while True:
    #     count = 0
    #     acumulator = [0,0]
    #     for indx, i in enumerate(flat_cluster):
    #         if i == clusterIndex:
    #             acumulator[0] = acumulator[0] + centroids[indx][0]
    #             acumulator[1] = acumulator[1] + centroids[indx][1]
    #             count = count + 1
    
        # if count == 0:
        #     break # we passed the last cluster

        # if count >= minimum_centroid_number:
        #     acumulator[0] = acumulator[0]/count
        #     acumulator[1] = acumulator[1]/count
        #     cluster_centroids.append(acumulator)

        # clusterIndex = clusterIndex + 1

    # for [cx, cy] in cluster_centroids:
    #     cv2.circle(org, (cx, cy), 1, (250,250,250), thickness = 2)

    # cv2.imwrite("%s Contours with Cluster.png" % (self.detection_time), org)
    # cv2.imshow("Contours with cluster", org)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()

    # for [cx,cy] in cluster_centroids:
    #     brightest_z = 0
    #     illumination = 0
    #     for indx, img in enumerate(stack):
    #         illum_temp = numpy.sum(img[(cy-20):(cy+20), (cx-20):(cy+20)])
    #         if illum_temp>illumination:
    #             brightest_z = indx
    #             illumination = illum_temp
    #     [x,y] = grid.getDeltaToScreenCenterMouseToUMFromCoords(cx, cy)
    #     x = startingCoordinate[0]+x
    #     y = startingCoordinate[1]+y
    #     z = startingCoordinate[2]+brightest_z*stepSize
    #     #self.owner.parent.parent.storedCoordinates.addItem(0,0,x,y,z)
    #     cellCentroids.append([x,y,z])

    # self.sig.emit()
