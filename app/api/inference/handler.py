from app.jobs.inference_worker import start_inference

def start_inference_by_model_uuid(model_uuid, data):
    model = None

    if not model:
        raise Exception("Model does not exist")
    
    result = start_inference.apply_async(args=[model, data])
    resp = {
        "uuid": result.task_id
    }

    return resp