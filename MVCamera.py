from threading import Thread
from six.moves.queue import Queue, Empty, Full
import numpy as np
import mv,cv2
import time

class AcquisitionThread(Thread):
    def __init__(self, device, queue):
    	super(AcquisitionThread, self).__init__()
    	self.dev = device
    	#import ipdb; ipdb.set_trace()
    	self.is_color = 'BayerRG8' in self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.PixelFormat.doc_string
    	if self.is_color:
            self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.PixelFormat.writeS(b'BayerRG8')
            
        
    	self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.BinningHorizontal.value = 1
    	self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.DecimationHorizontal = 2
    	self.dev.Setting.Base.Camera.GenICam.ImageFormatControl.DecimationVertical = 2
    	self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.ExposureAuto.writeS(b'Off')
    	self.dev.Setting.Base.Camera.GenICam.AnalogControl.GainAuto.writeS(b'Off')
    	self.dev.Setting.Base.Camera.GenICam.AnalogControl.Gain = 17
    	self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.ExposureTime = 2000
    	self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.AcquisitionFrameRateEnable = 1
    	self.dev.Setting.Base.Camera.GenICam.AcquisitionControl.AcquisitionFrameRate = 20

	#import ipdb; ipdb.set_trace()

    	self.queue = queue
    	self.wants_abort = False

    def acquire_image(self):
        #try to submit 2 new requests -> queue always full
        try:
            self.dev.image_request()
            #self.dev.image_request()
        except mv.MVError as e:
            print('errrrrrrr')
            import traceback
            traceback.print_exc()
            pass

        #get image
        image_result = None
        try:
            image_result = self.dev.get_image()
        except mv.MVTimeoutError:
            print("timeout")
        except Exception as e:
            print("camera error: ",e)
        
        #pack image data together with metadata in a dict
        if image_result is not None:
            buf = image_result.get_buffer()
            imgdata = np.array(buf, copy = False)
            
            info=image_result.info
            timestamp = info['timeStamp_us']
            frameNr = info['frameNr']

            del image_result
            return dict(img=imgdata, t=timestamp, N=frameNr)
        
    def reset(self):
        self.dev.image_request_reset()
        
    def run(self):
        self.reset()
        while not self.wants_abort:
            img = self.acquire_image()
            if img is not None:
                try:
                    self.queue.put_nowait(img)
                    #print('.',) #
                except Full:
                    #print('!',)
                    pass

        self.reset()
        print("acquisition thread finished")

    def stop(self):
        self.wants_abort = True

class MVCamera():
    def __init__(self):
        #find an open device
        serials = mv.List(0).Devices.children #hack to get list of available device names
        serial = serials[0]
        device = mv.dmg.get_device(serial)
        print('Using device:', serial)
        
        self.queue = Queue(10)
        acquisition_thread = AcquisitionThread(device, self.queue)
        self.is_color = acquisition_thread.is_color
        #consume images in main thread
        acquisition_thread.start()
        
    def get(self):
        img = self.queue.get(block=True, timeout = 1)
        #return  (np.dstack((img['img']['f0'],img['img']['f1'],img['img']['f2']))/1.0).astype(np.uint8)
        if self.is_color:
            return  cv2.rotate((np.dstack((img['img']['f0'],img['img']['f1'],img['img']['f2']))/1.0).astype(np.uint8),2)
        else:
            return  (np.array(img['img'])/1.0).astype(np.uint8)

def StreamCamera(cam):
    cam_name = 'irdc_store_entry'
    import sys,os
    sys.path.insert(0,os.path.join(os.path.dirname(os.path.realpath(__file__)),'..'))
    import config,zmq
    from utils import send_frame
    from FPSMeter import FPSMeter
    zmq_context = zmq.Context()
    socket = zmq_context.socket(zmq.PUB)
    socket.connect(config.bgr_img_xsub_addr_connect)
    meter = FPSMeter('MV camera', period=60)
    
    while True:
        bgr_frame = cam.get()
        send_frame(socket, str.encode(cam_name), bgr_frame, int(time.time() * 1000))
        meter.increment()
            
            
            
if __name__ == '__main__':
    
    camera = MVCamera()
    StreamCamera(camera)
    while True:
        img = camera.get()
        cv2.imshow('test', img)
        cv2.waitKey(1)