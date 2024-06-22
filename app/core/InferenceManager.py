import cv2
import os
from ultralytics import YOLO
from paddleocr import PaddleOCR
import boto3
from app.constants import AppConstants as app_constants
import logging
import subprocess

logger = logging.getLogger(__name__)


class InferenceManager:
    def __init__(self):
        self.bucket_name = os.getenv("BUCKET_NAME")
        self.s3_upload_path = "mesos"
        self.disk_download_path = app_constants.VIDEO_DOWNLOAD_TEMP_DIR
        self.disk_upload_path = app_constants.VIDEO_UPLOAD_TEMP_DIR
        self.storage_path = app_constants.DATA_UPLOAD_TEMP_DIR
        self.model_path = app_constants.MODEL_UPLOAD_TEMP_DIR
        self.display_real_time = False  # Set to True to enable real-time display
        self.confidence_threshold = os.environ.get('MODEL_CONF') or 0.5  # Confidence threshold for detections
        self.upload_to_s3 = True  # Set to True to upload video to S3

        os.makedirs(os.path.dirname(self.disk_download_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.disk_upload_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)

        self.model = YOLO(self.model_path)
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang="en",
            show_log=False,
        )

    def reencode_video_ffmpeg(self, input_path, output_path):
        command = [
            'ffmpeg',
            '-y',  # Automatically overwrite output files
            '-i', input_path,
            '-c:v', 'libx264',
            '-crf', '23',
            '-preset', 'fast',
            '-movflags', '+faststart',
            output_path
        ]

        # Check if the input video has an audio stream
        has_audio = self.check_audio_stream(input_path)
        if has_audio:
            command.extend(['-c:a', 'aac', '-b:a', '128k'])
        else:
            logger.info(f"No audio stream found in {input_path}. Skipping audio encoding.")

        try:
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            logger.info(f"FFmpeg output: {result.stdout}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise
        else:
            logger.info(f"Video re-encoded successfully")
            if os.path.exists(input_path):
                os.remove(input_path)
        

    def check_audio_stream(self, input_path):
        """Check if the input video has an audio stream"""
        command = [
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'a',
            '-show_entries', 'stream=codec_type',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            input_path
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return bool(result.stdout)

    def detect_car_plates_yolov8(self, inference_uuid):
        logger.info(f"Processing video {inference_uuid}.mp4")
        input_video_path = f"{self.disk_download_path}/{inference_uuid}.mp4"
        output_video_temp_path = f"{self.disk_upload_path}/{inference_uuid}_temp.mp4"
        output_video_path = f"{self.disk_upload_path}/{inference_uuid}.mp4"

        cap = cv2.VideoCapture(input_video_path)
        if not cap.isOpened():
            logger.error(f"Error: Could not open video file {input_video_path}")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        source_fps = int(cap.get(cv2.CAP_PROP_FPS))
        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )  # Try "mp4v", "XVID", "avc1", or "H264"

        out = cv2.VideoWriter(
            output_video_temp_path,
            fourcc,
            source_fps,
            (frame_width, frame_height),
        )

        if not out.isOpened():
            logger.error(f"Error: Could not open output video file {output_video_temp_path}")
            return

        plate_numbers_with_info = []
        frame_count = 0

        detection_area = {
            "x": 0,
            "y": 0,
            "width": frame_width,
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
                        logger.info(
                            f"Bounding box drawn: ({x}, {y}), ({x + w}, {y + h}), Text: {plate_number}"
                        )

            if self.display_real_time:
                cv2.imshow("License Plate Detection", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    logger.info(f"User interrupted the process")
                    break

            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()
        if self.display_real_time:
            cv2.destroyAllWindows()

        # Re-encode using FFmpeg
        self.reencode_video_ffmpeg(output_video_temp_path, output_video_path)

        if self.upload_to_s3:
            self.__upload_video_to_s3(inference_uuid)
        logger.info(
            f"Video uploaded to s3://{self.bucket_name}/{self.s3_upload_path}/{inference_uuid}.mp4"
        )
        response = {
            "output_video_path": f"s3://{self.bucket_name}/{self.s3_upload_path}/{inference_uuid}.mp4",
            "plate_numbers_with_info": plate_numbers_with_info,
        }
        return response

    def __upload_video_to_s3(self, inference_uuid):
        s3 = boto3.client("s3")
        s3.upload_file(
            f"{self.disk_upload_path}/{inference_uuid}.mp4",
            self.bucket_name,
            f"{self.s3_upload_path}/{inference_uuid}.mp4",
        )
        os.remove(f"{self.disk_upload_path}/{inference_uuid}.mp4")
