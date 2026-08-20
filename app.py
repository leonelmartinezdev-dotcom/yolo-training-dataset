import argparse
import os


def main():
    parser = argparse.ArgumentParser(description="Local YOLO annotation tool")
    parser.add_argument("--images", help="Path to the folder with raw images (default: workspace/images)")
    parser.add_argument("--labels", help="Path to store YOLO label .txt files (default: workspace/labels)")
    parser.add_argument("--classes", help="Path to classes.txt (default: workspace/classes.txt)")
    parser.add_argument("--output", help="Path to write the exported dataset (default: dataset)")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    if args.images:
        os.environ["YOLO_IMAGES"] = args.images
    if args.labels:
        os.environ["YOLO_LABELS"] = args.labels
    if args.classes:
        os.environ["YOLO_CLASSES"] = args.classes
    if args.output:
        os.environ["YOLO_OUTPUT"] = args.output

    import uvicorn

    from backend.main import app

    url = f"http://127.0.0.1:{args.port}"
    print(f"YOLO Local Annotator running at {url}")
    uvicorn.run(app, host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
