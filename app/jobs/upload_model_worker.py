import os
from celery import Celery
from celery import states
from celery.signals import (
    task_success,
    task_failure,
    task_prerun,
)
from app.models.models import MLModel, UserModel, JobsModel
from app.constants import AppConstants as app_constants
from app.constants import JobConstants as job_constants
from dotenv import load_dotenv
from werkzeug.datastructures import FileStorage

load_dotenv()

# Configure Celery to use the Redis broker
broker_url = os.getenv("RABBITMQ_URI")

worker = Celery("upload_model_worker", broker=broker_url)

@worker.task
def upload_model(model: FileStorage) -> tuple:
    upload_dir = app_constants.MODEL_UPLOAD_TEMP_DIR

    # Create the directory if it doesn't exist
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)

    # Save the uploaded file to the specified directory
    file_path = os.path.join(upload_dir, model.filename)
    model.save(file_path)
    return file_path, model.filename


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    # mock session user
    user_uuid = UserModel.get_user_uuid_by_email("dummyUser@dummy.com")
    JobsModel.save_job_to_db(
        job_uuid=task_id,
        user_uuid=user_uuid,
        job_type=job_constants.UPLOAD_MODEL,
        job_status=states.STARTED,
        reference_uuid=None,
    )

@task_success.connect
def task_success_handler(sender=None, result=None, *args, **kwargs):
    file_path, filename = result
    task_id = sender.request.id

    # Save the model to the database
    model_type = "tensorflow"  # TODO: Add support for other model types
    model_uuid = MLModel.save_model_to_db(
        model_name=filename, model_type=model_type, s3_url=file_path
    )

    JobsModel.update_task_status(task_id, states.SUCCESS)


@task_failure.connect
def task_failure_handler(task_id, *args, **kwargs):
    JobsModel.update_task_status(task_id, states.FAILURE)