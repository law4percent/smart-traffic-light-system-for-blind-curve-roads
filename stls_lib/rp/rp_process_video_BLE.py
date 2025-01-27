import cv2
from stls_lib import stls
import time
from picamera2 import Picamera2
import asyncio
from bleak import BleakClient
from bleak import BleakGATTCharacteristic
from bleak_retry_connector import establish_connection
import dbus
from bleak.backends.bluezdbus.service import BleakGATTService
from bleak.backends.bluezdbus.characteristic import BleakGATTCharacteristic

# BLE UUIDs
SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
CHARACTERISTIC_UUID = "87654321-1234-5678-1234-56789abcdef0"

class BLEPeripheral:
    def __init__(self):
        self.clients = set()
        self.service = None
        self.characteristic = None
        self.is_advertising = False

    async def setup(self):
        # Set up D-Bus system bus
        bus = dbus.SystemBus()
        
        # Create GATT service
        self.service = BleakGATTService(SERVICE_UUID)
        
        # Create characteristic
        self.characteristic = BleakGATTCharacteristic(
            uuid=CHARACTERISTIC_UUID,
            service_uuid=SERVICE_UUID,
            properties=["read", "write", "notify"],
        )
        self.service.add_characteristic(self.characteristic)

    async def start_advertising(self):
        if not self.is_advertising:
            # Start advertising the service
            self.is_advertising = True
            print("Started advertising...")

    async def stop_advertising(self):
        if self.is_advertising:
            self.is_advertising = False
            print("Stopped advertising...")

    async def send_notification(self, data: str):
        # Convert string data to bytes
        data_bytes = data.encode('utf-8')
        
        # Send notification to all connected clients
        for client in self.clients:
            try:
                await client.write_gatt_char(CHARACTERISTIC_UUID, data_bytes)
                print(f"Sent notification: {data}")
            except Exception as e:
                print(f"Failed to send notification: {e}")
                self.clients.remove(client)

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

    # Initialize BLE peripheral
    ble_peripheral = BLEPeripheral()
    await ble_peripheral.setup()
    await ble_peripheral.start_advertising()

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
                
                # Send data via BLE
                curr_time = queuing_data[indx]["current_time"]
                curr_vehic = queuing_data[indx]["vehicle"]
                if curr_time != 0.0:
                    if previous_vehicle[indx] != curr_vehic:
                        # Send data to ESP32 using BLE
                        await ble_peripheral.send_notification(str(curr_vehic))
                        previous_vehicle[indx] = curr_vehic

            stls.display_zone_info(frame, number_of_zones, zones_list, frame_name, queuing_data)
            success = stls.show_frame(frame, frame_name, wait_key, ord_key)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # Cleanup
        await ble_peripheral.stop_advertising()
        cv2.destroyAllWindows()