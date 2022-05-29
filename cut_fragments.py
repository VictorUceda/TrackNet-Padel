from parser import parser
import ntpath
import queue
import cv2
import numpy as np
import pandas as pd


args = parser.parse_args()
input_video_path = args.label_video_path
output_path =  args.output_segments_path
output_name = ntpath.basename(input_video_path)[:-4]

if output_path == "":
    exit()

#get video fps&video size
cap = cv2.VideoCapture(input_video_path)
fps = int(cap.get(cv2.CAP_PROP_FPS))
size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
fourcc = cv2.VideoWriter_fourcc(*'mp4v')

#start from first frame

segments_file = input_video_path[:-4]+".points.csv"

df_segments = pd.read_csv(segments_file, sep=';')
segments = []
videoWriters = []
i = 0
for index, row in df_segments.iterrows():
    print(row['ini'], row['fin'])
    segments.append([row['ini'], row['fin']])

    i += 1


videoWriter = cv2.VideoWriter(output_path+'/'+output_name+'_0.mp4', fourcc, fps, size)
#both first and second frames cant be predict, so we directly write the frames to output video
#capture frame-by-frame

currentFrame = 0
while(cap.isOpened()):
  #capture frame-by-frame
  if any([currentFrame==frag[1] for frag in segments]):
    ind = [frag[1] for frag in segments].index(currentFrame)
    if ind == len(segments)-1:
      break
    currentFrame = segments[ind+1][0]
    videoWriter.release()
    videoWriter = cv2.VideoWriter(output_path+'/'+output_name+'_'+str(ind+1)+'.mp4', fourcc, fps, size)
    cap.set(1,currentFrame);
    print("jump to next fragment in frame: "+str(currentFrame-2))


  ret, img = cap.read()
  if not ret:
    break

  videoWriter.write(img)

  currentFrame += 1
  if not currentFrame % 100: print(currentFrame)


# everything is done, release the video
cap.release()
videoWriter.release()
print("finish")
