import os
from pathlib import Path

WORKSPACE_DIR = Path(os.environ.get("YOLO_WORKSPACE", "workspace")).resolve()
IMAGES_DIR = Path(os.environ.get("YOLO_IMAGES", str(WORKSPACE_DIR / "images"))).resolve()
LABELS_DIR = Path(os.environ.get("YOLO_LABELS", str(WORKSPACE_DIR / "labels"))).resolve()
CLASSES_FILE = Path(os.environ.get("YOLO_CLASSES", str(WORKSPACE_DIR / "classes.txt"))).resolve()
OUTPUT_DIR = Path(os.environ.get("YOLO_OUTPUT", "dataset")).resolve()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
