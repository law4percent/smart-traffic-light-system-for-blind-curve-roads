from stls_lib import stls
import asyncio

if __name__ == "__main__":
    data = stls.extract_data(file_path="src/utils/root_data.txt")

    if data["device"].lower() == "rp":
        if data["write_points_mode"].lower() == "true":
            from stls_lib.rp import rp_write_points
            rp_write_points.main(
                    save_path = data["zones_file_path"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                    ord_key = data["ord_key"],
                )
            exit()
        elif data["write_points_mode"].lower() != "false":
            print("\nInvalid input found at data[\"write_points_mode\"]. Input must be between True and False.")


        if data["communication_protocol"].lower() == "mqtt":
            from stls_lib.rp import rp_process_video_MQTT
            rp_process_video_MQTT.main(
                    weight_file_path = data["weight_file_path"],
                    class_list_file_path = data["class_list_file_path"],
                    zones_file_path = data["zones_file_path"],
                    detect_sensitivity = data["detect_sensitivity"],
                    frame_name = data["frame_name"],
                    time_interval = data["time_interval"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                    wait_key = data["wait_key"],
                    ord_key = data["ord_key"],
                    mqtt_broker=data["mqtt_broker"],
                    mqtt_port=data["mqtt_port"]
                )
        elif data["communication_protocol"].lower() == "ble":
            from stls_lib.rp import rp_process_video_BLE
            asyncio.run(rp_process_video_BLE.main(
                    weight_file_path = data["weight_file_path"],
                    class_list_file_path = data["class_list_file_path"],
                    zones_file_path = data["zones_file_path"],
                    detect_sensitivity = data["detect_sensitivity"],
                    frame_name = data["frame_name"],
                    time_interval = data["time_interval"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                    wait_key = data["wait_key"],
                    ord_key = data["ord_key"]
                ))
        elif data["communication_protocol"].lower() == "socket":
            from stls_lib.rp import rp_process_video_socket
            rp_process_video_socket.main(
                    weight_file_path = data["weight_file_path"],
                    class_list_file_path = data["class_list_file_path"],
                    zones_file_path = data["zones_file_path"],
                    detect_sensitivity = data["detect_sensitivity"],
                    frame_name = data["frame_name"],
                    time_interval = data["time_interval"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                    wait_key = data["wait_key"],
                    ord_key = data["ord_key"],
                    esp32_ip = [data["IP_ESP32_1"], data["IP_ESP32_2"]],
                    esp32_port = [data["ESP32_port_1"], data["ESP32_port_2"]],
                )
        else:
            print("\nInvalid input found at data[\"communication_protocol\"]. Input must be between socket, ble and mqtt.")
        
    elif data["device"].lower() == "pc":
        if data["write_points_mode"].lower() == "true":
            from stls_lib.pc import pc_write_points
            pc_write_points.main(
                    video_source = data["video_source"],
                    save_path = data["zones_file_path"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                    ord_key = data["ord_key"],
                )
            exit()
        elif data["write_points_mode"].lower() != "false":
            print("\nInvalid input found at data[\"write_points_mode\"]. Input must be between True and False.")

        from stls_lib.pc import pc_video_process
        pc_video_process.main(
                video_source = data["video_source"],
                weight_file_path = data["weight_file_path"],
                class_list_file_path = data["class_list_file_path"],
                zones_file_path = data["zones_file_path"],
                detect_sensitivity = data["detect_sensitivity"],
                frame_name = data["frame_name"],
                time_interval = data["time_interval"],
                frame_height = data["frame_height"],
                frame_width = data["frame_width"],
                wait_key = data["wait_key"],
                ord_key = data["ord_key"]
            )
    
    else:
        print("\nInvalid input found at data[\"device\"]. Input must be between pc and rp.")