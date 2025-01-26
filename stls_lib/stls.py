import cv2
import numpy as np
import os
import ast
from ultralytics import YOLO

def read_class_names(file_path: str) -> list:
        with open(file_path, 'r') as f:
            class_names = [line.strip() for line in f.readlines()]
        return class_names

def check_exist_file(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")
    
    
def read_points_from_file(file_path):
    check_exist_file(file_path)
    data = {}
    with open(file_path, 'r') as file:
        for line in file:
            index_part, points_part = line.split(':', 1)
            index = int(index_part.strip())
            points = ast.literal_eval(points_part.strip())
            data[index] = points
    return data


def draw_polylines_zones(image, data, frame_name, linesColor=(0, 255, 0), txtColor=(0, 0, 255), fontScale=0.65, thickness=2):
    if frame_name.lower() == "off":
        return

    for key, points in data.items():
        points_array = np.array(points, dtype=np.int32)
        cv2.polylines(image, [points_array], isClosed=True, color=linesColor, thickness=2)
        centroid = np.mean(points_array, axis=0).astype(int)
        cv2.putText(image, f"{key}", tuple(centroid), cv2.FONT_HERSHEY_SIMPLEX, fontScale, txtColor, thickness)
        

def display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data, color=(255, 255, 255), fontScale=0.75, thickness=2):
    if frame_name.lower() == "off":
        return
    
    for zone_indx in range(number_of_zones):
        vehic = queuing_data[zone_indx]["vehicle"]
        curr_time = queuing_data[zone_indx]["current_time"]
        cv2.putText(
                    frame,
                    f"zone: {zone_indx} | nv: {len(zones_list[zone_indx])} | pv: {vehic} ["
                    f"{curr_time}]",
                    (25, 25 + 28 * zone_indx),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.75,
                    color,
                    2,
                )


def check_camera(cap):
    if not cap.isOpened():
        raise TypeError("Cannot open camera.")


def track_objects_in_zones(frame, boxes, class_list, zones, zones_list, frame_name):
    for idx, box in enumerate(boxes):
        x1, y1, x2, y2, conf_score, cls = box
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        conf_score = "%.2f" % conf_score
        cls_center_x = int(x1 + x2) // 2
        cls_center_y = int(y1 + y2) // 2
        cls_center_pnt = (cls_center_x, cls_center_y)
        for zone_indx, zone in enumerate(zones.values()):
            if cv2.pointPolygonTest(np.array(zone, dtype=np.int32), cls_center_pnt, False) == 1:
                show_object_info(frame, x1, y1, x2, y2, cls, conf_score, class_list, cls_center_pnt, frame_name)
                zones_list[zone_indx].append(class_list[int(cls)])
                break
    return zones_list


def show_object_info(frame, x1, y1, x2, y2, cls, conf_score, class_list, cls_center_pnt, frame_name):
    if frame_name.lower() == "off":
        return
    cv2.circle(img=frame, center=cls_center_pnt, radius=0, color=(255, 100, 255), thickness=5)
    cv2.rectangle(img=frame, pt1=(x1, y1), pt2=(x2, y2), color=(255, 100, 100), thickness=2)
    cv2.putText(img=frame, text=f"{class_list[int(cls)]} {conf_score}%", org=(x1, y1), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.75, color=(255, 255, 255), thickness=2)


def init_zone_list(number_of_zones):
    zones_list = []
    for _ in range(number_of_zones):
        zones_list.append([])
    return zones_list


def load_model(weights_file_path):
    check_exist_file(weights_file_path)
    return YOLO(weights_file_path, "v11")


def load_class_names(class_names_file_path):
    check_exist_file(class_names_file_path)
    return read_class_names(class_names_file_path)


def load_camera(video_source):
    captured = cv2.VideoCapture(video_source)
    check_camera(captured)
    return captured


def load_zones(zone_file_path):
    zones = read_points_from_file(zone_file_path)
    number_of_zones = len(zones)
    return [zones, number_of_zones]


def get_prediction_boxes(frame, yolo_model, confidence):
    pred = yolo_model.predict(source=[frame], save=False, conf=confidence)
    results = pred[0]
    boxes = results.boxes.data.numpy()
    return boxes


def show_frame(frame, frame_name, wait_key, ord_key):
    if frame_name.lower() == "off":
        return True
    
    cv2.imshow(frame_name, frame)
    if cv2.waitKey(wait_key) & 0xFF == ord(ord_key):
        return False
    return True


def extract_data(file_path: str):
    check_exist_file(file_path)
    get_data = {}

    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            # Skip empty lines or lines without a colon
            if ':' not in line:
                continue
            
            # Split each line by the first colon to separate the key and value
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            
            # Try to convert to float or int if possible
            if value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                if '.' in value:
                    get_data[key] = float(value)  # Convert to float
                else:
                    get_data[key] = int(value)  # Convert to int
            else:
                get_data[key] = value
    
    return get_data
    

def handle_zone_queuing(zone_index, zones_list, current_time, frame, zones_data, interval):
    zone = zones_data[zone_index]

    # Start the countdown if refresh is False and the zone has vehicles
    if not zone["refresh"] and len(zones_list[zone_index]) > 0:
        zone["refresh"] = True
        zone["countdown_start_time"] = current_time
        zone["get_vehicle"] = zones_list[zone_index][0]

    # Check if the countdown is active and has elapsed
    if zone["refresh"] and zone["countdown_start_time"] != 0.0:
        if current_time - zone["countdown_start_time"] >= interval:
            print(f"Countdown complete for Zone {zone_index}!")
            zone["refresh"] = False
            zone["countdown_start_time"] = 0.0
            zone["get_vehicle"] = None

    # Display the zone's status
    curr_time = '%.2f' % (current_time - zone['countdown_start_time']) if zone['countdown_start_time'] != 0.0 else 0.0
    
    return {
            "zone_index": zone_index,
            "vehicle": zone["get_vehicle"],
            "current_time": curr_time
        }