import cv2
import time
from stls_lib import stls, rtdb

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
         ord_key: str,
         communication_protocol: str
         ):
    
    # Load YOLO model and configurations
    captured = stls.load_camera(video_source)
    yolo_model = stls.load_model(weight_file_path)
    class_list = stls.load_class_names(class_list_file_path)

    # Extract data from the zones.txt file
    data = stls.extract_data_from_file(zones_file_path)
    zones = stls.convert_coordinates(data["zones"], data["frame_width"], data["frame_height"], frame_width, frame_height) # Ensuring the zone coordinates to fit the new frame dimensions
    number_of_zones = data["number_of_zones"]

    # Initalizing the Firebase Real-time Database
    rtdb.initialize_firebase(communication_protocol)

    # Initialize zones and tracking data
    count = 0
    success = True
    zones_data = [{"countdown_start_time": 0.0, "refresh": False, "get_vehicle": 'none'} for _ in range(number_of_zones)]
    prev_vehic_zone0 = 'none'
    prev_vehic_zone1 = 'none'

    while success:
        start_time = time.time() * 1000
        curr_time = time.time()
        success, frame = captured.read()
        
        if not success:
            break

        count += 1
        if count % 3 != 0:
            continue

        collected_vehicle = stls.init_list_of_collected_vehicle(number_of_zones)
        frame = cv2.resize(frame, (frame_width, frame_height))
        boxes = stls.get_prediction_boxes(frame, yolo_model, detect_sensitivity)
        stls.draw_polylines_zones(frame, zones, frame_name)  # Optional visualization
        collected_vehicle = stls.track_objects_in_zones(frame, boxes, class_list, zones, collected_vehicle, frame_name)

        queuing_data = []
        for indx in range(number_of_zones):
            queuing_data.append(stls.handle_zone_queuing(indx, collected_vehicle, curr_time, zones_data, time_interval))
            stls.traffic_light_display(frame, indx, is_zone_occupied = len(collected_vehicle[indx]) > 0) # Optional visualization

        curr_vehic_zone0 = queuing_data[0]["vehicle"]
        curr_vehic_zone1 = queuing_data[1]["vehicle"]    
        # Only send to Firebase if vehicle data has changed
        if curr_vehic_zone0 != prev_vehic_zone0 or curr_vehic_zone1 != prev_vehic_zone1:
            rtdb.send_data_in_firebase([curr_vehic_zone0, curr_vehic_zone1], communication_protocol)
            prev_vehic_zone0 = curr_vehic_zone0
            prev_vehic_zone1 = curr_vehic_zone1

        data_to_display = {
            "number_of_zones": number_of_zones,
            "zones_list": collected_vehicle,
            "frame_name": frame_name,
            "queuing_data": queuing_data,
            "processing_time": (time.time() * 1000) - start_time
        }
        stls.display_zone_info(frame, data_to_display)  # Optional visualization       
        success = stls.show_frame(frame, frame_name, wait_key, ord_key)  # Optional frame display

    captured.release()
    cv2.destroyAllWindows()