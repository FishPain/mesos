import os
from celery import Celery
from celery import states
from celery.signals import (
    task_success,
    task_failure,
    task_prerun,
)
from app.models.models import UserModel, JobsModel, InferenceModel
from app.constants import JobConstants as job_constants
from app.core.InferenceManager import image_preprocessor
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage

load_dotenv()

# Configure Celery to use the Redis broker
broker_url = os.getenv("RABBITMQ_URI")

worker = Celery("inference_worker", broker=broker_url)

@worker.task
def start_inference(model: FileStorage, image: FileStorage) -> tuple:
    data = image_preprocessor(image)
    resp = model.predict(data)
    return resp


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    # mock session user
    user_uuid = UserModel.get_user_uuid_by_email("dummyUser@dummy.com")
    JobsModel.save_job_to_db(
        job_uuid=task_id,
        user_uuid=user_uuid,
        job_type=job_constants.START_INFERENCE,
        job_status=states.STARTED,
        reference_uuid=None,
    )


@task_success.connect
def task_success_handler(sender=None, result=None, *args, **kwargs):
    task_id = sender.request.id
    user_uuid = JobsModel.get_record_by_uuid(task_id).user_uuid

    model_uuid = InferenceModel.save_inference_to_db(
        user_uuid=user_uuid,
        model_registry_uuid = model_uuid,
        inference_status=states.SUCCESS,
        inference_output=result
    )
    JobsModel.update_task_status(task_id, states.SUCCESS)


@task_failure.connect
def task_failure_handler(task_id, *args, **kwargs):
    JobsModel.update_task_status(task_id, states.FAILURE)