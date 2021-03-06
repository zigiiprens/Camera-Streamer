import os
import cv2 as cv
import numpy as np
from threading import Thread


class ProcessFrame:
    def __init__(self, algorithm, api_mode):
        self.algo = algorithm
        self.mode = api_mode
        self.imgDataFolder = "data/img/"
        self._count = 0
        self.confidence_threshold = 0.5
        self.process_frame = None
        self.stopped = False
        self.detections = None
        self.confidence = None
        self.box = None
        self.cropped_frame = None
        self.write_string = None

        if self.algo == "CAFFE":
            self.modelFile = "src/models/res10_300x300_ssd_iter_140000_fp16.caffemodel"
            self.configFile = "src/models/deploy.prototxt"
            self.net = cv.dnn.readNetFromCaffe(self.configFile, self.modelFile)
            print("[INFO] Loaded model from CAFFE")
        elif self.algo == "TF":
            self.modelFile = "src/models/opencv_face_detector_uint8.pb"
            self.configFile = "src/models/opencv_face_detector.pbtxt"
            self.net = cv.dnn.readNetFromTensorflow(
                self.modelFile, self.configFile)
            print("[INFO] Loaded model from TENSORFLOW")

    def start(self, frame):
        try:
            self.process_frame = frame
        except Exception as ex:
            print("[ERROR] Could not copy frame into process_frame, {}" .format(ex.message))

        Thread(target=self.processDetect, args=()).start()

    def processDetect(self):
        while not self.stopped:
            if self.algo == "CAFFE":
                print("[INFO] Inside ProcessDetect of algorithm {}" .format(self.algo))
                self.process_frame = self.process_frame[:, :, ::-1]

            (h, w) = self.process_frame.shape[:2]
            blob = cv.dnn.blobFromImage(cv.resize(self.process_frame, (300, 300)), 1.0, (300, 300),
                                        (104.0, 177.0, 123.0))

            self.net.setInput(blob)
            self.detections = self.net.forward()

            if self.process_frame is not None:
                if len(self.detections) > 0:
                    # loop over the detections
                    for i in range(0, self.detections.shape[2]):

                        # extract the confidence (i.e., probability) associated with the
                        # prediction
                        self.confidence = self.detections[0, 0, i, 2]

                        # filter out weak detections by ensuring the `confidence` is
                        if self.confidence < self.confidence_threshold:
                            continue

                        # compute the (x, y)-coordinates of the bounding box for
                        # the face
                        self.box = self.detections[0, 0, i, 3:7] * np.array([w, h, w, h])
                        (startX, startY, endX, endY) = self.box.astype("int")

                        # face_locations += [(startY, endX, endY, startX)]

                        # extract the face ROI and grab the ROI dimensions
                        self.cropped_frame = self.process_frame[startY:endY, startX:endX]
                        (fH, fW) = self.cropped_frame.shape[:2]

                        # ensure the face width and height are sufficiently large
                        if fW < 50 or fH < 50:
                            continue

                        self.write_string = f'{self.imgDataFolder + str(self._count)}.jpg'
                        ret = cv.imwrite(self.write_string, self.cropped_frame)
                        print("[INFO] Found faces, saving face to {}, status {}" .format(self.write_string, ret))
                        self._count += 1
            else:
                print("[INFO] Process_frame is empty")

            self.stopped = True

        self.stopped = False

    def stop(self):
        self.stopped = True
