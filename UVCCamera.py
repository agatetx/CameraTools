import numpy as np
import cv2
import time


class UVCCamera():
    def __init__(self, camera_id=0):
        self.cap = cv2.VideoCapture(camera_id)
     
    def get(self):
        ret, frame = self.cap.read()
        return  frame

if __name__ == '__main__':
    
    camera = UVCCamera()
    while True:
        img = camera.get()
        #if not img is None:
            #cv2.imshow('test', img)
        cv2.waitKey(1)