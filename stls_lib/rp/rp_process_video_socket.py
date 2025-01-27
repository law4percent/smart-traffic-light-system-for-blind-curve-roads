import cv2
from stls_lib import stls
import time
from picamera2 import Picamera2
import socket

def send_data_to_esp32(ip, port, data):
    try:
        # Create a TCP/IP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Connect to ESP32
        sock.connect((ip, port))
        # Send data as string (no JSON encoding)
        sock.send(data.encode())
        # Close socket
        sock.close()
        print(f"Data sent successfully to {ip}")
        return True
    except Exception as e:
        print(f"Error sending to {ip}: {str(e)}")
        return False

def main(weight_file_path: str,
         class_list_file_path: str,
         zones_file_path: str,
         detect_sensitivity: float,
         time_interval: float,
         frame_name: str,
         frame_height: int,
         frame_width: int,
         wait_key: int,
         ord_key: str,
         esp32_ip: list,
         esp32_port: list):
    
    # ESP32 device configurations
    esp32_devices = [
        {"name": "ESP32_1", "ip": esp32_ip[0], "port": esp32_port[0]},
        {"name": "ESP32_2", "ip": esp32_ip[1], "port": esp32_port[1]}
    ]

    # Initialize camera
    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (frame_width, frame_height)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()
    
    # Load YOLO model and configurations
    yolo_model = stls.load_model(weight_file_path)
    class_list = stls.load_class_names(class_list_file_path)
    zones, number_of_zones = stls.load_zones(zones_file_path)

    # Initialize zones and tracking data
    count = 0
    success = True
    zones_data = [{"countdown_start_time": 0.0, "refresh": False, "get_vehicle": None} for _ in range(number_of_zones)]
    previous_vehicle = [None, None]

    try:
        while success:
            current_time = time.time()
            frame = picam2.capture_array()

            count += 1
            if count % 3 != 0:
                continue

            zones_list = stls.init_zone_list(number_of_zones)
            frame = cv2.resize(frame, (frame_width, frame_height))
            boxes = stls.get_prediction_boxes(frame, yolo_model, detect_sensitivity)
            stls.draw_polylines_zones(frame, zones, frame_name)
            
            zones_list = stls.track_objects_in_zones(
                frame, boxes, class_list, zones, zones_list, frame_name)

            queuing_data = []
            for indx in range(number_of_zones):
                queuing_data.append(
                    stls.handle_zone_queuing(
                        indx, zones_list, current_time, frame, 
                        zones_data, time_interval))
                
                # Send data via WiFi to ESP32
                curr_time = queuing_data[indx]["current_time"]
                curr_vehic = queuing_data[indx]["vehicle"]
                if curr_time != 0.0 and previous_vehicle[indx] != curr_vehic:
                    # Send to corresponding ESP32 (assuming one ESP32 per zone)
                    if indx < len(esp32_devices):
                        device = esp32_devices[indx]
                        success = send_data_to_esp32(device["ip"], device["port"], curr_vehic)
                        if success:
                            previous_vehicle[indx] = curr_vehic
                            print(f"Vehicle data sent to {device['name']}")
                        else:
                            print(f"Failed to send data to {device['name']}.")

            stls.display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data)
            success = stls.show_frame(frame, frame_name, wait_key, ord_key)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        cv2.destroyAllWindows()