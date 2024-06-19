import cv2
import os
from ultralytics import YOLO
from paddleocr import PaddleOCR
import json
import boto3
from app.constants import AppConstants as app_constants


class InferenceManager:
    def __init__(self):
        self.bucket_name = "your-bucket-name"
        self.s3_download_path = "path/to/your/s3/video.mp4"
        self.s3_upload_path = "path/to/your/s3/output_video.mp4"
        self.disk_download_path = app_constants.VIDEO_DOWNLOAD_TEMP_DIR
        self.disk_upload_path = app_constants.VIDEO_UPLOAD_TEMP_DIR
        self.storage_path = app_constants.DATA_UPLOAD_TEMP_DIR
        self.model_path = "model_resources/lpd.pt"
        self.display_real_time = False  # Set to True to enable real-time display
        self.output_fps = None
        self.confidence_threshold = 0.95  # Confidence threshold for detections
        self.upload_to_s3 = True  # Set to True to upload video to S3

        os.makedirs(os.path.dirname(self.disk_download_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.disk_upload_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        self.model = YOLO(self.model_path)
        self.ocr = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)

    def detect_car_plates_yolov8(self):
        self.__download_video_from_s3()
        cap = cv2.VideoCapture(self.disk_download_path)
        frame_width = int(cap.get(3))
        frame_height = int(cap.get(4))
        source_fps = int(cap.get(cv2.CAP_PROP_FPS))
        output_fps = output_fps or source_fps
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(
            self.disk_upload_path, fourcc, output_fps, (frame_width, frame_height)
        )

        if not out.isOpened():
            print(f"Error: Could not open output video file {self.disk_upload_path}")
            return

        frame_info = []
        plate_numbers_with_info = []
        frame_count = 0
        # Calculate the detection area
        detection_area = {
            "x": frame_width * 0.25,
            "y": 0,
            "width": (frame_width * 0.75) - (frame_width * 0.25),
            "height": frame_height,
        }

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            results = self.model(frame)
            current_frame_plates = []
            for result in results:
                for detection in result.boxes:
                    x1, y1, x2, y2 = detection.xyxy[0]
                    x, y, w, h = int(x1), int(y1), int(x2 - x1), int(y2 - y1)
                    if (
                        x > detection_area["x"]
                        and y > detection_area["y"]
                        and x + w < detection_area["x"] + detection_area["width"]
                        and y + h < detection_area["y"] + detection_area["height"]
                    ):
                        current_frame_plates.append((x, y, w, h))
                        plate_frame = frame[y : y + h, x : x + w]

                        # Resize the frame to speed up OCR
                        plate_frame_resized = cv2.resize(
                            plate_frame, (0, 0), fx=0.5, fy=0.5
                        )

                        ocr_result = self.ocr.ocr(plate_frame_resized, cls=True)
                        plate_number, conf = (
                            ocr_result[0][0][1]
                            if ocr_result and ocr_result[0] and len(ocr_result[0]) > 0
                            else ("", 0)
                        )
                        if conf < self.confidence_threshold:
                            continue

                        plate_numbers_with_info.append(
                            {
                                "frame_number": frame_count,
                                "bounding_box": (x, y, w, h),
                                "plate_number": plate_number,
                                "confidence": conf,
                            }
                        )
                        frame_info.append(
                            {"frame_number": frame_count, "bounding_box": (x, y, w, h)}
                        )
                        # Draw bounding box and text on the frame
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        cv2.putText(
                            frame,
                            plate_number,
                            (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.9,
                            (255, 0, 0),
                            2,
                        )
                        print(
                            f"Bounding box drawn: ({x}, {y}), ({x + w}, {y + h}), Text: {plate_number}"
                        )

            # Display the frame if the toggle is enabled
            if self.display_real_time:
                cv2.imshow("License Plate Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()
        if self.display_real_time:
            cv2.destroyAllWindows()

        # Upload the video to S3 if required
        if self.upload_to_s3 and self.bucket_name and self.s3_upload_path:
            self.__upload_video_to_s3()
            print(
                f"Video uploaded to S3: s3://{self.bucket_name}/{self.s3_upload_path}"
            )
        else:
            print(f"Video saved locally: {self.disk_upload_path}")

        self.__store_plate_numbers_with_info(plate_numbers_with_info, self.storage_path)

        response = {
            "output_video_path": f"s3://{self.bucket_name}/{self.s3_upload_path}",
            "plate_numbers_with_info": plate_numbers_with_info,
        }

        return response
    
    def __download_video_from_s3(self):
        s3 = boto3.client("s3")
        s3.download_file(
            self.bucket_name, self.s3_download_path, self.disk_download_path
        )

    def __upload_video_to_s3(self):
        s3 = boto3.client("s3")
        s3.upload_file(self.disk_upload_path, self.bucket_name, self.s3_upload_path)

    def __store_plate_numbers_with_info(self, plate_numbers_with_info, storage_path):
        data_to_store = {"plate_numbers": plate_numbers_with_info}
        with open(storage_path, "w") as f:
            json.dump(data_to_store, f, indent=4)
