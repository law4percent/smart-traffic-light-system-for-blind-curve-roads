from picamera2 import Picamera2
import cv2
import numpy as np

points = []
entry_counter = 0

def click_event(event, x, y, flags, param):
    global points
    if event == cv2.EVENT_LBUTTONDOWN:
        points.append((x, y))
        redraw_frame(points, frame_copy, frame_name)

def redraw_frame(points, image, frame_name):
    temp_image = image.copy()
    if len(points) > 1:
        cv2.polylines(temp_image, [np.array(points)], isClosed=False, color=(0, 255, 0), thickness=2)
    for point in points:
        cv2.circle(temp_image, point, 5, (0, 0, 255), -1)
    cv2.imshow(frame_name, temp_image)

def save_points_to_file(file_path):
    global points, entry_counter
    with open(file_path, "a") as file:
        formatted_points = ', '.join([f"({x}, {y})" for x, y in points])
        file.write(f"{entry_counter}: [{formatted_points}]\n")
    print(f"Entry {entry_counter} saved to '{file_path}'.")
    points = []
    entry_counter += 1

def main(save_path, frame_height, frame_width):
    global points, frame_copy, frame_name

    picam2 = Picamera2()
    picam2.preview_configuration.main.size = (frame_width, frame_height)
    picam2.preview_configuration.main.format = "RGB888"
    picam2.preview_configuration.align()
    picam2.configure("preview")
    picam2.start()

    frame_name = "Writing Points Mode: RP"
    frame_idx = 0

    print("Press 'n' to move to the next frame, 's' to save points, 'c' to close the polygon, and 'q' to quit.")

    while True:
        frame = picam2.capture_array()
        frame_copy = frame.copy()

        cv2.imshow(frame_name, frame)
        cv2.setMouseCallback(frame_name, click_event)
        
        print(f"{frame_idx}: Left click to select points. Press 's' to save, 'c' to close the polygon, and 'q' to quit.")

        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s'):  # Save points to file
                save_points_to_file(save_path)
                redraw_frame(points, frame_copy, frame_name)
            elif key == ord('c'):  # Close the polygon
                if len(points) > 2:
                    cv2.polylines(frame_copy, [np.array(points)], isClosed=True, color=(255, 0, 0), thickness=2)
                    redraw_frame(points, frame_copy, frame_name)
                    print("Polygon closed.")
                else:
                    print("A polygon must have at least 3 points.")
            elif key == ord('n'):  # Next frame
                points = []
                frame_idx += 1
                break
            elif key == ord('q'):  # Quit
                picam2.stop()
                cv2.destroyAllWindows()
                return