from pydantic import BaseModel, model_validator


class Box(BaseModel):
    class_id: int
    x_center: float
    y_center: float
    width: float
    height: float


class AnnotationPayload(BaseModel):
    boxes: list[Box]


class ImageInfo(BaseModel):
    filename: str
    width: int
    height: int
    labeled: bool
    box_count: int


class ExportRequest(BaseModel):
    train_pct: float = 0.8
    val_pct: float = 0.2
    test_pct: float = 0.0
    seed: int = 42

    @model_validator(mode="after")
    def check_percentages(self) -> "ExportRequest":
        total = self.train_pct + self.val_pct + self.test_pct
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"train_pct + val_pct + test_pct must sum to 1.0 (got {total})")
        return self


class ExportResult(BaseModel):
    train_count: int
    val_count: int
    test_count: int
    skipped_unlabeled: int
    classes: list[str]
    output_dir: str
    # De qué directorio salieron las etiquetas: las fusionadas (labels_auto) o las
    # manuales sueltas. Exportar desde las manuales le borra al modelo las clases COCO.
    labels_source: str = ""
    # Etiquetas manuales editadas después de la última corrida de pseudolabel.py:
    # sus cambios NO están en el export.
    stale_labels: list[str] = []
