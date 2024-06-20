import os
import json
from celery import Celery
from celery import states
from celery.signals import (
    task_success,
    task_failure,
    task_prerun,
)
from app.models.models import UserModel, JobsModel, InferenceModel
from app.constants import JobConstants as job_constants
from app.core.InferenceManager import InferenceManager
from dotenv import load_dotenv

load_dotenv()

# Configure Celery to use the Redis broker
broker_url = os.getenv("RABBITMQ_URI")

worker = Celery("inference_worker", broker=broker_url)

inference_manager = InferenceManager()


@worker.task(bind=True)
def start_inference(self) -> tuple:
    # get the task id here
    return inference_manager.detect_car_plates_yolov8(self.request.id)


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    # mock session user
    user_uuid = UserModel.get_user_uuid_by_email("dummyUser@dummy.com")
    model_uuid = InferenceModel.save_inference_to_db(
        inference_uuid=task_id,
        user_uuid=user_uuid,
        inference_status=states.STARTED,
        inference_output=None,
    )
    JobsModel.save_job_to_db(
        job_uuid=task_id,
        user_uuid=user_uuid,
        job_type=job_constants.START_INFERENCE,
        job_status=states.STARTED,
        reference_uuid=model_uuid,
    )


@task_success.connect
def task_success_handler(sender=None, result=None, *args, **kwargs):
    task_id = sender.request.id
    InferenceModel.update_inference_status(task_id, states.SUCCESS)
    InferenceModel.update_inference_output(task_id, json.dumps(result))
    JobsModel.update_task_status(task_id, states.SUCCESS)


@task_failure.connect
def task_failure_handler(task_id, *args, **kwargs):
    JobsModel.update_task_status(task_id, states.FAILURE)
