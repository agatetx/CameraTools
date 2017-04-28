import numpy as np
import cv2
import time


class FILECamera():
    def __init__(self, filepath):
        self.cap = cv2.VideoCapture(filepath)
     
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