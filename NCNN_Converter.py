from ultralytics import YOLO

# Load a YOLOv8n PyTorch model
model = YOLO("yolo11s.pt")

# Export the model to NCNN format
model.export(format="ncnn", imgsz=320)  # creates 'yolo11s_ncnn_model'
