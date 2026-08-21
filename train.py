import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Train a YOLO model on an exported dataset")
    parser.add_argument("--data", default="dataset/data.yaml", help="Path to data.yaml (default: dataset/data.yaml)")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model to fine-tune (default: yolov8n.pt)")
    parser.add_argument("--epochs", type=int, default=100) #cuántas veces estudia todo el dataset.
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--patience", type=int, default=30) #cuánto tiempo le permitís seguir estudiando si no está mejorando.
    parser.add_argument("--batch", type=int, default=16) #cuántas imágenes mira de golpe
    # AMP off por defecto: la validación corre en FP16 puro (validator.py:162) y en
    # GPUs Pascal (GTX 10xx) eso desborda a NaN. Activalo con --amp en GPUs Turing+.
    parser.add_argument("--amp", action=argparse.BooleanOptionalAction, default=False)
    # mosaic arma collages de 4 imágenes; con datasets chicos genera basura.
    parser.add_argument("--mosaic", type=float, default=0.0)
    # freeze=10 congela el backbone: adapta al dominio sin reescribir lo aprendido en COCO.
    parser.add_argument("--freeze", type=int, default=10)
    parser.add_argument("--optimizer", default="auto") #'auto' ignora --lr0 y elige el suyo
    parser.add_argument("--lr0", type=float, default=0.01) #solo aplica si --optimizer no es 'auto'
    parser.add_argument("--device", default=None, help="e.g. 'cpu', '0', 'mps' (default: auto-detected by ultralytics)")
    parser.add_argument("--project", default="runs/train", help="Output folder for training runs")
    parser.add_argument("--name", default="exp", help="Name for this training run")
    parser.add_argument("--resume", action="store_true", help="Resume the last interrupted run")
    args = parser.parse_args()

    data_path = Path(args.data)
    if not data_path.exists():
        print(f"No se encontró {data_path}.", file=sys.stderr)
        print("Primero etiquetá imágenes con la app y usá 'Exportar dataset' para generarlo.", file=sys.stderr)
        sys.exit(1)

    project_path = Path(args.project).resolve()

    from ultralytics import YOLO

    model = YOLO(args.model)
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        patience=args.patience,
        amp=args.amp,
        mosaic=args.mosaic,
        freeze=args.freeze,
        optimizer=args.optimizer,
        lr0=args.lr0,
        device=args.device,
        project=str(project_path),
        name=args.name,
        resume=args.resume,
    )

    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\nEntrenamiento terminado. Mejores pesos: {best_weights}")
    print(f"Para usarlos: yolo predict model={best_weights} source=<imagen_o_carpeta>")


if __name__ == "__main__":
    main()
