import numpy as np
import cv2
import time
import ids




class UEYECamera():
    def __init__(self):
        self.cam = ids.Camera()
        self.cam.color_mode = ids.ids_core.COLOR_RGB8    # Get images in RGB format
        self.cam.exposure = 5                            # Set initial exposure to 5ms
        self.cam.auto_exposure = True
        self.cam.continuous_capture = True               # Start image capture
     
    def get(self):
        img, meta = self.cam.next() 
        return  img[:,:,::-1]

if __name__ == '__main__':
    
    camera = UEYECamera()
    while True:
        img = camera.get() 
        if not img is None:
            cv2.imshow('test', img)
        cv2.waitKey(1)