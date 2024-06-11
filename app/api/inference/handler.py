from app.models.models import MLModel
from app.jobs.inference_worker import start_inference

def get_model_path(model_uuid):
    model = MLModel.get_record_by_uuid(model_uuid)
    if not model:
        raise Exception("Model does not exist")

    resp = {
        "uuid": model_uuid,
        "local_filepath_list": [model.s3_url],
    }

    return resp

def start_inference_by_model_uuid(model_uuid, data):
    model = MLModel.get_record_by_uuid(model_uuid)

    if not model:
        raise Exception("Model does not exist")
    
    result = start_inference.apply_async(args=[model, data])
    resp = {
        "uuid": result.task_id
    }

    return resp