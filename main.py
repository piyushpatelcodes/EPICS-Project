import numpy as np
from ultralytics import YOLO
import cv2
import time
from sort.sort import *
from util import get_car, read_license_plate, write_csv, estimate_speed
import argparse

results = {}

mot_tracker = Sort()

# Argument Parser
parser = argparse.ArgumentParser(description='Speed estimation from video')
parser.add_argument('input', type=str, help='Path to input video file')
args = parser.parse_args()

# load model
coco_model = YOLO("yolov8n.pt")
license_plate_detector = YOLO('best.pt')

# Open video capture
cap = cv2.VideoCapture(args.input)

if not cap.isOpened():
    print("Error: Unable to open video.")
    exit()

video_fps = cap.get(cv2.CAP_PROP_FPS)
vehicles = [2, 3, 5, 7]

frame_nmr = -1

# read frames
prev_frame = None
prev_results = None
while True:
    frame_nmr += 1
    ret, frame = cap.read()
    if not ret:
        break

    results[frame_nmr] = {}
    # detect vehicles
    detections = coco_model(frame)[0]
    detections_ = []
    for detection in detections.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = detection
        if int(class_id) in vehicles:
            detections_.append([x1, y1, x2, y2, score])

    # track vehicles
    track_ids = mot_tracker.update(np.asarray(detections_))

    # detect licence plate
    license_plates = license_plate_detector(frame)[0]
    for license_plate in license_plates.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = license_plate

        # assign license plate to car
        xcar1, ycar1, xcar2, ycar2, car_id = get_car(license_plate, track_ids)

        if car_id != -1:

            # crop license plate
            license_plate_crop = frame[int(y1):int(y2), int(x1):int(x2)]

            # process license plate
            license_plate_crop_gray = cv2.cvtColor(license_plate_crop, cv2.COLOR_BGR2GRAY)
            _, license_plate_crop_thresh = cv2.threshold(license_plate_crop_gray, 64, 255, cv2.THRESH_BINARY_INV)

            # read license plate number
            license_plate_text, license_plate_text_score = read_license_plate(license_plate_crop_thresh)

            if license_plate_text is not None:
                # Get the speed and license plate information for the car
                car_data = {
                    'locations': track_ids,  # Assuming you have the car's locations over time in track_ids
                }
                car_info = estimate_speed(car_id, car_data)

                results[frame_nmr][car_id] = {
                    'car': {'bbox': [xcar1, ycar1, xcar2, ycar2]},
                    'car_speed': car_info['speed_label'],
                    'license_plate': {'bbox': [x1, y1, x2, y2],
                                      'text': license_plate_text,
                                      'bbox_score': score,
                                      'text_score': license_plate_text_score}}
                write_csv(results, './speed_test.csv')

# Release video capture
cap.release()

# write results
write_csv(results, './speed_test.csv')
