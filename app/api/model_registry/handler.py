import boto3
from app.constants import SageMakerConstants as sm_constants
from app.jobs.model_registry_worker import register_model_worker
from app.models.models import ModelRegistryModel, InferenceModel


def register_model(model_uuid):
    result = register_model_worker.apply_async(args=[model_uuid])
    return result.task_id


def clean_up_model_resources(model_uuid, endpoint_name):
    """This function deletes the endpoint, endpoint configuration, and model resources from SageMaker."""

    # Create a low-level SageMaker service client.
    sagemaker_client = boto3.client("sagemaker", region_name=sm_constants.REGION)

    # Store DescribeEndpointConfig response into a variable that we can index in the next step.
    response = sagemaker_client.describe_endpoint_config(
        EndpointConfigName=endpoint_name
    )

    # Delete endpoint
    model_name = response["ProductionVariants"][0]["ModelName"]

    sagemaker_client.delete_model(ModelName=model_name)

    sagemaker_client.delete_endpoint_config(EndpointConfigName=endpoint_name)

    sagemaker_client.delete_endpoint(EndpointName=endpoint_name)

    # delete from inference table due to foreign key constraint
    inference_uuid = InferenceModel.get_record_by_model_registry_uuid(model_uuid)
    if inference_uuid:
        InferenceModel.delete_record_by_uuid(inference_uuid)

    ModelRegistryModel.delete_record_by_uuid(model_uuid)