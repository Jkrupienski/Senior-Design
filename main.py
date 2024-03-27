import cv2

import csv

import collections

import numpy as np

from tracker import *

tracker = EuclideanDistTracker()

confThreshold =0.1
nmsThreshold= 0.2

# Middle cross line position
middle_line_position = 225
up_line_position = middle_line_position - 15
down_line_position = middle_line_position + 15

classesFile = "coco.names"

classNames = open(classesFile).read().strip().split('\n')
print(classNames)
print(len(classNames))
modelConfiguration = 'yolov3-320.cfg'
modelWeights = 'yolov3-320.weights'
net = cv2.dnn.readNetFromDarknet(modelConfiguration, modelWeights)

net.setPreferableBackend(cv2.dnn.DNN_BACKEND_CUDA)

net.setPreferableTarget(cv2.dnn.DNN_TARGET_CUDA)

np.random.seed(42)

colors = np.random.randint(0, 255, size=(len(classNames), 3), dtype='uint8')

cap = cv2.VideoCapture('Alibi ALI-IPU3030RV IP Camera Highway Surveillance.mp4')

def realTime():

    while True:
        success, img = cap.read()

        img = cv2.resize(img,(0,0),None,0.5,0.5)

        ih, iw, channels = img.shape

# Draw the crossing lines
        cv2.line(img, (0, middle_line_position), (iw, middle_line_position),

        (255, 0, 255), 1)

        cv2.line(img, (0, up_line_position), (iw, up_line_position), (0, 0, 255), 1)

        cv2.line(img, (0, down_line_position), (iw, down_line_position), (0, 0, 255), 1)

# Show the frames

        cv2.imshow('Output', img)

# if name == 'main':
  #  realTime()

input_size = 320

blob = cv2.dnn.blobFromImage(img, 1 / 255, (input_size, input_size), [0, 0, 0], 1, crop=False)

# Set the input of the network

net.setInput(blob)

layersNames = net.getLayerNames()

outputNames = [(layersNames[i[0] - 1]) for i in net.getUnconnectedOutLayers()]

# Feed data to the network

outputs = net.forward(outputNames)

# Find the objects from the network output


def postProcess(outputs,img):

    global detected_classNames

    height, width = img.shape[:2]

    boxes = []

    classIds = []

    confidence_scores = []

    detection = []

    for output in outputs:

        for det in output:

            scores = det[5:]

            classId = np.argmax(scores)

            confidence = scores[classId]

    if classId in required_class_index:

        if confidence > confThreshold:

    # print(classId)

            w,h = int(det[2]width),int(det[3]height)

            x,y = int((det[0]width)-w/2) , int((det[1]height)-h/2)

            boxes.append([x,y,w,h])

            classIds.append(classId)

            confidence_scores.append(float(confidence))

#Update the tracker for each object
postProcess(outputs,img)

detected_classNames = []

boxes_ids = tracker.update(detection)

for box_id in boxes_ids:

    count_vehicle(box_id)

temp_up_list = []

temp_down_list = []

up_list = [0, 0, 0, 0]

down_list = [0, 0, 0, 0]


def count_vehicle(box_id):

    x, y, w, h, id, index = box_id

    # Find the center of the rectangle for detection

    center = find_center(x, y, w, h)

    ix, iy = center


def find_center(x, y ,w ,h):
    # Find the current position of the vehicle

    if (iy > up_line_position) and (iy < middle_line_position):

        if id not in temp_up_list:
            temp_up_list.append(id)

    elif iy < down_line_position and iy > middle_line_position:

        if id not in temp_down_list:
            temp_down_list.append(id)

    elif iy < up_line_position:

        if id in temp_down_list:
            temp_down_list.remove(id)

            up_list[index] = up_list[index] + 1

    elif iy > down_line_position:

        if id in temp_up_list:
            temp_up_list.remove(id)

            down_list[index] = down_list[index] + 1