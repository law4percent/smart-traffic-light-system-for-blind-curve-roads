import cv2
from stls_lib import stls
import time
from picamera2 import Picamera2
import asyncio
from bleak import BleakServer, BleakAdvertisement, BleakCharacteristic
from bleak import BleakScanner


# BLE Server (Raspberry Pi)
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHARACTERISTIC_UUID = "87654321-1234-5678-1234-56789abcdef0"


class MyBLEServer:
    def __init__(self):
        self.server = None
        self.characteristic = None

    async def start_server(self):
        # Create a BLE advertisement
        advertisement = BleakAdvertisement(SERVICE_UUID)
        advertisement.add_service(SERVICE_UUID)

        # Create the server
        self.server = await BleakServer.create(advertisement)

        # Create a characteristic
        self.characteristic = BleakCharacteristic(CHARACTERISTIC_UUID)
        self.characteristic.write = self.on_write
        self.server.add_characteristic(self.characteristic)

        print("Raspberry Pi BLE Peripheral started...")
        await self.server.start()

    async def stop_server(self):
        await self.server.stop()
        print("Raspberry Pi BLE Peripheral stopped.")

    async def send_data(self, data):
        # Send data to connected client
        await self.characteristic.write(data.encode('utf-8'))
        print(f"Sent data: {data}")

    def on_write(self, characteristic, value):
        # Handle write from client (optional)
        print(f"Received data from client: {value}")


# Main function with BLE integration
async def main(weight_file_path: str,
                class_list_file_path: str,
                zones_file_path: str,
                detect_sensitivity: float,
                time_interval: float,
                frame_name: str,
                frame_height: int,
                frame_width: int,
                wait_key: int,
                ord_key: str):

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

    # Initialize BLE server
    raspberry_pi_ble = MyBLEServer()
    await raspberry_pi_ble.start_server()

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
            
            # Send data via BLE
            curr_time = queuing_data[indx]["current_time"]
            curr_vehic = queuing_data[indx]["vehicle"]
            if curr_time != 0.0:
                if previous_vehicle[indx] != curr_vehic:
                    # Send data to ESP32 using BLE
                    await raspberry_pi_ble.send_data(curr_vehic)
                    previous_vehicle[indx] = curr_vehic

        stls.display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data)  # Optional
        success = stls.show_frame(frame, frame_name, wait_key, ord_key)  # Optional

    # Cleanup
    await raspberry_pi_ble.stop_server()
    cv2.destroyAllWindows()