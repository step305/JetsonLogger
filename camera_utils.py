import cv2
import multiprocessing as mp
import numpy as np
import time
from config import *


class CameraMessage:
    def __init__(self, ts, descriptors, points):
        self.descriptors = descriptors
        self.points = points
        self.ts = ts


def orb_detector_process(frame: np.ndarray):
    orb_detector = cv2.ORB_create(nfeatures=ORB_DETECTOR_MAX_FEATURES)
    frame_bw = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    keypoints, descriptors = orb_detector.detectAndCompute(frame_bw, None)
    ts = time.time()
    return CameraMessage(ts, descriptors, keypoints)


def camera_reader(queue_features: mp.Queue,
                  queue_record: mp.Queue,
                  stop: mp.Event):
    pipeline = ('v4l2src device={} do-timestamp=true ! '
                'video/x-raw, width={}, height={}, framerate={}/1, format={} ! '
                'videoconvert ! video/x-raw, format=BGR ! appsink'
                ).format(VIDEO_CAPTURE_DEVICE, VIDEO_LOG_FRAME_SHAPE[0], VIDEO_LOG_FRAME_SHAPE[1],
                         VIDEO_CAPTURE_FRAMERATE, VIDEO_CAPTURE_FORMAT)

    capture_device = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
    time.sleep(1)
    if capture_device.isOpened():
        print('Camera opened!')
    else:
        print('Error opening camera!')
        stop.set()
        return
    fps_timer_start = time.time()
    fps_counter = 0

    while True:
        if stop.is_set():
            break
        ret, frame = capture_device.read()
        if ret:
            if fps_counter >= FPS_MAX_COUNTER:
                fps_timer_stop = time.time()
                print('VideoCapture at {:.1}fps'.format(fps_counter / (fps_timer_stop - fps_timer_start)))
                fps_timer_start = time.time()
                fps_counter = 0
            else:
                fps_counter += 1
            msg = orb_detector_process(frame)
            if not queue_record.full() and not queue_features.full():
                queue_record.put(frame)
                queue_features.put(msg)
            else:
                print('VideoCapture: Warning! Queue is full!')
    capture_device.release()


def video_recorder(queue_record: mp.Queue,
                   stop: mp.Event):
    fourcc = cv2.VideoWriter_fourcc(*'MJPG')
    recorder_device = cv2.VideoWriter('video_slam.avi', fourcc, VIDEO_LOG_FRAMERATE, VIDEO_LOG_FRAME_SHAPE)

    fps_timer_start = time.time()
    fps_counter = 0

    while True:
        if stop.is_set():
            break
        if not queue_record.empty():
            if fps_counter >= FPS_MAX_COUNTER:
                fps_timer_stop = time.time()
                print('VideoRecord at {:.1}fps'.format(fps_counter / (fps_timer_stop - fps_timer_start)))
                fps_timer_start = time.time()
                fps_counter = 0
            else:
                fps_counter += 1
            frame = queue_record.get()
            recorder_device.write(frame)
    recorder_device.release()
