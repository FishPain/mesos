import cv2
import os
import torch
from ultralytics import YOLO
from collections import defaultdict
import numpy as np
from paddleocr import PaddleOCR
import json
import boto3


def download_video_from_s3(bucket_name, video_key, download_path):
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, video_key, download_path)


def upload_video_to_s3(bucket_name, video_path, s3_key):
    s3 = boto3.client("s3")
    s3.upload_file(video_path, bucket_name, s3_key)


def store_plate_numbers_with_info(plate_numbers_with_info, consistent_plates, storage_path):
    os.makedirs(os.path.dirname(storage_path), exist_ok=True)
    data_to_store = {
        "plate_numbers": plate_numbers_with_info,
        "consistent_plates": consistent_plates,
    }
    with open(storage_path, "w") as f:
        json.dump(data_to_store, f, indent=4)


def detect_car_plates_yolov8(
    video_path,
    output_video_path,
    model_path,
    display_real_time=False,
    output_fps=None,
    duration_threshold=30,
    confidence_threshold=0.75,
    upload_to_s3=False,
    bucket_name=None,
    s3_key=None
):
    model = YOLO(model_path)
    ocr = PaddleOCR(use_angle_cls=True, lang="en")
    cap = cv2.VideoCapture(video_path)
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    source_fps = int(cap.get(cv2.CAP_PROP_FPS))
    output_fps = output_fps or source_fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(
        output_video_path, fourcc, output_fps, (frame_width, frame_height)
    )

    if not out.isOpened():
        print(f"Error: Could not open output video file {output_video_path}")
        return
    
    frame_info = []
    plate_tracks = defaultdict(list)
    plate_ids = {}
    plate_numbers_with_info = []
    frame_count = 0

    # Calculate the detection area
    detection_area = {
        "x": frame_width // 2 - 200,
        "y": 0,
        "width": 400,
        "height": frame_height
    }
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = model(frame)
        current_frame_plates = []
        for result in results:
            for detection in result.boxes:
                x1, y1, x2, y2 = detection.xyxy[0]
                conf = detection.confidence
                if conf < confidence_threshold:
                    continue
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
                    plate_frame_resized = cv2.resize(plate_frame, (0, 0), fx=0.5, fy=0.5)

                    ocr_result = ocr.ocr(plate_frame_resized, cls=True)
                    plate_number = ""
                    if ocr_result and len(ocr_result[0]) > 0:
                        plate_number, conf = ocr_result[0][0][1]
                    plate_numbers_with_info.append(
                        {
                            "frame_number": frame_count,
                            "bounding_box": (x, y, w, h),
                            "plate_number": plate_number,
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

        # Track plates over frames
        for x, y, w, h in current_frame_plates:
            plate_id = find_plate_id(plate_ids, x, y, w, h)
            if plate_id is None:
                plate_id = len(plate_ids)
                plate_ids[plate_id] = (x, y, w, h)
            plate_tracks[plate_id].append(frame_count)

        # Display the frame if the toggle is enabled
        if display_real_time:
            cv2.imshow("License Plate Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        out.write(frame)
        frame_count += 1

    cap.release()
    out.release()
    if display_real_time:
        cv2.destroyAllWindows()

    # Identify plates in view for at least duration_threshold seconds
    consistent_plates = [
        plate_id
        for plate_id, frames in plate_tracks.items()
        if len(frames) >= duration_threshold * source_fps
    ]

    # Upload the video to S3 if required
    if upload_to_s3 and bucket_name and s3_key:
        upload_video_to_s3(bucket_name, output_video_path, s3_key)
        print(f"Video uploaded to S3: s3://{bucket_name}/{s3_key}")
    else:
        print(f"Video saved locally: {output_video_path}")

    return plate_numbers_with_info, consistent_plates


def find_plate_id(plate_ids, x, y, w, h, iou_threshold=0.5):
    for plate_id, (px, py, pw, ph) in plate_ids.items():
        iou = calculate_iou((x, y, w, h), (px, py, pw, ph))
        if iou > iou_threshold:
            return plate_id
    return None


def calculate_iou(box1, box2):
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    xi1 = max(x1, x2)
    yi1 = max(y1, y2)
    xi2 = min(x1 + w1, x2 + w2)
    yi2 = min(y1 + h1, y2 + h2)
    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)
    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area
    iou = inter_area / union_area
    return iou


if __name__ == "__main__":
    bucket_name = "your-bucket-name"
    video_key = "path/to/your/s3/video.mp4"
    download_path = "models/video.mp4"
    output_video_path = "run/output/annotated_video.mp4"
    storage_path = "run/plate_numbers_with_info.json"
    model_path = "models/lpd.pt"
    duration_threshold = 30  # seconds
    display_real_time = True  # Set to True to enable real-time display
    output_fps = None  # Set a specific fps or leave None to follow source video fps
    confidence_threshold = 0.75  # Confidence threshold for detections
    upload_to_s3 = False  # Set to True to upload video to S3
    s3_key = "path/to/your/s3/output_video.mp4"

    # Step 1: Download video
    # download_video_from_s3(bucket_name, video_key, download_path)

    # Step 2: Detect car plates and draw bounding boxes using YOLOv8
    plate_numbers_with_info, consistent_plates = detect_car_plates_yolov8(
        download_path,
        output_video_path,
        model_path,
        display_real_time,
        output_fps,
        duration_threshold,
        confidence_threshold,
        upload_to_s3,
        bucket_name,
        s3_key
    )

    # Step 3: Store the plate numbers with frame information
    store_plate_numbers_with_info(
        plate_numbers_with_info, consistent_plates, storage_path
    )
