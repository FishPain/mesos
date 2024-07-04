from app.jobs.inference_worker import start_inference
from app.models.models import InferenceModel
from app.models.models import JobsModel
from celery import states
import json
from datetime import datetime


def start_inference_by_model_uuid(temp_uuid):
    result = start_inference.apply_async(args=[temp_uuid])
    resp = {"uuid": result.task_id}
    return resp


def get_inference_by_uuid(uuid):
    inference_job = JobsModel.get_record_by_uuid(uuid)
    job_status = inference_job.job_status
    inference_output = None
    if job_status == states.SUCCESS:
        inference = InferenceModel.get_record_by_uuid(inference_job.reference_uuid)
        inference_output = inference.inference_output

    return {
        "status": job_status,
        "inference_result": json.loads(inference_output) if inference_output else None,
    }


def get_latest_inference_job():
    record = InferenceModel.get_latest_completed_record()
    if record is None:
        return None
    return {
        "inference_uuid": record.inference_uuid,
        "status": record.inference_status,
        "inference": record.inference_output,
    }


def get_all_inference_job():
    records = InferenceModel.get_all_inference_job()
    if records is None:
        return None
    l = list()
    for record in records:
        l.append(
            {
                "inference_uuid": record.inference_uuid,
                "status": record.inference_status,
                "inference_datetime": record.inference_datetime.strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
            }
        )
    return l


def delete_inference(inference_uuid):
    uuid = InferenceModel.delete_record_by_uuid(inference_uuid)
    return {"uuid": uuid}
