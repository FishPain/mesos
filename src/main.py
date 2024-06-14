from ultralytics import YOLO
import torch

def load_model(model_path):
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    model = YOLO(model_path).to(device)
    return model

if __name__ == '__main__':
    model_path = 'models/lpd.pt'
    model = load_model(model_path)
    # refer to docs for source_file_path and additional arguments
    model.predict(source="source_file_path", show=True, conf=0.7)