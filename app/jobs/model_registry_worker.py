import uuid, os
from celery import Celery
from celery import states
from celery.signals import task_sent, task_success, task_failure, task_prerun, task_postrun
from app.models.models import MLModel, ModelRegistryModel, UserModel, JobsModel
from app.constants import InstanceType as instance_type
from app.constants import SageMakerConstants as sm_constants
from app.core.SagemakerManager import SagemakerManager
from dotenv import load_dotenv

load_dotenv()

# Configure Celery to use the Redis broker
broker_url = os.getenv("RABBITMQ_URI")

worker = Celery("model_registry_worker", broker=broker_url)


@worker.task
def register_model_worker(model_uuid: str) -> tuple:
    sm = SagemakerManager(bucket_name=sm_constants.BUCKET_NAME, role=sm_constants.ROLE)
    record = MLModel.get_record_by_uuid(model_uuid)
    model = sm.create_model(model_path=record.s3_url, model_type=record.model_type)

    dummy_uuid_generator = str(uuid.uuid4())

    endpoint_name = sm.deploy_model(
        model=model,
        instance_type=instance_type.CPU,
        endpoint_name=f"dummy-endpoint-{dummy_uuid_generator}",
    ).endpoint_name

    return model_uuid, endpoint_name

@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    # mock session user
    user_uuid = UserModel.get_user_uuid_by_email("dummyUser@dummy.com")
    JobsModel.save_job_to_db(
        job_uuid=task_id,
        user_uuid=user_uuid,
        job_type="model_registry",
        job_status=states.PENDING,
        reference_uuid=None,
    )

@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    JobsModel.update_task_status(task_id, states.STARTED)

@task_success.connect
def task_success_handler(sender=None, result=None, *args, **kwargs):
    model_uuid, model_endpoint = result
    task_id = sender.request.id

    model_registry_uuid = ModelRegistryModel.register_model(
        model_uuid=model_uuid,
        model_version="1.0",
        model_status=states.SUCCESS,
        model_endpoint=model_endpoint,
    )

    JobsModel.update_task_status(task_id, states.SUCCESS)
    JobsModel.update_task_reference(task_id, model_registry_uuid)


@task_failure.connect
def task_failure_handler(task_id, *args, **kwargs):
    JobsModel.update_task_status(task_id, states.FAILURE)
