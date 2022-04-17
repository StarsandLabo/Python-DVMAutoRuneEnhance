import numpy as np
from PIL import ImageGrab
import cv2, datetime

#キャプチャを取得するだけならこれ
#img = ImageGrab.grab()

class ScreenCapture():
    
    posLeft     = None
    posRight    = None
    posUpper    = None
    posBottom   = None
    imgPath     = None
    
    def grab(self, mode, filepath):
        image = ImageGrab.grab(all_screens=True)
        img = np.array(image, dtype=np.uint8)
        
        if      mode == 'gray':
            #print('true statement')
            converted = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        elif    mode == 'color':
            #print('else statement')
            converted = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
        
        self.imgPath = filepath
        cv2.imwrite(filepath, converted)