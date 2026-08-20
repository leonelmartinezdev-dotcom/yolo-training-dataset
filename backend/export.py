import random
import shutil
from pathlib import Path

import yaml

from backend.models import ExportResult
from backend.storage import is_labeled, label_path_for, list_image_files


def export_dataset(
    images_dir: Path,
    labels_dir: Path,
    classes: list[str],
    output_dir: Path,
    train_pct: float,
    val_pct: float,
    test_pct: float,
    seed: int,
) -> ExportResult:
    all_images = list_image_files(images_dir)
    labeled_images = [p for p in all_images if is_labeled(p, labels_dir)]
    skipped = len(all_images) - len(labeled_images)

    rng = random.Random(seed)
    shuffled = labeled_images[:]
    rng.shuffle(shuffled)

    n = len(shuffled)
    n_test = int(n * test_pct)
    n_train = int(n * train_pct)
    n_val = n - n_train - n_test

    splits = {
        "train": shuffled[:n_train],
        "val": shuffled[n_train : n_train + n_val],
        "test": shuffled[n_train + n_val :],
    }

    shutil.rmtree(output_dir, ignore_errors=True)
    for split_name, split_images in splits.items():
        if not split_images and split_name == "test" and test_pct == 0:
            continue
        images_out = output_dir / "images" / split_name
        labels_out = output_dir / "labels" / split_name
        images_out.mkdir(parents=True, exist_ok=True)
        labels_out.mkdir(parents=True, exist_ok=True)
        for image_path in split_images:
            shutil.copy2(image_path, images_out / image_path.name)
            label_path = label_path_for(image_path, labels_dir)
            shutil.copy2(label_path, labels_out / label_path.name)

    data_yaml = {
        "path": str(output_dir.resolve()),
        "train": "images/train",
        "val": "images/val",
        "names": {i: name for i, name in enumerate(classes)},
    }
    if test_pct > 0:
        data_yaml["test"] = "images/test"

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "data.yaml").open("w") as f:
        yaml.safe_dump(data_yaml, f, sort_keys=False, allow_unicode=True)

    return ExportResult(
        train_count=len(splits["train"]),
        val_count=len(splits["val"]),
        test_count=len(splits["test"]),
        skipped_unlabeled=skipped,
        classes=classes,
        output_dir=str(output_dir.resolve()),
    )
