from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.config import (
    CLASSES_FILE,
    FRONTEND_DIR,
    EXPORT_LABELS_DIR,
    IMAGES_DIR,
    LABELS_DIR,
    OUTPUT_DIR,
)
from backend.export import export_dataset
from backend.models import AnnotationPayload, ExportRequest, ExportResult, ImageInfo
from backend.storage import (
    get_image_size,
    is_labeled,
    label_path_for,
    list_image_files,
    read_boxes,
    read_classes,
    safe_image_path,
    write_boxes,
)

IMAGES_DIR.mkdir(parents=True, exist_ok=True)
LABELS_DIR.mkdir(parents=True, exist_ok=True)

if not CLASSES_FILE.exists() or not read_classes(CLASSES_FILE):
    raise RuntimeError(
        f"No classes found at {CLASSES_FILE}. Create it with one class name per line "
        "before starting the app."
    )

app = FastAPI(title="YOLO Local Annotator")

app.mount("/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR / "static")), name="static")


@app.get("/")
def index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))


@app.get("/api/classes")
def get_classes() -> list[str]:
    return read_classes(CLASSES_FILE)


@app.get("/api/images")
def get_images() -> list[ImageInfo]:
    result = []
    for image_path in list_image_files(IMAGES_DIR):
        width, height = get_image_size(image_path)
        boxes = read_boxes(label_path_for(image_path, LABELS_DIR))
        result.append(
            ImageInfo(
                filename=image_path.name,
                width=width,
                height=height,
                labeled=is_labeled(image_path, LABELS_DIR),
                box_count=len(boxes),
            )
        )
    return result


@app.get("/api/annotations/{filename}")
def get_annotations(filename: str) -> AnnotationPayload:
    try:
        image_path = safe_image_path(filename, IMAGES_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    boxes = read_boxes(label_path_for(image_path, LABELS_DIR))
    return AnnotationPayload(boxes=boxes)


@app.put("/api/annotations/{filename}")
def put_annotations(filename: str, payload: AnnotationPayload) -> AnnotationPayload:
    try:
        image_path = safe_image_path(filename, IMAGES_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image not found")
    label_path = label_path_for(image_path, LABELS_DIR)
    write_boxes(label_path, payload.boxes)
    return AnnotationPayload(boxes=read_boxes(label_path))


def _resolve_export_labels() -> tuple[Path, list[str]]:
    """Elige el directorio de etiquetas del export y detecta si quedó desactualizado.

    Prefiere las fusionadas (manual + pseudo-COCO). Si no existen todavía, cae a las
    manuales para no romper el flujo, pero eso entrena solo con lo etiquetado a mano.
    """
    if not EXPORT_LABELS_DIR.is_dir():
        return LABELS_DIR, []
    stale = []
    for manual in sorted(LABELS_DIR.glob("*.txt")):
        merged = EXPORT_LABELS_DIR / manual.name
        if not merged.exists() or merged.stat().st_mtime < manual.stat().st_mtime:
            stale.append(manual.name)
    return EXPORT_LABELS_DIR, stale


@app.post("/api/export")
def post_export(req: ExportRequest) -> ExportResult:
    classes = read_classes(CLASSES_FILE)
    labels_dir, stale = _resolve_export_labels()
    result = export_dataset(
        images_dir=IMAGES_DIR,
        labels_dir=labels_dir,
        classes=classes,
        output_dir=OUTPUT_DIR,
        train_pct=req.train_pct,
        val_pct=req.val_pct,
        test_pct=req.test_pct,
        seed=req.seed,
    )
    result.labels_source = str(labels_dir)
    result.stale_labels = stale
    return result
