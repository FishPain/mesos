from app.jobs.inference_worker import start_inference
from app.models.models import InferenceModel
from app.models.models import JobsModel
from celery import states
import json


def start_inference_by_model_uuid():
    result = start_inference.apply_async()
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
