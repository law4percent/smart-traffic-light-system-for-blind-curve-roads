import cv2
from stls_lib import stls
import time

def main(video_source, 
         weight_file_path: str, 
         class_list_file_path: str, 
         zones_file_path: str, 
         detect_sensitivity: float, 
         time_interval: float, 
         frame_name: str, 
         frame_height: int, 
         frame_width: int, 
         wait_key: int, 
         ord_key: str
         ):
    captured = stls.load_camera(video_source)
    yolo_model = stls.load_model(weight_file_path)
    class_list = stls.load_class_names(class_list_file_path)
    zones, number_of_zones = stls.load_zones(zones_file_path)

    count = 0
    success = True
    zones_data = [{"countdown_start_time": 0.0, "refresh": False, "get_vehicle": None} for _ in range(number_of_zones)]
    previous_vehicle = [None, None]

    while success:
        current_time = time.time()
        success, frame = captured.read()
        
        if not success:
            break

        count += 1
        if count % 3 != 0:
            continue

        zones_list = stls.init_zone_list(number_of_zones)
        frame = cv2.resize(frame, (frame_width, frame_height))
        boxes = stls.get_prediction_boxes(frame, yolo_model, detect_sensitivity)
        stls.draw_polylines_zones(frame, zones, frame_name) # Optional
        zones_list = stls.track_objects_in_zones(frame, boxes, class_list, zones, zones_list, frame_name)

        queuing_data = []
        for indx in range(number_of_zones):
            queuing_data.append(stls.handle_zone_queuing(indx, zones_list, current_time, frame, zones_data, time_interval))
            
            curr_time = queuing_data[indx]["current_time"]
            curr_vehic = queuing_data[indx]["vehicle"]
            if curr_time != 0.0:
                if previous_vehicle[indx] != curr_vehic:
                    previous_vehicle[indx] = curr_vehic
            
            stls.traffic_light(frame, indx, is_zone_occupied=len(zones_list[indx]) > 0, vehicle=curr_time) # Optional

        stls.display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data) # Optional
        success = stls.show_frame(frame, frame_name, wait_key, ord_key) # Optional

    captured.release()
    cv2.destroyAllWindows()