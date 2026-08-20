from pathlib import Path

from PIL import Image

from backend.config import IMAGE_EXTENSIONS
from backend.models import Box


def list_image_files(images_dir: Path) -> list[Path]:
    if not images_dir.is_dir():
        return []
    files = [p for p in images_dir.iterdir() if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS]
    return sorted(files, key=lambda p: p.name)


def get_image_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as img:
        return img.size


def label_path_for(image_path: Path, labels_dir: Path) -> Path:
    return labels_dir / f"{image_path.stem}.txt"


def read_boxes(label_path: Path) -> list[Box]:
    if not label_path.exists():
        return []
    boxes = []
    for line in label_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        class_id, x, y, w, h = line.split()
        boxes.append(
            Box(
                class_id=int(class_id),
                x_center=float(x),
                y_center=float(y),
                width=float(w),
                height=float(h),
            )
        )
    return boxes


def write_boxes(label_path: Path, boxes: list[Box]) -> None:
    label_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{b.class_id} {b.x_center:.6f} {b.y_center:.6f} {b.width:.6f} {b.height:.6f}"
        for b in boxes
    ]
    label_path.write_text("\n".join(lines) + ("\n" if lines else ""))


def is_labeled(image_path: Path, labels_dir: Path) -> bool:
    return label_path_for(image_path, labels_dir).exists()


def read_classes(classes_file: Path) -> list[str]:
    if not classes_file.exists():
        return []
    return [line.strip() for line in classes_file.read_text().splitlines() if line.strip()]


def safe_image_path(filename: str, images_dir: Path) -> Path:
    if Path(filename).name != filename:
        raise ValueError(f"Invalid filename: {filename}")
    return images_dir / filename
