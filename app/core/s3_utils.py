import boto3
import botocore


def download_video_from_s3(bucket_name, s3_download_path, disk_download_path):
    s3 = boto3.client("s3")
    s3.download_file(bucket_name, s3_download_path, disk_download_path)


def upload_video_to_s3(disk_upload_path, bucket_name, s3_upload_path):
    s3 = boto3.client("s3")
    s3.upload_file(disk_upload_path, bucket_name, s3_upload_path)


def get_s3_file(bucket_name, file_key, range_header=None):
    try:
        s3 = boto3.client("s3")
        if range_header:
            s3_response = s3.get_object(
                Bucket=bucket_name, Key=file_key, Range=range_header
            )
        else:
            s3_response = s3.get_object(Bucket=bucket_name, Key=file_key)
        return (
            s3_response["Body"],
            s3_response["ContentType"],
            s3_response.get("ContentRange"),
            s3_response.get("ContentLength"),
        )
    except botocore.exceptions.ClientError as e:
        print(f"Error fetching file from S3: {e}")
        return None, None, None, None
