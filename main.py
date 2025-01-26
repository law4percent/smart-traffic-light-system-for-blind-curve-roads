from stls_lib import stls


if __name__ == "__main__":
    data = stls.extract_data(file_path="src/utils/root_data.txt")

    if data["device"].lower() == "rp":
        if data["write_points_mode"].lower() == "true":
            from stls_lib.rp import rp_write_points
            rp_write_points.main(
                    save_path = data["zones_file_path"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                )

        from stls_lib.rp import rp
        rp.main(
                weight_file_path = data["weight_file_path"],
                class_list_file_path = data["class_list_file_path"],
                zones_file_path = data["zones_file_path"],
                detect_sensivity = data["detect_sensivity"],
                frame_name = data["frame_name"],
                time_interval = data["time_interval"],
                frame_height = data["frame_height"],
                frame_width = data["frame_width"],
                wait_key = data["wait_key"],
                ord_key = data["ord_key"]
            )
        
    elif data["device"].lower() == "pc":
        if data["write_points_mode"].lower() == "true":
            from stls_lib.pc import pc_write_points
            pc_write_points.main(
                    video_source = data["video_source"],
                    save_path = data["zones_file_path"],
                    frame_height = data["frame_height"],
                    frame_width = data["frame_width"],
                )

        from stls_lib.pc import pc
        pc.main(
                video_source = data["video_source"],
                weight_file_path = data["weight_file_path"],
                class_list_file_path = data["class_list_file_path"],
                zones_file_path = data["zones_file_path"],
                detect_sensivity = data["detect_sensivity"],
                frame_name = data["frame_name"],
                time_interval = data["time_interval"],
                frame_height = data["frame_height"],
                frame_width = data["frame_width"],
                wait_key = data["wait_key"],
                ord_key = data["ord_key"]
            )
    
    else:
        print("Invalid input found data[\"device\"]. Input must be between pc or rp")