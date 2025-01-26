import cv2
from stls_lib import stls
import time
from picamera2 import Picamera2

def main(weight_file_path: str, class_list_file_path: str, zones_file_path: str, detect_sensivity: float, time_interval: float, frame_name: str, frame_height: int, frame_width: int, wait_key: int, ord_key: str):
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (frame_width,frame_height)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()
    
    yolo_model = stls.load_model(weight_file_path)
    class_list = stls.load_class_names(class_list_file_path)
    zones, number_of_zones = stls.load_zones(zones_file_path)

    count = 0
    success = True
    zones_data = [{"countdown_start_time": 0.0, "refresh": False, "get_vehicle": None} for _ in range(number_of_zones)]

    while success:
        current_time = time.time()
        frame = picam2.capture_array()

        count += 1
        if count % 3 != 0:
            continue

        zones_list = stls.init_zone_list(number_of_zones)
        frame = cv2.resize(frame, (frame_width, frame_height))
        boxes = stls.get_prediction_boxes(frame, yolo_model, detect_sensivity)
        stls.draw_polylines_zones(frame, zones, frame_name) # Optional
        zones_list = stls.track_objects_in_zones(frame, boxes, class_list, zones, zones_list, frame_name)

        queuing_data = []
        for indx in range(number_of_zones):
            queuing_data.append(stls.handle_zone_queuing(indx, zones_list, current_time, frame, zones_data, time_interval))

        stls.display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data) # Optional
        
        success = stls.show_frame(frame, frame_name, wait_key, ord_key) # Optional
        
    # captured.release()
    cv2.destroyAllWindows()