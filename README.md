# Smart Traffic Light System

## Overview

The **Smart Traffic Light System** is designed to enhance traffic management on curved roads, where blind spots often occur. The system uses a centrally positioned camera to monitor both the left and right sides of the road. Two traffic lights are installed — one on the left side and one on the right side of the road.

The system is programmed to detect vehicles in both directions:

- If the **right side** detects vehicles, the **left traffic light** will turn red, ensuring that traffic is halted on the left side to prioritize flow on the right.
- Conversely, if the **left side** detects vehicles, the **right traffic light** will turn red to prioritize the left side of the road.

This dynamic control system improves traffic flow and safety, especially in areas with limited visibility or blind spots due to road curves.



## Configuration Parameters

The behavior of the Smart Traffic Light System is controlled through the `root_data.txt` configuration file. Below is an explanation of the key parameters you can customize:

### `device`
Defines the processing device. Options:

- **`pc`**: Use your personal computer for processing.
- **`rp`**: Use a Raspberry Pi device for processing (useful for edge deployments).

### `write_points_mode`
- **`True`** or **`False`**. If set to `True`, the program will allow you to **draw a new zone pattern** on the video frame by specifying points to define new zones for vehicle detection.

### `detect_sensivity`
A floating-point value ranging from **0.10 to 0.90**. This defines the sensitivity threshold for vehicle detection:

- A lower value (e.g., `0.10`) makes it easier to detect vehicles, potentially increasing the number of detections.
- A higher value (e.g., `0.90`) makes the detection more strict, which can help reduce false positives.

### `frame_name`
The title of the display window, typically **"Smart Traffic System"**.

### `frame_height` & `frame_width`
Defines the resolution of the video frame for processing. Example values might be:

- `frame_height: 800`
- `frame_width: 1280`

These values control the size of the frame being processed by the system.

### `time_interval`
A floating-point number (in seconds) to set the countdown timer between traffic light changes. Example value:

- `time_interval: 3.0` (The system will wait 3 seconds before changing the traffic light state).

### `video_source`
The path to the video file or live video stream that the system will analyze for traffic monitoring. Example value:

- `video_source: src/inference/videos/video.mp4`

### `weight_file_path`
The path to the trained YOLO weights file used for vehicle detection. Example value:

- `weight_file_path: src/YOLO11_training/train_result/weights/best.pt`

### `class_list_file_path`
The path to a file containing the names of the objects/classes detected by the YOLO model. These might include classes such as:

- `vehicle`
- `pedestrian`
- Other detected classes (defined in your model)

Example value:

- `class_list_file_path: src/utils/class.names`

### `zones_file_path`
The path to a file containing the traffic zone definitions for detecting and tracking vehicles in different areas of the traffic network. Example value:

- `zones_file_path: src/utils/zones.txt`

### `wait_key`
OpenCV `waitKey` delay in milliseconds for each frame. Example value:

- `wait_key: 1` (1ms delay for each frame).

### `ord_key`
The key to exit the program. The default key is **`q`**. If you wish to change it to another key, modify this parameter accordingly. Example value:

- `ord_key: q`



## Installation and Running the Program

After configuring the `root_data.txt` file with your desired settings, you can run the program by executing the following command:

```bash
pip install -r requirements.txt # To install all the requirements and dependencies

python main.py                  # To run the program
