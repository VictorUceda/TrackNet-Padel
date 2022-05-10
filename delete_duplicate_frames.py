from parser import parser
import cv2
import numpy as np

def is_similar(image1, image2):
    return image1.shape == image2.shape and np.amax(cv2.subtract(image1, image2))<80

args = parser.parse_args()
video_path = args.label_video_path

out_video_root = video_path[:-4]+'_c.mp4'

print(video_path)
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')
videoWriter = cv2.VideoWriter(out_video_root, fourcc, fps, size)
i = 0
last_img = None
while (cap.isOpened()):
        flag, img = cap.read()
        if not flag:
            break
        #modify img
        if last_img is not None and is_similar(last_img, img):
          print(i)
          continue
        
        last_img = img
        i += 1
        #cv2.putText(img, str(i), (80,150), cv2.FONT_HERSHEY_SIMPLEX, 1, (153, 0, 0), 1, cv2.LINE_AA)

        #save img
        videoWriter.write(img)
        
cap.release()
videoWriter.release()
