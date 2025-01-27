import cv2
from stls_lib import stls
import time
from picamera2 import Picamera2
import paho.mqtt
import paho.mqtt.client as mqtt


def on_publish(client, userdata, mid):
    print("message published")


def safe_publish(client, topic, message, qos=0):
    # Check if the client is connected
    if not client.is_connected():
        print("Client is not connected. Attempting to reconnect...")
        try:
            client.reconnect()
            print("Reconnected successfully.")
        except Exception as e:
            print(f"Error reconnecting: {e}")
            return  # Exit if reconnection fails
    
    try:
        # Publish message
        pubMsg = client.publish(topic, message.encode('utf-8'), qos=qos)
        pubMsg.wait_for_publish()  # Wait for the publish to complete
        print("Message published successfully.")
    except Exception as e:
        print(f"Message publish failed: {e}")


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
         mqtt_broker: str,  # "192.168.1.100" Replace with Raspberry Pi's static IP
         mqtt_port: int  # 1883 default port
         ):
    
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

    topic_esp = ["esp32/one", "esp32/two"]

    if paho.mqtt.__version__[0] > '1':
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1, "RaspberryPi")
    else:
        client = mqtt.Client("RaspberryPi")
        
    client.connect(mqtt_broker, mqtt_port)
    client.on_publish = on_publish
    client.loop_start()  # Start the MQTT loop for handling background tasks

    # Initialize zones and tracking data
    count = 0
    success = True
    zones_data = [{"countdown_start_time": 0.0, "refresh": False, "get_vehicle": None} for _ in range(number_of_zones)]
    previous_vehicle = [None, None]

    while success:
        current_time = time.time()
        frame = picam2.capture_array()

        count += 1
        if count % 3 != 0:
            continue

        zones_list = stls.init_zone_list(number_of_zones)
        frame = cv2.resize(frame, (frame_width, frame_height))
        boxes = stls.get_prediction_boxes(frame, yolo_model, detect_sensitivity)
        stls.draw_polylines_zones(frame, zones, frame_name)  # Optional
        zones_list = stls.track_objects_in_zones(frame, boxes, class_list, zones, zones_list, frame_name)

        queuing_data = []
        for indx in range(number_of_zones):
            queuing_data.append(stls.handle_zone_queuing(indx, zones_list, current_time, frame, zones_data, time_interval))
            
            # Publish data
            curr_time = queuing_data[indx]["current_time"]

            curr_vehic = queuing_data[indx]["vehicle"]
            if curr_time != 0.0:
                if previous_vehicle[indx] != curr_vehic:
                    # Use safe_publish to ensure client is connected before publishing
                    safe_publish(client, topic_esp[indx], curr_vehic, qos=0)
                    previous_vehicle[indx] = curr_vehic

        stls.display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data)  # Optional
        success = stls.show_frame(frame, frame_name, wait_key, ord_key)  # Optional

    # Cleanup
    client.loop_stop()
    client.disconnect()
    cv2.destroyAllWindows()
