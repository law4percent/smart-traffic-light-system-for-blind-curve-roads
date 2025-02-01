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
    
def print_data(data):
    print("check_params: ", end="")
    for key, value in data.items():
        print(f"{key}={value}", end=" ")
    
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
        

def display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data, color=(255, 255, 255)):
    if frame_name.lower() == "off":
        return
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.75
    thickness = 2
    bg_color = (0, 0, 0)
    alpha = 0.6
    
    overlay = frame.copy()
    
    for zone_indx in range(number_of_zones):
        vehic = queuing_data[zone_indx]["vehicle"]
        curr_time = queuing_data[zone_indx]["current_time"]
        text = f"Zone: {zone_indx} | NV: {len(zones_list[zone_indx])} | PV: {vehic} [{curr_time}]"
        
        position = (25, 25 + 30 * zone_indx)
        (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
        
        cv2.rectangle(overlay, (position[0] - 5, position[1] - text_h - 5), 
                      (position[0] + text_w + 5, position[1] + 5), bg_color, cv2.FILLED)
        cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
        
        cv2.putText(frame, text, position, font, font_scale, color, thickness)


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
    colors = {'box': (86, 179, 255), 'text': (255, 255, 255), 'center': (255, 89, 94)}
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1, y1), (x2, y2), colors['box'], cv2.FILLED)
    cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)
    cv2.rectangle(frame, (x1, y1), (x2, y2), colors['box'], 2)
    cv2.circle(frame, cls_center_pnt, 4, colors['center'], -1)
    text = f"{class_list[int(cls)]} {conf_score}%"
    cv2.putText(frame, text, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, colors['text'], 2)          

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
            
            if key == "mqtt_broker" or key == "SERVICE_UUID" or key == "CHARACTERISTIC_UUID" or key == "IP_ESP32_1" or key == "IP_ESP32_2":
                get_data[key] = value
            else:
                # Try to convert to float or int if possible
                if value.replace('.', '', 1).isdigit() and value.count('.') < 2:
                    if '.' in value:
                        get_data[key] = float(value)  # Convert to float
                    else:
                        get_data[key] = int(value)  # Convert to int
                else:
                    get_data[key] = value

    print_data(get_data)
    return get_data
    

def handle_zone_queuing(zone_index, zones_list, current_time, frame, zones_data, interval):
    zone = zones_data[zone_index]

    # Start the countdown if it's not already refreshing and the zone has vehicles
    if not zone["refresh"] and len(zones_list[zone_index]) > 0:
        zone["refresh"] = True
        zone["countdown_start_time"] = current_time
        zone["get_vehicle"] = zones_list[zone_index][0]

    # Check if the countdown is active and has elapsed
    if zone["refresh"] and zone["countdown_start_time"] != 0.0:
        elapsed_time = current_time - zone["countdown_start_time"]
        if elapsed_time >= interval:
            # Countdown is complete
            print(f"Countdown complete for Zone {zone_index}!")
            zone["refresh"] = False
            zone["countdown_start_time"] = 0.0
            zone["get_vehicle"] = None

    # Calculate the current time remaining in the countdown
    remaining_time = 0.0
    if zone["countdown_start_time"] != 0.0:
        remaining_time = round(current_time - zone['countdown_start_time'], 2)

    return {
        "zone_index": zone_index,
        "vehicle": zone["get_vehicle"],
        "current_time": f'{remaining_time:.2f}'
    }

def traffic_light(frame, zone_index, is_zone_occupied, vehicle, rect_color=(100, 100, 100), thickness=4, radius=15):
    # Get the frame dimensions
    frame_width = frame.shape[1]
    frame_height = frame.shape[0]

    if zone_index == 0:
        top_left = (int(0.05 * frame_width), int(frame_height - 150))
        bottom_right = (top_left[0] + 50, top_left[1] + 100)
    else:
        top_left = (int(frame_width - 100), int(frame_height - 150))
        bottom_right = (top_left[0] + 50, top_left[1] + 100)


    # Calculate center of the rectangle and y positions for circles
    rect_center_x = (top_left[0] + bottom_right[0]) // 2
    upper_y = top_left[1] + radius + 5
    lower_y = bottom_right[1] - radius - 5

    # Mask color (background for rectangle)
    mask_color = (0, 0, 0)

    # Draw rectangle and mask
    cv2.putText(frame, f"Zone: {zone_index}", (top_left[0], top_left[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    cv2.rectangle(frame, top_left, bottom_right, rect_color, thickness)
    cv2.rectangle(frame, top_left, bottom_right, mask_color, -1)

    # Determine the circle colors based on vehicle presence
    if is_zone_occupied:
        upper_circle_color = (0, 255, 255)
        lower_circle_color = (0, 100, 0)
    else:
        upper_circle_color = (0, 100, 100)
        lower_circle_color = (0, 255, 0)

    # Draw the circles
    cv2.circle(frame, (rect_center_x, upper_y), radius, upper_circle_color, -1)
    cv2.circle(frame, (rect_center_x, lower_y), radius, lower_circle_color, -1)

