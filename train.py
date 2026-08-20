import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Train a YOLO model on an exported dataset")
    parser.add_argument("--data", default="dataset/data.yaml", help="Path to data.yaml (default: dataset/data.yaml)")
    parser.add_argument("--model", default="yolov8n.pt", help="Base model to fine-tune (default: yolov8n.pt)")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
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

    from ultralytics import YOLO

    model = YOLO(args.model)
    results = model.train(
        data=str(data_path),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        project=args.project,
        name=args.name,
        resume=args.resume,
    )

    best_weights = Path(results.save_dir) / "weights" / "best.pt"
    print(f"\nEntrenamiento terminado. Mejores pesos: {best_weights}")
    print(f"Para usarlos: yolo predict model={best_weights} source=<imagen_o_carpeta>")


if __name__ == "__main__":
    main()
