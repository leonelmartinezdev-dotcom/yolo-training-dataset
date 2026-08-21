import os
from pathlib import Path

WORKSPACE_DIR = Path(os.environ.get("YOLO_WORKSPACE", "workspace")).resolve()
IMAGES_DIR = Path(os.environ.get("YOLO_IMAGES", str(WORKSPACE_DIR / "images"))).resolve()
# Etiquetas manuales: lo que escribe la UI de etiquetado. Fuente de verdad del humano.
LABELS_DIR = Path(os.environ.get("YOLO_LABELS", str(WORKSPACE_DIR / "labels"))).resolve()
# Etiquetas fusionadas (manuales + pseudo-COCO) que genera scripts/pseudolabel.py.
# El export las prefiere si existen: entrenar solo con las manuales convierte todo
# objeto COCO sin etiquetar en fondo y le borra al modelo las clases preentrenadas.
# Si el directorio no existe, el export cae de vuelta a LABELS_DIR.
EXPORT_LABELS_DIR = Path(
    os.environ.get("YOLO_EXPORT_LABELS", str(WORKSPACE_DIR / "labels_auto"))
).resolve()
CLASSES_FILE = Path(os.environ.get("YOLO_CLASSES", str(WORKSPACE_DIR / "classes.txt"))).resolve()
OUTPUT_DIR = Path(os.environ.get("YOLO_OUTPUT", "dataset")).resolve()

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp"}
